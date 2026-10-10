# JetRover ROS2 Jazzy 전체 프로젝트 체크리스트

상태: `[x]` 완료 · `[~]` 부분 완료/추가 검증 필요 · `[ ]` 미완료
작업을 끝낼 때마다 이 파일의 상태를 갱신하고 `README.md`의 진행률 표도 고친다.
0번 섹션은 사용자가 알려준 환경 정보 기준이며, 1~3번은 실제 로봇에서 확인한 내용이다.

## 0. Jetson 개발환경
- [x] Jetson Orin Nano 8GB OS 설치
- [x] Ubuntu 개발환경 기본 설정
- [x] CUDA / nvcc 동작 확인
- [x] SSH 원격접속
- [x] VS Code Remote-SSH 사용
- [x] 자동 로그인
- [x] 화면 잠금/절전 해제
- [x] ROS2 Jazzy 설치
- [x] colcon, rosdep 개발환경
- [x] ~/jetrover_ws workspace 구성
- [ ] Docker 기반 재현 가능한 개발환경
- [ ] 전체 패키지 버전/환경 문서화
- 현재 단계에서는 Docker보다 로봇 기능 구현이 우선이다.

## 1. STM32 / Base Driver
### RRC / Serial
- [x] CH9102 USB-UART 확인 (`1a86:55d4`, `/dev/ttyACM0`)
- [x] STM32 UART2 확인
- [x] 1,000,000 baud 확인
- [x] 안정적인 `/dev/serial/by-id/usb-1a86_USB_Single_Serial_596F003889-if00` 경로 확인
- [x] RRC frame 분석 (`AA 55 FUNC LEN DATA CRC`)
- [x] CRC8-MAXIM 구현, 실제 프레임 607개 CRC 검증
- [x] Streaming parser 구현
- [x] termios serial driver
- [x] Serial 자동 reconnect
- [x] 공식 프로토콜 PDF 확보 (`firmware_source/`)

### Motor
- [x] Motor ID 0~3 확인 (펌웨어는 0부터, 공식 PDF 예제는 1부터라 문서와 다름)
- [x] 4개 바퀴 실제 mapping 확인 (모터 ID 0 왼앞, 1 왼뒤, 2 오른앞, 3 오른뒤 = 보드 포트 1~4; 오른쪽은 전진이 음수)
- [x] Mecanum inverse kinematics
- [x] /cmd_vel → motor packet
- [x] 최대 선속도 제한 (0.2 m/s), 최대 각속도 제한 (1.0 rad/s)
- [x] 실제 모터 구동 확인
- [x] 명령 timeout 0.5초 (host 측 watchdog)
- [x] 정상 종료 시 stop packet
- [x] crash signal(SEGV/ABRT/BUS/FPE/ILL/HUP/QUIT)에서 stop packet (SIGKILL은 불가)

### 남은 안전 문제
- [~] STM32 hang 진단 (**9회 발생**, 원인 미확정. 저전압 단독 가설은 폐기(9.47 V~완충 12 V 전 범위에서 발생). idle 지속이 가장 일관된 조건으로 추정. **2026-09-23: RST 버튼으로 hang 상태에서도 즉시 복구 가능함을 확인** — 이전 "전원 재시작만 복구" 기록은 정정됨. DTR/RTS 소프트웨어 자동 리셋은 4×4 조합까지 다 시험했지만 없음: `troubleshooting/001-stm32-firmware-hang.md`)
- [x] STM32 heartbeat monitor (1초 이상 packet 미수신 감지)
- [x] `/battery_state` 발행 (STM32 배터리 패킷 → `sensor_msgs/BatteryState`, 10 V 미만이면 경고) — hang 시점 전압을 남기기 위함
- [x] hang 진단 도구/기록 (`tools/stm32_diagnostics/`)
- [x] 펌웨어 `.hex` 정적 분석 (IWDG 약 20 ms, `app_task`가 먹이 → 다른 태스크만 막히면 못 잡을 수 있음)
- [x] UART1(ISP/flashing) 포트 특정 — 보드 라벨 "USB serial port 1/flashing download"로 확인, `/dev/ttyACM1`. **실제 ROM 부트로더 응답 검증 완료(2026-09-27)**: 0x7F→ACK, GET(부트로더 v0x31, Read/Write/Erase 등 지원), GET ID(`0x0413`=STM32F40x/41x, 예상과 일치)
- [x] RDP 상태 확인 + 전체 flash 백업 — RDP 없음(512KB 전부 읽기 성공), `firmware_source/RosRobotControllerM4_dumped_backup.bin`에 저장. **`firmware_source/RosRobotControllerM4.hex`와 79,857바이트(약 15%) 다름**(리셋벡터 SP부터 다른 빌드) — 사용자 요청으로 이 vendor hex로 재플래시(mass erase+write+검증 성공, 512KB 바이트 일치). RST로 재부팅 확인, 부저/OLED/IMU/배터리/바퀴 모터/로봇팔 서보 6개(관절1~5+그리퍼10) 전부 정상 동작 확인(2026-09-27)
- [ ] STM32 hang 근본 원인 규명 — 원인 규명 대신 **자체 펌웨어 재작성으로 방향 전환** (아래 참고)
- [ ] MCU 자체 motor command timeout (현재 없음, 13초 확인)
- [ ] task-health 기반 watchdog
- [ ] UART DMA recovery
- [ ] encoder feedback packet (공식 프로토콜에 없음 → 펌웨어 개발 필요. 보드 사양상 모터는 물리적으로 "4채널 인코더 모터"라 엔코더 자체는 있고 펌웨어가 내부 폐루프 속도제어에 쓰고 있을 가능성이 높지만(추정), host로는 여전히 안 옴 — 재플래시 후에도 동일 확인)
- 가장 중요한 미해결 문제는 STM32 firmware hang이다. host 측은 감지·정지 시도까지만 가능하고,
  STM32 자체가 먹통이면 정지 명령을 처리하지 못하므로 완전한 fail-safe가 아니다. RST 버튼 복구는 사람이 있어야 한다.

### 자체 STM32 펌웨어 재작성 (2026-09-27 착수, 소스가 없어 원인 규명이 막혀서 방향 전환)
계획 전체: `~/.claude/plans/enchanted-chasing-sky.md`. 목표는 모터/IMU/배터리(현재 `jetrover_base`와 와이어 호환) +
보드 PDF에 문서화된 전 기능(LED/부저/PWM서보/버스서보/버튼/SBUS/게임패드)까지 새로 구현.
- [x] **SWD 디버거 확보** (2026-10-08 도착). 실제로는 ST-Link가 아니라 **J-Link OB 클론**(USB `1366:0101`, 펌웨어 "J-Link ARM-OB STM32" 2012) — openocd `interface/jlink.cfg`로 사용, SEGGER 툴 펌웨어 업데이트 금지(클론 벽돌 위험)
- [x] **SWD 연결 + 플래시 백업 (2026-10-10, 읽기 전용, halt 없음/모터 스위치 OFF)**: VTarget 3.3 V, DPIDR 0x2ba01477, device id 0x101f6413(STM32F40x), flash 512 KiB, RDP 0(읽기 가능).
  `swd_backup.sh`로 512 KB 2회 읽기 해시 일치(`450d63d0…936e`, 64 KiB/s), **앞 82,144바이트 = 09-27 재플래시 vendor 빌드와 동일, 나머지 전부 0xFF** → 현재 칩 펌웨어 확정.
  백업: `~/firmware_source/swd_backup_20261010_130702/` (host에도 복사 완료). 백업 후 base.launch 정상(IMU 111 Hz, 배터리 12.55 V, 관절 읽기, 오류 없음)
- [~] 툴체인 설치 — `arm-none-eabi-gcc`(13.2.1)/`objdump`, `STM32_Programmer_CLI`(2.23.0)는 사용자가 `~/.local/opt/stm32/`에 설치 완료(`setup/ENVIRONMENT_SETUP.md` 8번). `openocd`/`stlink-tools`는 ST-Link 도착 후 설치 예정
- [x] UART1 ROM 부트로더 응답 검증 (읽기 전용: 0x7F→ACK, GET, GET_ID) — 완료, 위 1번 섹션 참고
- [x] RDP 상태 확인 + 전체 flash 백업 — 완료, 위 1번 섹션 참고 (덤으로 vendor hex 재플래시까지 실행됨)
- [~] 정적 리버스엔지니어링으로 GPIO/페리페럴 핀 1차 가설 (`analyze_firmware.py` 확장, 2026-09-27) — MOVW/MOVT로 만들어지는 페리페럴 base 주소만 잡는 방식이라 **정확한 핀은 아직 모름**(1차 활동량 신호만). TIM3/4/5/7/8/9/10/11/12/13/14 다수 사용(PWM/타이밍 후보), USART1/2/3/6+UART5 참조, SPI2 1회(디스플레이 후보), ADC1 1회(배터리 후보), GPIOB/D/H만 잡힘(A/C/E/F/G/I는 이 방식으로 안 잡힘 — LDR 리터럴풀 방식일 가능성, 탐지 방법 한계). **재플래시한 빌드는 IWDG 초기화/refresh 패턴 자체가 안 잡힘**(이전 빌드와 태스크 스택 크기도 다름 — 15% 바이트 차이와 일치, 정말 다른 빌드였다는 재확인). 정확한 핀은 ST-Link 도착 후 SWD로 확정 예정
- [x] 프로토콜 코덱(CRC8-MAXIM + FUNC 0~9) 순수 C, 호스트 유닛테스트 — `firmware/rrc_m4/lib/protocol/` (완료: FUNC0~9 pack/unpack, 골든벡터=PDF 예제+오늘 실제로 로봇에 보낸 프레임, 호스트 테스트 전부 통과, Cortex-M4 타겟 프리스탠딩 컴파일도 확인. 버스서보 부가 서브커맨드·PWM서보 deviation upload 서브커맨드 값은 미확정으로 남겨둠)
- [x] `firmware/rrc_m4/` 프로젝트 뼈대 (CMake) — 코덱 라이브러리만 있음, ARM 링크/CMSIS/HAL vendor는 아직
- [ ] (ST-Link 도착 후) SWD로 정품 펌웨어 관찰하며 핀맵 확정
- [~] 신규 펌웨어 단계별 브링업 (LED→UART→프로토콜/IWDG 재설계→IMU→배터리→**모터**→부저/LED→버튼→SBUS→PWM서보→버스서보→OLED/블루투스/게임패드 USB Host)
  - [x] 2026-10-10 첫 flash(RRC, MOTOR_ENABLE=OFF, J-Link+openocd): 두 문제 수정 후 동작 — 크리스털 16 MHz(8 MHz 가정으로 336 MHz 오버클럭 lockup), LCD 태스크 스택 넘침(0.8초 IWDG 리셋). troubleshooting/035
  - [x] UART(USART3 1 Mbaud) 텔레메트리 CRC 오류 0, IWDG 감독 정상(uptime 연속), STATUS 10 Hz / WHEEL 50 Hz
  - [x] IMU(QMI8658 자동판별) 50 Hz, |a| 0.96 g, 자이로 bias가 vendor 시절 `base.yaml` 값과 일치
  - [x] 배터리 2 Hz 12.528 V(vendor 12.55 V와 일치)
  - [x] LED: PE10, 호스트 LED 명령(FUNC1)으로 깜빡임 확인(평소 꺼짐은 설계대로)
  - [x] 상태 화면: 실제는 **SSD1306 128×32 OLED(I2C 0x3C, IMU 버스 공유)** — SPI2 LCD 가정 폐기, 드라이버 교체 후 4줄 표시 확인, IMU 49.6 Hz 유지(troubleshooting/035)
  - [x] 버튼 2개(PE0/PE1, 2026-10-11): PRESSED / CLICK / LONGPRESS / DOUBLE_CLICK 모두 두 버튼에서 수신(SWD로도 누르면 핀이 0). **번호 실측**: 보드의 K1을 누르니 id 2가 와서 K1 = PE1 = id 1로 맞바꿈(flash 후 재확인 남음)
  - [x] 부저(FUNC2, 2026-10-11): 0.2초 × 3회 소리 확인(사용자)
  - [x] 버스 서보 쓰기(2026-10-11, 자체 펌웨어 직접 명령, base_node 없이): 관절 1(ID 1) +20 눈금(4.8°) 1초 → 읽은 위치 498 → 515(+17), 복귀 명령 후 499(+1 눈금 = 0.24°). 사용자 육안: 오른쪽으로 움직임(너무 작아 부드러움은 판단 불가). 방향 핀(PE7/PE8) 추정 조합이 쓰기에서도 맞음. 읽기: ID 1~5·10 모두 응답
  - [-] PWM 서보 4채널: **해당 없음** — 사용자 확인(2026-10-11): 로봇에 바퀴 모터와 팔 버스 서보 외 서보 없음(9/27 vendor 시험에서 움직임이 안 보인 이유). 펌웨어 경로(FUNC4)는 L0 시험만
  - [-] SBUS: **해당 없음/보류** — 수신기 없음(10초 청취에 프레임 0). 수신기 연결 시 `rrc_m4_io_test.py sbus`로 확인
  - [x] USB 게임패드(2026-10-11): 중립에서 버튼이 눌린 것으로 읽던 버그 수정(HID 리포트 ID 때문에 한 칸씩 밀림, 레이아웃 실측 확정) → 전 버튼·방향키·스틱 FUNC8 정상(troubleshooting/039)
  - [x] 모터 fault 핀(PD3) 극성 확정(2026-10-10): 모터 스위치 OFF → fault [1,1,1,1](드라이버 무전원), ON → [0,0,0,0]. **High = fault 확정**. uptime 331 s 동안 리셋 없음
  - [x] base_node(호스트, 수정 없이)와 연동(2026-10-10): `/imu/data_raw` 50 Hz(vendor 111 Hz), 자이로 bias 보정 후 ≈0.01 rad/s, |a| 9.43 m/s²; `/battery_state` 12.528 V; `/joint_states` 5 Hz 6관절(버스 서보 FUNC5 읽기 동작 → PE7/PE8 방향 핀 조합 OK); `/odom` 30 Hz(EKF). 오류/silent 로그 없음. 팔·모터 명령은 미시험
  - [~] 태스크 스택 여유: 진단 프레임 0x24(DIAG 0x06 요청 시) + `rrc_m4_diag.py` 구현(2026-10-10), 실기 기록 남음
  - [x] 배터리 값 갱신(2026-10-10): 부팅 첫 값으로 고정되던 ADC DMA 재시작 거부 수정, 실제 11.05 V 확인(troubleshooting/038)
  - [x] 냉간 부팅(전원 완전 차단 후) IMU 동작(2026-10-10): 처음엔 QMI8658 값이 멈춤 → 소프트 리셋 + 멈춘 값 감지 추가 후 정상(troubleshooting/037)
  - [x] 모터 PWM 핀 짝·방향·엔코더 부호(2026-10-10, 바퀴 띄움, RAW_PWM ±400): 4바퀴 확정 — 왼쪽 +PWM 전진, 오른쪽 +PWM 후진(vendor 규약), 엔코더 전부 +1. M2 PWM 짝이 추정과 반대였음. 중간에 M2 폭주 → 부호 가드·e-stop 유지 추가(troubleshooting/036)
  - [x] PID 속도 제어(FUNC3): 목표 0.5/1.0(구 단위) → 후반 평균 0.506/1.002, std 0.07~0.08(진동 있음, 튜닝 여지). **한 바퀴 = 3,996 카운트 실측**(30초 10바퀴+10°, 이전 1320 추정은 약 3배 틀림) → 펌웨어 반영, `MOTOR_RPS_LIMIT` 3.0. **새 값으로 4바퀴 확인(2026-10-10)**: 실제 0.5 rps 6초씩 → 후반 평균 0.496~0.509, std 0.019~0.024(진동이 이전 0.07에서 크게 줄어 게인이 실제 rev/s 단위였음을 뒷받침), 정지 포함 3.13~3.19바퀴 = 사용자 육안 "3바퀴 조금 더" 일치
  - [x] base_node(수정 없음) `/cmd_vel` 바퀴 띄움 시험(2026-10-10): 전진 vx 0.05, 왼쪽 옆이동 vy 0.05, 반시계 wz 0.3 각 2초 → 4바퀴 방향 모두 메카넘 기대대로(사용자 육안), 오류 로그 없음, 배터리 12.50 V
  - [x] 바닥 저속 주행(2026-10-10, base_node 경유, 0.05 m/s·3초): 전진 15 cm(바퀴 기준 14.4~15.1 cm, 사용자 실측 15~16), 왼쪽 옆이동 15 cm(사용자 실측), 반시계 0.3 rad/s·3초 → **자이로 51.5°(명령 51.6°), 육안 약 55°** — vendor 펌웨어에서 회전이 명령의 81%였던 것이 약 100%로(폐루프 속도 제어 효과로 추정). 직접 명령 시 바퀴 속도는 0.3~0.5초에 목표 도달. 첫 2초 시험의 "1 cm"는 재시험에서 재현 안 됨(가속 구간 + 표시 없는 눈대중으로 추정)
  - [~] 엔코더 피드백(FUNC 0x21) → base_node `wheel_twist`(2026-10-10, **RRC 경로로 결정**): `decode_wheel_feedback`, `wheel_twist_source: command|encoder|auto`(기본 command, launch 인자, encoder는 끊기면 0+경고, auto는 명령으로 폴백), 단위시험(디코드 1 + 선택 4), colcon test 119개 통과. 실기 바닥 전진 3초 2회: 엔코더 odom 14.3 / 14.7 cm, 실측 약 15 / 15.0 cm(−2 %). **E4 완료(2026-10-10, 각 5회)**: 직진 1 m 엔코더 +0.24 ± 0.41 cm(명령값 −0.68 ± 0.50), 옆이동 1 m −0.48 ± 0.16(명령값 −1.08 ± 0.13), 회전 360° 자이로 +0.5 ± 0.4°·엔코더 −7.4°·명령값 −6.1° → 이동은 엔코더, yaw는 자이로 유지(`docs/benchmarks/navigation/encoder_odom_e4_20261010.md`). **회전 보정(2026-10-10)**: wheelbase/track 0.216/0.195 → 0.2120/0.1914 → 360°×5 실측 359.6°, 명령값 +0.38°, 엔코더 −0.12°, 자이로 +0.28°(보정 전 −6.1/−7.4/+0.5). **공분산(E5)**: 엔코더 twist 분산 vx 1e-4·vy 2e-4(`wheel_twist_covariance_encoder`, 바닥 vx 순간 표준편차 0.004 m/s 근거), 명령값 모드는 0.05 유지. **E5 왕복(사각형 4 m, 3회)**: 실제 어긋남 3~5 cm·최대 4°(롤러 미끄러짐), 엔코더 단독 3.4~5.0 cm 오차, **EKF 0.1~0.4 cm**(자이로 bias 재측정 [0.2075, 0.1660, −0.0162] 후). **E6 진행 중(14/30, `docs/benchmarks/navigation/e6_interim_20261010.md`)**: A 5회씩 두 조건 차이 없음(13.6 대 15.2 cm, goal tolerance 경계), B 2회씩 둘 다 오른쪽 16~27 cm — AMCL이 3~7 cm 왼쪽으로 치우치고 출발 AMCL 강제값이 실제 출발과 5 cm 달라 odom 차이가 묻힘. C·B3~5 남음(출발 초기화 방식 결정 후)
  - [~] (micro-ROS 실기 브링업 전 선행 조건, 2026-10-10 외부 검토로 확인) ~~① `CMD_VEL_MAX_*` 0.2·1.0으로 통일~~ ~~② NaN/Inf 거부(코어 `robot_set_*`·`enc_motor_set_speed`)~~ ~~③ 단일 활성 제어원(`robot_ctrl` owner)~~ — ①~③ 코드·호스트 시험 완료(2026-10-10, 실기 미확인) ④ `jetrover_microros`에 팔(서보·`/joint_states`) 기능 없음 ⑤ RAM 사용률·스택 여유 실측, agent 재연결 반복 시험


#### RRC 완성 + micro-ROS 적용 (2026-10-05 착수, PRD `prd/rrc-microros-firmware.md`, 시험 계획 `prd/rrc-microros-firmware-test-plan.md`)
Hiwonder 공식 문서 저장소 + 사용자가 준 디컴파일 팩을 근거로 코드/빌드까지 진행. **flash와 모터 시험은 하지 않았다(별도 승인).** 아래 `[~]`는 L0(빌드·호스트 시험)까지.
- [x] 핀맵 확정/추정 구분 — `firmware_source/PINMAP.md` (모터 PWM 8핀=TIM1/9/10/11, 호스트=USART3 PD8/9, IMU 소프트 I2C PB10/11, 배터리 ADC PB0+Vrefint 등. 재구성 패키지의 "TIM8" 오기 정정, 부저 PA4/PA8 문서 충돌은 바이너리 기준 PA8 채택). 추출 도구 `tools/firmware_re/extract_gpio.py`
- [~] core 라이브러리 `lib/core` (PID, 엔코더 모터+runaway 래치, 메카넘, robot_ctrl 안전, IMU 자동판별, 버스·PWM 서보, SBUS, 게임패드, 버튼, 부저·LED, 배터리, local_drive) — 호스트 단위 시험 통과
- [~] 프로토콜 미구현분 — 모터 서브커맨드 0x00/0x02/0x03, PWM 서보 deviation 0x07, 버스 서보 부가 서브커맨드 전부(0x07/09/0B/0C/10/12/20/22/24/30/32/34/36/38/3A), 확장 FUNC 0x20~0x23(상태/엔코더 피드백/진단/원시 HID)
- [~] RRC 어댑터 `lib/comm` — PDF 예제 프레임 골든 시험, 쓰레기/플러드/바이트 단위 입력 복구 시험
- [~] ARM 펌웨어 `app/` (HAL + FreeRTOS 정적 태스크, USB 호스트 게임패드, LCD 상태 화면, 블루투스, 버스 서보 자동 극성 탐색, 감시 태스크 IWDG) — **RRC 모드 빌드 성공**(flash 56 KB, RAM 50 KB, 경고 0), flash 안 함
- [~] 벤더에 없던 안전기능: MCU 자체 명령 timeout, e-stop 래치, 저전압 차단, task-health watchdog (위 "MCU 자체 motor command timeout / task-health watchdog" 항목의 구현본, 실기 검증 전)
- [~] 엔코더 피드백(FUNC 0x21 / `/rrc/wheel_rps`) — 위 3번 "wheel RPS feedback 추가" 항목의 펌웨어측 구현. 호스트가 이걸 읽는 쪽은 `jetrover_microros`의 `rrc_bridge`(micro-ROS 경로)만 있음, `jetrover_base`는 아직 FUNC 0x21을 안 읽음
- [~] micro-ROS: `micro_ros/build_microros_lib.sh`(Jetson 네이티브 빌드, docker 불가), 펌웨어 노드 `app/src/comm_microros.c`, 호스트 패키지 `src/jetrover_microros`(브리지+launch). 상태는 `firmware/rrc_m4/micro_ros/README.md`
- [ ] 브링업(별도 승인): L2 IMU/배터리/통신만(MOTOR_ENABLE=0) → 바퀴 띄운 모터 극성/엔코더 부호 확인 → PID 튜닝 → 바닥 주행. 확인할 "추정" 목록은 `firmware/rrc_m4/README.md`

## 2. IMU
- [x] 0x07 packet decoding
- [x] sensor_msgs/msg/Imu, `/imu/data_raw` (약 111 Hz)
- [x] g → m/s², deg/s → rad/s
- [x] 실제 센서 축 확인 (센서 X 오른쪽, Y 뒤, Z 아래)
- [x] STM32 sensor frame → base_link 방향 변환 (x=−y, y=−x, z=−z)
- [x] gyro bias 측정, gyro bias YAML 적용, bias 자동 측정 tool (`tools/imu_calibration/`)
- [x] 3자세 축 검증, 360° 회전 검증
- [~] gyro scale 약 97%
- [~] accel magnitude 약 3% 오차 (축별 배율 차이)
- [ ] temperature별 bias 변화 분석
- [ ] 장시간 Allan variance 분석
- 마지막 두 개는 연구 목적이 아니면 우선순위가 낮다.

## 3. Odometry / State Estimation
- [x] /wheel_twist (TwistWithCovarianceStamped)
- [x] /odom_raw (command 기반 open-loop, 디버깅용)
- [x] Mecanum vx, vy, wz 처리
- [x] robot_localization 설치
- [x] EKF 설정 (`config/ekf.yaml`)
- [x] vx, vy + IMU wz 융합, open-loop 위치는 EKF에 넣지 않음 (twist 전용 입력)
- [x] /odom, odom → base_link TF
- [x] 가상 시리얼 전체 경로 검증 (`tools/stm32_diagnostics/ekf_pipeline_test.py`)
- [x] 정지 상태 실제 로봇 검증 (yaw 드리프트 약 0.8°/분)
- [~] 실제 이동 /odom 검증(왕복 3세트 후 원위치 오차 약 1 cm 이내): 바닥에서 전진/후진/좌/우/회전 완료(0.05~0.1 m/s, STM32 정상). 전진·옆 이동은 명령과 일치(0.99). 1 m 이상 직진과 속도별 반복은 남음

STM32가 encoder feedback을 보내지 않으므로 실제 이동거리가 아니라 명령 속도를 적분한 open-loop odom이다.
- [~] 실제 직진 거리 측정: 0.1 m/s × 3초 명령 30.4 cm → 실측 약 30 cm (1회). 1 m 이상은 아직
- [~] 전진 scale (`odom_linear_scale`): 0.99 → 1.0 유지 (측정 1회, 반복 필요)
- [x] 횡이동 scale: 재측정(줄자)에서 명령 30.4 cm → 실측 30 cm = 0.99 → 1.0 유지. 처음의 "44 cm"는 눈대중 오차였음(troubleshooting/010). 코드에 `odom_lateral_scale` 파라미터는 남겨 두었고 기본 1.0
- [~] angular scale (`odom_angular_scale`): 명령 적분 60° → 자이로 +48.9° (81%, 눈대중 약 45°). EKF는 자이로 yaw를 쓰므로 `odom_raw`에만 영향
- [~] 여러 속도 구간에서 오차 측정: EKF(명령 적분)는 0.05/0.1/0.2 m/s에서 일관(0.301/0.602/0.608 m). 실측(줄자)은 0.2 m/s 등 아직
- [ ] 바닥 종류별 slip 측정
- [ ] (가능하면) STM32 firmware에서 wheel RPS feedback 추가 → encoder 기반 wheel odometry 전환
  - **2026-10-06 구체화(계획)**: PRD `prd/encoder-odometry.md`, 시험 `prd/encoder-odometry-test-plan.md`(E0~E6). 선행: Nav2 baseline(`prd/nav2-baseline-test-plan.md`). 현재 순서/게이트는 `docs/ROADMAP.md`.
  - [x] E0 `mecanum_forward` C++(`jetrover_base`)↔Python(`jetrover_microros/rrc_bridge.py`) 교차검증 (L0): 골든 벡터 5건을 양쪽 단위시험이 공유(2026-10-06). 두 구현의 수식 일치도 대수적으로 확인
  - [ ] E1 엔코더 부호·ticks/rev 실측 (L2, ST-Link·flash 승인 필요)
  - [ ] E2/E3 바퀴 띄운 속도 응답, MCU 자체 정지 시험 (L3)
  - [ ] E4/E5 바닥 직선·회전에서 open-loop vs encoder odom 비교, EKF 공분산 근거 설정 (L4)
  - [ ] E6 Nav2 baseline 15회 재시험(`encoder_ekf` 태그) + Before/After 표

## 4. Robot Description / TF
목표 TF: map → odom → base_footprint → base_link → {imu_link, lidar_link, camera_link(color/depth optical), arm_base_link → arm}
- [x] **JetRover URDF 실제 메쉬로 교체 (2026-10-03)**: `~/AI_secretary_robot`(사용자의 다른 로컬 프로젝트)에
  Hiwonder 공식 `jetrover_arm_moveit` 패키지 전체(xacro+메쉬)가 있는 걸 발견, `src/jetrover_description/`로
  가져옴(`$(find jetrover_arm_moveit)`→`$(find jetrover_description)`로 치환). 손으로 쓴 박스/실린더
  placeholder(`jetrover_placeholder.urdf`로 보관)는 더 안 쓰고, `description.launch.py`가 이제
  `jetrover.xacro`를 직접 처리한다(`xacro` 설치돼 있음 확인, 패키지 의존성 추가). 상세: `src/jetrover_description/README.md`
- [x] base_footprint (EKF 프레임 = `odom → base_footprint`), [x] base_link (이제 실제 차체 메쉬)
- [x] IMU frame 개념 확정
- [x] imu_link (실제 메쉬 적용. **벤더 xacro의 `imu_joint` rpy(원시 센서축 회전)는 `0 0 0`으로 되돌림** —
  `base_node`가 이미 소프트웨어로 변환하므로 벤더 회전을 그대로 쓰면 이중 변환이 됨. translation은 벤더값=기존값과 일치 확인)
- [x] lidar_link (실제 메쉬, 벤더 xacro 값이 기존 값과 거의 동일(소수점 정밀도만 다름) — 교차 검증됨). 장착 위치 실측은 아직
- [x] **camera_link, depth_cam_link/frame — TF 트리에 들어감** (`link4`에 연결, optical 변환까지 벤더 xacro에 있음). **실제 카메라 드라이버의 frame_id와 일치 확인 완료(2026-10-04)**: `base_link→link4→camera_connect_link→depth_cam_link→depth_cam_color_optical_frame` 전부 실측 lookup_transform 성공
- [x] **arm_base_link → 5축 팔(link1~5)+그리퍼(gripper_link+손가락) 전체가 TF 트리에 들어감** (`check_urdf`로 트리 확인 완료, `joint1`~`joint5` + fixed 조인트들). 실제 서보(bus servo ID 1~5+그리퍼10)와 연결하는 컨트롤러/조인트 상태 publish는 아직 없음(14번 섹션)
- [x] robot_state_publisher (`jetrover_description/launch/description.launch.py`, `base.launch.py`에 포함) — xacro 처리로 전환 후 재검증 완료(`/robot_description` 정상 발행, 에러 없음)
- [~] RViz RobotModel 검증 — host Ubuntu 24.04 + RViz2(ROS_DOMAIN_ID=25)로 띄움, 실제 메쉬 반영 확인은 사용자 몫
- [x] TF tree 검증: `check_urdf`로 전체 트리(29개 링크) 확인 완료. `odom→lidar_link`, `odom→imu_link`, `base_link→link1~5`(실제 서보 각도), `base_link→depth_cam_*`(2026-10-04) 전부 실측 확인됨
- [ ] 실측 footprint(바퀴/차체 치수를 줄자로 재검증 — 지금은 전부 Hiwonder 공식값)

## 5. LiDAR (RPLIDAR A1, 사용자 확인)
- [x] USB/serial 인식 — `drivers/ch341/`의 모듈을 설치해서 `/dev/ttyUSB*` 생성, **재부팅 후에도 자동 로드 확인**. `ttyUSB0/1` 번호는 재부팅마다 바뀌므로 by-path(`...usb-0:2.1.4:1.0-port0`)로 지정 (GET_INFO로 A1M8 fw 1.29 확인, 헬스 Good)
- [x] Jazzy driver: `ros-jazzy-rplidar-ros` 설치됨 (A1은 115200 baud 예상, 실제 시험은 포트가 생긴 뒤)
- [x] /scan (`jetrover_bringup/launch/lidar.launch.py`), frame_id `lidar_frame` (URDF에서 `lidar_link` 기준 yaw 180°)
- [x] scan frequency 약 14 Hz = **실제 회전 속도**(time_increment×720 = 74.7 ms와 일치; 이 어댑터가 A1 모터를 최대 속도로 돌리는 것으로 추정, 드라이버에 속도 파라미터 없음). 각도 해상도 약 0.64°, 720 bin(0.5°), 범위 0.15~12 m
- [x] 유효 포인트 50%의 원인: **스캔 −72°~+90°(로봇 기준 뒤쪽 약 160°)가 로봇팔 기둥/몸체에 가려짐**. 나머지 구간은 빈틈 거의 없음 → SLAM은 앞쪽 약 200°만 본다. 범위 정확도 검증은 아직
- [~] RViz(사용자 환경은 VS Code SSH라 화면 없음 → `tools/viz/snapshot.py`로 PNG 저장해서 확인, 실시간은 Foxglove 권장): `jetrover_bringup/rviz/jetrover.rviz`(Grid, RobotModel, TF, LaserScan, Odometry; 고정 프레임 odom)와 `rviz.launch.py`. 로봇 화면(:0)에서 12초 시작해 설정 오류 없음 확인, 실제 화면 확인은 사용자 몫
- [x] base_link → lidar_link → lidar_frame TF (URDF, 실제 스캔으로 방향 검증: 정면 물체 +9°(배치 오차 추정), 왼쪽 물체 +90°/+89° → 좌우 반전 없음, 재부팅 후 재확인)
- [ ] 로봇 회전하면서 scan 정합 확인
- [~] 장시간 USB 안정성 시험 — **2026-09-28: 약 30분 운영 중 USB 재연결 1회 발생**(`ttyUSB0`→`ttyUSB2`), `rplidar_composition`이 자동 복구 안 되고 `/scan` 완전히 끊김(재시작으로 회복). 원인 미확정, `troubleshooting/015` 참고. 재발하는지 계속 관찰 필요
- 완료 기준: RViz에서 RobotModel + /scan + /odom + TF 모두 정상

## 6. SLAM (SLAM Toolbox: 2D scan matching + pose graph + loop closure)
- [x] slam_toolbox 설치 (사용자 sudo로 설치 완료). 설정/launch: `jetrover_navigation`
- [x] async mode 결정 (online async, `config/slam_toolbox_online_async.yaml`: base_footprint, 12 m, 작은 움직임에도 갱신)
- [x] /scan, /odom 연결: 정지 상태에서 `slam_toolbox` active, `/map` 발행(0.05 m), `map→base_footprint` TF 정상, 경고 없음
- [x] map 생성: **키보드 조종 한 바퀴 완주, hang 없이 사각형 방 지도 완성** (`tools/viz/out/lap1_final.png`), 로봇이 출발 지점으로 복귀
- [ ] loop closure
- [x] map 저장: `slam_toolbox serialize_map`으로 `~/jetrover_ws/maps/lap1_20260922.{posegraph,data}` 저장 성공. **`nav2_map_server` 설치 완료(2026-09-22 22:31) 후 표준 `.pgm/.yaml`도 저장 성공**(`/slam_toolbox/save_map` result=0, `setup/ENVIRONMENT_SETUP.md` 참고) — 이전 기록의 "실패"는 stale이었음(2026-09-28 정정). map 재로드(`deserialize_map`으로 계속 매핑 또는 AMCL용 로드)는 아직
- [ ] 긴 복도 테스트, 반복 주행 map distortion 확인
- [ ] 성능 기록: loop closure error, 벽 직선성, 재방문 위치 오차, CPU/RAM

## 7. Localization (map_server + AMCL, Mecanum이므로 OmniMotionModel 검토)
- [x] Map Server — `src/jetrover_navigation/launch/localization.launch.py`. **2026-09-28: 단독 실행으로 확인**: `maps/lap1_20260922.yaml` 로드(67×67 @ 0.05m/cell, yaml과 일치), configure→activate lifecycle 전환 성공
- [x] AMCL — `config/amcl.yaml`(`robot_model_type: nav2_amcl::OmniMotionModel`), 빌드 성공. **2026-09-28 실제 로봇(base+LiDAR)으로 소프트웨어 연동 검증 완료**: `ros2 launch jetrover_navigation localization.launch.py`로 map_server+amcl+lifecycle_manager 전부 정상 activate, `/scan` 구독·`/amcl_pose` 발행·`map→odom` TF 전부 확인
- [x] Omni motion model — 실제 activate까지 확인(정지 상태 기준, 회전/횡이동 중 particle filter 반응은 로봇을 움직여야 확인 가능 — 아직)
- [~] Initial Pose — `amcl.yaml`의 (0,0,0) 기본값으로 정상 설정됨(`Setting pose: 0.000 0.000 0.000` 로그 확인). 이게 실제 로봇 시작 위치와 맞는지는 물리적으로 검증 안 함
- [x] /amcl_pose — 발행 확인(x=0,y=0, covariance 0, 정지 상태라 당연한 값). **주의**: 이 토픽은 `TRANSIENT_LOCAL` durability라 기본 QoS로 구독하면 조용히 아무것도 안 받는다(`troubleshooting/015` 참고)
- [x] map → odom — TF 확인(거의 identity, 로봇이 초기 pose에서 안 움직인 상태라 당연)

### AMCL 물리 검증 (PRD: `prd/slam-nav2.md`, 2026-10-04 Task 분해)
- [x] 7.1(2026-10-05): RViz "2D Pose Estimate"로 초기 pose 수동 지정, 여러 번 반복 확인함(새 지도 `lap2_20261005` 기준)
- [x] 7.2(2026-10-05, Trial 1): `NavigateToPose`로 1m 이동 후 줄자 실측과 비교 — 이동거리 amcl 89.1cm vs 실측 85cm(오차 4.1cm, 4.8%), yaw amcl 12.5° vs 실측 7.2°(오차 5.3°). 거리는 양호, **각도 오차가 상대적으로 큼** — 원인 미조사(자이로 스케일/바퀴 슬립 등 후보)
- [x] 7.3(2026-10-05): 사용자가 로봇을 손으로 들어서 다른 위치로 옮긴 뒤 `/initialpose`로 재설정 — 이건 AMCL이 "스스로" kidnap을 감지하고 재수렴한 게 아니라 **수동으로 알려준 것**이라 완전한 자동 kidnap 복구 시험은 아님. 자동 복구(`global_localization` 서비스 등)는 아직 안 함
- [x] 7.4(2026-10-05): Trial 1 수치 기록됨(위 7.2). 반복 시험(2회 이상 더)은 8.9와 함께 진행 예정이었으나 충돌로 중단(아래 8.9 참고)

## 8. Nav2 (PRD: `prd/slam-nav2.md`, 2026-10-04 Task 분해)
이번 단계는 **DWB까지만**(MPPI는 최종 단계, `prd/jetinspect-m-pipelines.md` 3절).
- [x] 8.1 Nav2 패키지 설치 확인(2026-10-04): `ros-jazzy-navigation2`+`ros-jazzy-nav2-bringup` 설치, 11개 패키지(`nav2_bringup`/`planner`/`controller`/`costmap_2d`/`behaviors`/`bt_navigator`/`dwb_core`/`smac_planner`/`regulated_pure_pursuit_controller`/`velocity_smoother`/`collision_monitor`) 전부 확인됨. `setup/ENVIRONMENT_SETUP.md` 기록
- [x] 8.2 Costmap 설정(2026-10-04): `jetrover_navigation/config/nav2_params.yaml`에 local/global costmap(static+obstacle+inflation) 작성. footprint는 바퀴 중심(±0.0975/±0.1121)+바퀴반경(0.0485)+여유로 `[[0.16,0.18],[0.16,-0.18],[-0.16,-0.18],[-0.16,0.18]]` 사각형(로봇팔은 주행중 안 움직인다는 전제로 2D footprint엔 미포함)
- [x] 8.3 Global Planner(2026-10-04): `nav2_smac_planner::SmacPlanner2D`(순수 격자 A*, mecanum이라 회전반경 제약 불필요). **플러그인 이름 오타(`/`아니라 `::`) 한 번 잡음**(troubleshooting/017)
- [x] 8.4 Local Controller(DWB, 2026-10-04): `vy_samples: 10`으로 옆이동 샘플링 열어둠(홀로노믹 활용). 속도 상한은 `jetrover_base`의 `max_linear`(0.2)/`max_angular`(1.0)과 동일하게 맞춤. **실제 옆이동이 나오는지는 아직 실주행으로 확인 안 함**(8.8에서)
- [x] 8.5 BT Navigator(2026-10-04): 기본 BT XML, `odom_topic: /odom`(EKF 출력과 일치)
- [x] 8.6 Recovery(2026-10-04): `spin`/`backup`/`wait` 설정. 실제 발동 확인은 8.11
- [x] 8.7 `jetrover_navigation/launch/nav2.launch.py`(2026-10-04): 우리 `localization.launch.py`(map_server+amcl) + `nav2_bringup`의 `navigation_launch.py`(params_file로 `nav2_params.yaml` 전달) 조합. **실제 로봇으로 전체 스택 기동 성공**(map_server/amcl/controller_server/planner_server/bt_navigator/behavior_server/smoother_server/velocity_smoother/collision_monitor/docking_server/route_server/waypoint_follower 전부 active, 중복 노드 없음 확인). `collision_monitor`/`docking_server`는 `nav2_bringup`이 끄는 옵션 없이 하드코딩으로 띄워서 공식 예시값으로 플레이스홀더 설정 추가해야 했음(docking_server는 실제 충전 도크 없음, 미사용) — troubleshooting/017
- [x] 8.8 실제 로봇으로 `NavigateToPose` 1회 성공 시연(2026-10-04): 호스트(원격 PC)의 RViz에서 "2D Nav Goal"로 짧은 거리 주행 성공. 가는 길에 호스트→Jetson DDS 디스커버리가 Jetson/호스트 양쪽의 다중 네트워크 인터페이스 때문에 비대칭으로 깨져 있던 것과, RViz의 기본 "Nav2 Goal" 툴이 Navigation 2 패널 없이는 애초에 아무 토픽/액션도 안 쏘는 설계였던 것, 두 가지를 같이 고쳐야 했음 — troubleshooting/018
- [~] 8.9 목표 위치/yaw 오차 측정, 반복 시험(3회 이상): **3회 시도, 2회 성공 + 1회 실패(충돌 없음).** 의자 경로였던 Trial 2 첫 시도는 충돌(troubleshooting/021) → 피해서 재시도해 성공. 거리오차 Trial1 4.1cm(4.8%)/Trial2 4.3cm(3.8%) — 안정적으로 양호. yaw오차 Trial1 +5.3°(과대추정)/Trial2 -6.7°(과소추정) — 방향이 매번 달라서 고정 바이어스보다는 노이즈성으로 추정. Trial 3은 장애물 없이도 목표 15.6cm 앞에서 "Goal failed"(progress checker가 근거리 미세조정을 "정체"로 오판한 것으로 추정, `required_movement_radius: 0.3`이 너무 큼 — 추가 조사 필요). 의자/저상 장애물 근처 자율주행은 8.12 해결 전까지 보류
- [~] **8.13(2026-10-06) depth 장애물 회피 + 직선 복귀 시험**: 상자(LiDAR에 안 보임)를 depth로 인식해 우회하고 `tools/nav/line_goal.py`(직선 웨이포인트)로 원래 선으로 돌아오는 동작. 로봇팔 홈 자세 변경(손목을 들어 카메라가 앞 18~51 cm를 연속으로 봄, `base.yaml`, 기준 depth 재촬영, margin 60 mm), global/local/collision_monitor 모두에 depth 소스, 상자 몸통 연장(0.3 m, 이후 0.15 m), 속도 0.12 m/s·가속 0.5, footprint 0.40×0.48(이후 0.36×0.50, 안전망은 실제 크기), BT 웨이포인트 반경 0.12. 사용자 육안: 요란함 감소·미세조정 개선·상자 안 침(마지막 RViz 시험 "얼추 됨"). 정량 시험(반복 횟수, 우회 폭, 도착 오차)은 아직 안 함 — 원인과 설정은 `troubleshooting/028`. **(2026-10-07 정정/추가)** footprint 실제 값은 0.36×0.50, 연장은 현재 0.15 m. DWB 생성기를 LimitedAccelGenerator로 바꿔 회피 동작도 달라졌으므로 회피 재시험 필요 — troubleshooting/031.
  - [~] 8.13.1 Nav2 직진 흔들림: `LimitedAccelGenerator`(후보를 현재 속도 ±0.05로 제한), `min_speed_xy` 무효 확인(0.0으로 정리). L0만, 실기 미검증
  - [x] 8.13.2 직진 A/B 실기(2026-10-09): shim + Twirling + DWB acc_lim_theta 3.0 적용 후 A(LimitedAccel) 6/6, C(Standard) 6/6. 직진 중 몸 방향 오차 중앙값 A 4.5° vs C 29.1° → **LimitedAccel 채택**. 시험 전용 BaseObstacle 0.02 조건 — troubleshooting/031 하단
  - [~] 8.13.10 DWB `xy_goal_tolerance` 0.12 추가(기본 0.25가 goal checker 0.15보다 커서 목표 앞 정지). 기본 설정 반영, 실기에서 B→A 성공으로 확인
  - [~] 8.13.11 AMCL 초기 위치 자동 추정(`jetrover_navigation/scan_match_init.py`, localization/nav2 launch에서 자동, `auto_localize:=false`로 끔). 실기 4회 사용(0.97~0.99), 모호할 때 거부 확인
  - [~] 8.13.12 DWB 데드존 가드 `min_speed_xy` 0.04 + `min_speed_theta` 0.1 (목표 앞 0.006 m/s 정지·A 끝 출발 실패 대책). A 조건 3/4 성공, 회전 4/4. 0.2는 LimitedAccel에서 회전 후보 0개라 실패
  - [x] 8.13.13 RotationShim + Twirling(10) + DWB acc_lim_theta 3.0: 지그재그(shim이 회전 중 넘김 + DWB 자체 회전) 해결, 직진 구간 방향 오차 ±2.5° 실측(2026-10-09)
  - [~] 8.13.7 local costmap scan/depth 레이어 분리(오래된 LiDAR 점이 안 지워져 통로가 막히던 문제). 실기에서 막힘 해소 확인, global은 아직 한 레이어
  - [x] 8.13.8 좁은 방 비용 균형: 원인은 가중치가 아니라 허용오차 충돌·데드존(수정됨). 기본 BaseObstacle 0.1로 직진 3/3 성공, 횡이탈 4~6 cm(2026-10-09). 회피 시 적정값은 회피 시험에서 다시 본다
  - [ ] 8.13.9 정지 후 바퀴 울림(미해결): 정지 프레임(0x03)은 바닥에서 효과 없음 → 기본 끔. 근본 대책은 자체 펌웨어에서 정지 시 PWM 0/적분 리셋 — troubleshooting/032
  - [~] 8.13.3 회피 재시험(2026-10-09, troubleshooting/034): 정면 상자 5회 실패(원인 수정) → 상자 오른쪽 20 cm 옮겨 **MPPI 3/3 성공**(15~17 s, collision_monitor 개입 없음). 우회 폭 37~42 cm로 과대(이상적 ~15) → inflation 0.40→0.25 적용, 주행 확인 전(배터리). DWB 같은 조건 비교도 남음
  - [~] 8.13.4 depth 기준 영상 홈 자세 게이트(`sparse_point_cloud`, ±0.08 rad + 1초 debounce, 벗어나면 발행 중지 → CM 정지). 실기: 팔 접힘(0.65 rad) 차단 확인, 0.04는 주행 중 백래시로 열림/닫힘 반복해서 완화함
  - [x] 8.13.5 카메라 감지거리 재설계(2026-10-09): 손목 joint4 1.6043 → 1.45, 바닥 시야 0.21~0.62 → **0.26~0.81 m**, 자기 바퀴 시야 밖, LiDAR 가림 변화 없음. 기준 depth 재촬영(이전 백업), 빈 바닥 거짓 점 0, 상자 범퍼 10/30/60 cm 모두 검출(60 cm는 아래 4 cm만). 기록 `docs/benchmarks/perception/home_pose_20261009.md`
  - [ ] 8.13.14 depth 레이어 `raytrace_min_range`: 새 홈 자세의 사각지대(범퍼~8 cm)에 들어간 상자를 depth 광선이 지우지 않게(회피 단계)
  - [x] 8.13.15 footprint 줄자 실측(2026-10-09): 36×26 cm → 플래너 0.38×0.28(+1 cm), collision_monitor 정지 0.40×0.30 / 감속 0.56×0.44. 이전 0.36×0.50은 미실측 과대값
  - [~] 8.13.16 MPPI(Omni) 설정 `config/mppi_followpath.yaml` + `make_variants.sh`로 `nav2_params_mppi.yaml` 생성. 로드맵 4단계를 앞당김(2026-10-09 사용자 승인). 2회 시험, 튜닝 전
  - [~] 8.13.17 회피 방식(정면 유지 + 대각 이동, 회전은 큰 방향 전환에서만): MPPI 목표 근처 기준 0.35 m 적용 후 **왕복 3/4 성공**(옆 이동 15~18 cm, 몸 방향 2~11°, 2026-10-09). 실패 1회(F2-4, 48 cm 우회 후 진동): **2026-10-10 bag 분석** — 회전 직후 전역 경로가 41 cm 우회로 바뀌고, 목표가 몸 기준 왼쪽 ~75°인 지점에서 40 s 정체(경로 정상, MPPI 출력 ≈0, 몸 옆 8 cm 안 센서 점). 막은 물체는 bag에 costmap이 없어 미확정 → `straight_trial.py --bag`에 scan/depth 점/costmap 추가(troubleshooting/034). M3~M8 접촉 없음
  - [~] 8.13.18 MPPI LateralRatioCritic(메카넘 대각 45° 제한, PRD `prd/mppi-lateral-ratio-critic.md`)
    - [x] 계산 함수 + 단위시험 6개(45° 경계, slack, 후진, 배치 독립, 30° 변형) — `src/jetrover_nav_plugins`
    - [x] 플러그인 등록·로드 확인(`Critic loaded : mppi::critics::LateralRatioCritic`), colcon test 22개 통과
    - [x] MPPI 연결(weight 50, PathAlign 14→6, PathFollow 5→3)
    - [x] 판정 지표 `diag50_frac`(`tools/nav/trial_metrics.py`, 단위시험 5개, CI) → `straight_trial.py` v3 CSV. 실기 bag 재계산: 성공 회차 0~1%, F2-4 정체 40%
    - [~] 시뮬레이션 비교 시나리오 S1/S2/S3 × dwb/mppi/mppi_nolr(`tools/sim/run_scenarios.sh`, `make_variants.sh`가 `nav2_params_mppi_nolr.yaml`도 생성) — 준비만, host 실행 대기
    - [ ] 실기 회피 왕복 4회: 명령 각도 > 50° 시간 비율 < 5%, 성공 ≥ 3, 최대 옆 속도/우회 시작점 비교(배터리 ≥ 10.3 V)
  - [ ] 8.13.6 장기: 기준 영상 차분 대신 TF/URDF self-filter + 바닥 제거(서보 백래시에 둔감하게)
- [ ] 8.10 성능 지표 기록 (**2026-10-06: 계획 `prd/nav2-baseline-test-plan.md`, 3시나리오×5회=15회, 도구 `tools/nav/benchmark/`(지표 단위시험 통과, **2026-10-10 실기 bag 4개로 analyze.py 검증**: 시간 0.1 s 이내 일치, 목표 오차는 마지막 /amcl_pose가 3~8 cm 과대 → /tf 기반으로 수정, `prd/nav2-baseline-test-plan.md`), 시험 자체는 미실시. 엔코더 odom 적용 전 baseline 용도**): CTE RMS, Goal Position/Yaw Error, Success Rate, Planning/Replanning Latency (표본 2개, 3회차 이후 집계)
- [ ] 8.11 (여유 있으면) 직선/90도 코너/좁은 통로/장애물 회피 개별 시나리오 — LiDAR 뒤쪽 160° 사각지대(로봇팔에 가려짐)가 costmap에서 오탐지 안 하는지 확인
- [~] **8.12(2026-10-05) 2D LiDAR가 못 보는 얇은 장애물(의자 다리 등) 대응** — troubleshooting/021.
  팔을 카메라-전방 home pose로 두고(14번 참고) `sparse_point_cloud`가 `/depth_cam/depth/points_sparse`를
  local costmap의 두 번째 `observation_sources`(`depth_cloud`, PointCloud2, min/max_obstacle_height=-0.1/2.0,
  raytrace/obstacle_max_range=3.0)로 들어가도록 `nav2_params.yaml` local_costmap의 `obstacle_layer`만 수정
  (global_costmap은 그대로 — 짧은 range라 static global에 넣을 가치 없음). 홈 포즈가 로봇 자신의 바퀴를
  근접 시야에 일부러 보이게 하므로, `sparse_point_cloud.py`에 TF 기반 self-filter(`_drop_self_points`,
  `base_footprint` 기준 footprint 사각형 밖 포인트만 통과, TF 안 준비되면 그 프레임은 publish 안 함)를
  추가해 로봇 자신을 장애물로 오인(troubleshooting/020 재발)하지 않게 함.
  **실기 검증(2026-10-05)**: self-filter 단독 — raw ~3196pt→필터 후 ~2947pt, 독립 검증 스크립트로
  publish된 포인트 전부(2946개) footprint 밖임 확인. Nav2 전체 스택 기동 후 `/local_costmap/costmap`에서
  로봇 자신의 footprint 셀 값=0(free, 오탐지 없음) 확인, `observation_sources`에 `scan depth_cloud` 둘 다
  반영됨 확인, map→base_footprint TF 정상. (재시작 중 `rplidar_composition`이 `/scan`을 못 내는 채로 멈춰
  있던 걸 발견해 재시작으로 해결 — Nav2와는 무관한 별개의 행잉, 원인 미확정.)
  **실제 저상 장애물 회피 재현 시험(2026-10-05) 결과: 실패.** 물체를 로봇 앞에 두고 목표를 보냈는데,
  근접 목표 부근에서 recovery가 4회 발동했고 그중 **후진(BackUp recovery로 추정)하면서 물건을 그대로
  밀고 지나감** — troubleshooting/022. 전진 방향 얇은 장애물 대응을 위해 넣은 depth_cloud가 **후진
  방향에는 전혀 도움이 안 됨**(카메라가 전방 고정, LiDAR는 원래부터 팔에 가려 후방 160도 사각) —
  로봇 뒤쪽이 통째로 센서 사각지대라는 구조적 문제를 새로 발견. 8.12는 "전진 중 얇은 장애물"만
  부분 해결된 상태이고, 후진 충돌 문제는 미해결로 `[~]` 유지.
  **후진 안전 조치(2026-10-05, 사용자 승인 후 적용)**: DWB `min_vel_x: 0`(원래 -0.2, 후진 완전 차단) +
  `bt_navigator`의 기본 BT XML에서 `<BackUp/>` 노드를 제거한 커스텀 XML(`config/behavior_trees/
  navigate_{to_pose,through_poses}_no_backup.xml`)로 교체, `behavior_server`의 `backup` 플러그인도
  제거. 재기동해서 `backup` action server 없이 전체 lifecycle이 깨끗이 active됨 확인(troubleshooting/022).
  **두 번째 전진 재시험 결과: 또 실패 (다른 원인) — troubleshooting/023.** 후진은 더 안 했지만, 이번엔
  **아예 회피 시도 자체가 없이 물체를 비비고 지나감.** raw depth를 직접 뒤져서 원인 확인: depth_cloud는
  물체를 정확히 보고 있었는데(바닥보다 뚜렷이 가까운 depth, base_footprint 변환 시 높이 4.5~8.8cm),
  8.12에서 넣은 self-filter가 이걸 "로봇 자기 자신"으로 오인해서 지워버리고 있었음 — 풋프린트 사각형
  (x<0.16, |y|<0.18)과 바퀴 높이(~9.7cm)가 이번 물체의 위치/높이와 겹쳐서 구조적으로 구분이 안 됐음.
  **self-filter를 교체함**: XY/높이 비교 대신, 홈 포즈에서 아무것도 없을 때 미리 찍어둔 기준 depth
  이미지(`config/depth_background_ref.npy`)와 지금 depth를 픽셀별로 비교해서, 30mm 이상 더 가깝게
  찍힌 픽셀만 "새로 생긴 물체"로 판단(`tf2_ros` 의존성도 제거됨 — 더 이상 TF 변환 불필요).
  **실기 재검증(2026-10-05)**: 물체 치운 상태로 기준 캡처(유효 91.4%) → 물체 없을 때 발행 0개(바퀴
  오탐지 없음) → 물체를 다시 35cm 앞에 둠 → 397개 포인트 발행, 높이/거리 일치 → local costmap에서
  로봇 전방 0.1~0.5m가 점유(94~100)로 찍히고 로봇 자신의 풋프린트 셀은 그대로 free(0) 확인.
  **아직 안 한 것**: 이 상태로 실제 `NavigateToPose` 재시험해서 진짜로 멈추거나 돌아가는지(코스트맵
  반영까지만 확인했고, 주행 중 회피 동작 자체는 아직 재시험 안 함) — 다음에 이어서.

### 8.14 Gazebo 시뮬레이션 (PRD `prd/gazebo-sim.md`, 2026-10-09 착수, 실행은 host)
- [x] 8.14.1 `jetrover_description` `sim_mode` 인자: 기본 false 출력이 변경 전 URDF와 동일(diff), true면 바퀴 4개 continuous(y축)+구 충돌
- [x] 8.14.2 지도 → 월드 생성기(`map_to_world.py`): 점유 737칸 → 벽 167개(덮는 칸 일치), `gz sdf -k` Valid(상자 있음/없음 2종)
- [x] 8.14.3 sim xacro(ros2_control 바퀴 속도·팔 위치, 메카넘 이방성 마찰, LiDAR/RGB-D/IMU): `gz sdf -p` 변환 성공(센서 3, 플러그인 1, fdir1 4, 회전 바퀴 4)
- [x] 8.14.4 launch/브리지/EKF/보조 노드(cmd_vel→stamped, depth float→16UC1 mm, 팔 홈 유지), Nav2/localization `use_sim_time` 인자. colcon test 12개 통과
- [ ] 8.14.5 host 실행(L5-sim): 데모 → JetRover 키보드 전후좌우·회전 방향, 센서 토픽, Nav2 A→B·상자 회피를 실기 좌표로 재현
- [x] 8.14.6 방 스캔용 팔 자세: 후보 A(손목만, 0.43 m/10.7°)·B(팔 세움, 0.52 m/5.9°) 실측 비교 → **B 채택**, 이동 순서 FK 확인·실기 왕복 확인(`docs/benchmarks/perception/scan_pose_20261010.md`, `tools/scan/README.md`). `arm_set_joint.py`: 첫 명령 유실(DDS 매칭 전) 수정, 실측 기준 0.25 rad 단계
- [ ] 8.14.7 방 RGB-D 스캔 녹화(`tools/scan/record_room_scan.sh`, B 자세) → host 재구성/정합/Blender

## 9. Navigation BT
- [ ] Nav2 BT 구조 이해
- [ ] 기본 NavigateToPose BT
- [ ] Recovery BT
- [ ] Custom BT XML
- [ ] 필요한 Custom BT node (예: ComputePath → FollowPath → 실패 → ClearCostmap → Retry)

## 10. 정밀 위치 정렬 (AprilTag + PnP + TF2)
- [ ] AprilTag detector
- [ ] Tag pose
- [ ] Desk marker, Charging marker, Workstation marker
- [ ] Nav2 coarse approach → AprilTag fine alignment
- [ ] 정차 오차 측정

## 11. RGB-D Camera
- [x] 카메라 확인: **Orbbec DaBai DCW** (RGB `2bc5:0559`+시리얼 있음, Depth `2bc5:0659`+**시리얼 없음**, legacy OpenNI/SDK v1 장치)
- [x] `jetrover_perception` 패키지, udev 규칙 설치로 USB 권한 문제는 해결
- [x] ~~막힘: OrbbecSDK v2 버그~~ **해결**: `ros-jazzy-orbbec-camera`(SDK v2, apt)는 이 장치를 못 찾는 업스트림 버그가 있음
  (`orbbec/OrbbecSDK_v2#51`). **`OrbbecSDK_ROS2`의 `main` 브랜치(SDK v1.10.37)를 소스로 빌드해서 apt 버전을 오버레이**하여 해결 (troubleshooting/013)
- [x] Jazzy driver: 소스 빌드(SDK v1) `orbbec_camera` 정상 동작, `Device DaBai DCW connected`
- [x] RGB topic(`color/image_raw` 640×360 rgb8, 약 23 Hz), Depth topic(`depth/image_raw`, 약 24 Hz), IR(약 23 Hz), CameraInfo, point cloud 모두 발행 확인
- [x] RGB 영상 실측 확인(2026-10-04): 픽셀 값 정상(평균 124, 97% non-zero), 직접 캡처로 시각 확인(그리퍼+바닥, 이후 사람 발+가구 — 팔 자세와 일치)
- [x] Depth 실측 확인(2026-10-04): 팔이 접힌 최초 자세에서는 유효 픽셀 0%(카메라가 그리퍼에 너무 가까워 최소 측정 거리 미만으로 추정)였으나, **사용자가 팔 각도를 수동으로 바꾼 뒤 유효 픽셀 89%, 거리 범위 293~914mm로 정상 측정 확인** — 최소 측정 거리(~29cm) 가설이 맞았음. 최소/최대 측정 거리 정확한 스펙값은 아직 미확인
- [x] RGB/Depth alignment(2026-10-04): depth 영상에서 깊이 불연속(물체 경계, gradient>15mm) 픽셀을 뽑아 RGB 위에 겹쳐보니 신발/가구/천 등 실제 물체 경계와 픽셀 단위로 정확히 일치(오프셋 없음). 스크립트 결과: `src/jetrover_perception/verification/rgb_depth_alignment_20261004.png`. `depth_registration: true` 설정이 실제로 작동함을 확인
- [x] Camera calibration 확인(2026-10-04): `/depth_cam/{color,depth}/camera_info`의 K 행렬이 640×360 해상도에 맞는 현실적인 공장 출하값(fx=fy≈362.5, cx≈318.5, cy≈177.4, distortion 비0) — placeholder/identity 아님. color/depth가 동일 K와 `frame_id: depth_cam_color_optical_frame`을 공유(registration 확인)
- [x] TF 연결(2026-10-04): `base_link → link4 → camera_connect_link → depth_cam_link → depth_cam_color_optical_frame` 전부 `lookup_transform`으로 실측 확인됨. 카메라 드라이버가 발행하는 실제 frame_id(`depth_cam_color_optical_frame` 등)가 URDF의 프레임 이름과 정확히 일치함(Hiwonder 벤더 URDF가 Orbbec 드라이버 네이밍에 맞춰 설계됨)
- [x] RGB/Depth 이미지 직접 캡처로 시각 확인 완료(2026-10-04, 둘 다 정상)
- [x] PointCloud 시각 검증(2026-10-05): `/depth_cam/depth/points` 203,916개 포인트, Z범위 0.29~0.92m(depth 이미지와 일치). top-down/front 투영 scatter plot으로 확인 — 바닥면이 평평하게 이어지고 노이즈/이상치 없음(`src/jetrover_perception/verification/pointcloud_20261005.png`). **섹션 11 완료**
  - **주의(2026-10-05, troubleshooting/019)**: Nav2 풀스택이 같이 떠 있는 상태에서 `enable_ir`+`enable_point_cloud`를 동시에 켜두면 카메라 드라이버가 에러 없이 조용히 멈추는 현상 발견(재부팅으로도 안 풀림, USB가 아니라 Jetson 자원 경합으로 추정). 그래서 `dabai_dcw.yaml` 기본값을 `enable_ir: false`/`enable_point_cloud: false`로 바꿈 — **지금은 RGB+Depth만 상시 켜짐**
  - **대체 수단(2026-10-05)**: `sparse_point_cloud.py` 노드 추가 — depth 이미지를 8픽셀 간격으로 성기게 샘플링한 뒤 camera_info로 XYZ 투영해서 `/depth_cam/depth/points_sparse`로 상시 발행(약 2,900개 포인트, CPU 9%, Nav2 풀스택과 동시에 돌려도 문제없음 확인). PRD의 실제 depth 사용처(3D XYZ 피킹, Safety Manager)는 애초에 dense cloud가 필요 없어서 이걸로 충분
  - Depth를 눈으로 보려면 `depth_colorizer.py`가 `/depth_cam/depth/image_colorized`(JET 컬러맵, bgr8, ~7Hz로 rate-limit)로 발행 — `web_video_server`(`jetrover_perception web_video.launch.py`)로 브라우저에서 스트리밍 확인 가능

## 12. Vision AI
- Detection (YOLO nano급 → ONNX → TensorRT FP16)
  - [ ] 모델 선택, ONNX export, TensorRT engine
  - [ ] ROS2 inference node, /detections
  - [ ] latency, FPS, GPU/RAM 측정
- Segmentation (Manipulation 단계)
  - [ ] instance segmentation, mask
  - [ ] Depth ROI, invalid depth filtering, median depth
- Tracking (ByteTrack)
  - [ ] Person tracking, Object ID 유지, lost/reacquire

## 13. 3D Perception (Detection/Mask → 픽셀(u,v)+Depth → 카메라 내부 파라미터 → XYZ_camera → TF2 → XYZ_arm_base)
- [ ] Pixel + Depth
- [ ] Back-projection, XYZ
- [ ] TF2 transformation
- [ ] object PoseStamped
- [ ] depth noise filtering
- [ ] 반복 측정 표준편차
- [ ] 실제 물체 위치 오차 측정

## 14. Robot Arm / MoveIt2 (MoveIt2 + OMPL + RRTConnect)
- [~] **버스 서보 ID 확인(2026-09-27, raw 프로토콜 레벨, ROS2 드라이버는 아직 없음)**: FUNC5로 ID 1~5 응답(관절, pulse 0~1000↔0~240°), **ID10 = 그리퍼**(ID 6~9,11~15는 무응답). PWM 서보(FUNC4) 채널 1~4는 응답은 하지만(전부 1500 기본값) 실제로 움직여도 육안으로 아무 변화 없음 — 미사용이거나 연결 안 된 채널로 추정. 각 서보 소폭 이동(±40~60 pulse)→원위치 왕복으로 실제 로봇에서 확인함
- [x] **Arm driver — 서보 위치 읽기 (2026-10-03~04)**: `jetrover_base`(`base_node`)에 FUNC5 read-position 폴링(5Hz round-robin, ID 1~5+10)과 `sensor_msgs/JointState` publish(`/joint_states`, 그리퍼는 `r_joint`만 — 나머지 5개 손가락 조인트는 URDF `<mimic>`으로 자동 계산됨)를 추가함. 변환식 `(ticks-center)*rad_per_tick*sign+offset`은 `~/AI_secretary_robot`의 `arm_servo_state_bridge.py`(Hiwonder 공식 jetrover_arm_moveit 부속)에서 가져옴.
  sign=+1 기본값은 틀렸었다(동어반복 검증이었을 뿐 물리 방향 미확인) → `~/AI_secretary_robot`의 실제 캘리브레이션(`config/servo_calibration.yaml`)대로 **sign=-1(전 관절)로 교체, 2026-10-04 사용자가 host RViz에서 실물 팔을 직접 움직이며 최종 확인함(잘 따라옴)** — center=500/offset=0/sign=-1로 확정.
  파라미터는 `config/base.yaml`에 노출(재조정 시 재컴파일 불필요).
- [x] **Arm driver — 쓰기(이동) 명령 (2026-10-05)**: `rrc_protocol`에 FUNC5 move(sub 0x01)/torque on-off(sub 0x0B/0x0C) 프레임 빌더 추가, `base_node`에 `arm/command`(JointState, rad)·`arm/torque`(Bool) 토픽 추가. **이 로봇 첫 소프트웨어 팔 이동**(그 전까진 전부 손으로 돌림). 기본 `arm_command_enabled: false`로 꺼둠(안전).
  안전장치: 모르는 관절/읽기 없는 관절/`arm_max_step_rad`(0.35) 초과 스텝이면 **명령 전체를 거부**(부분 실행 없음), pulse를 `arm_pulse_min/max`(100~900)로 클램프, 서보 프레임 간 150ms 큐잉(연속 프레임 유실 확인됨).
  실기로 알아낸 것: 서보 load_state 응답은 ~~`1=힘빠짐/0=걸림`~~ **(2026-10-05 정정: 1=걸림/0=풀림, 토크 서브커맨드도 0x0B=해제/0x0C=걸기, troubleshooting/027)**이고, **토크만 켜면 서보가 자기 내부에 저장된 옛 목표값으로 튀어버려서** 토크 ON 직후 반드시 "현재 위치로 이동" 명령을 보내야 한다(hold). 참고: `~/AI_secretary_robot`의 `ros_robot_controller_cpp/src/board.cpp`(Hiwonder 공식, FUNC5 서브커맨드 전체 표).
- [x] **Home pose(주행용 자세) 확정 (2026-10-05)**: joint1~5 = `[0.0, -0.553, 1.688, 1.671, 0.017]` rad, 그리퍼 닫힘. 카메라가 로봇 자기 바퀴(14.5cm)부터 바닥까지 끊김없이 보여서, 기존에 안 보이던 로봇 바로 앞 구간(troubleshooting/021의 저상 장애물 사각지대)을 depth로 커버함. `/scan` 가림은 기존과 동일(약 49%, 악화 없음). joint2/3를 더 접어보기도 했으나 `arm_pulse_min`/`arm_pulse_max` 안전 클램프에 걸리고 근접 거리도 오히려 나빠져서 기각 — 지금 값이 탐색 범위 내 최선.
  `base.yaml`의 `arm_home_pose_rad`에 기록, `arm_move_home_on_start`(기본 false)를 켜면 기동 시 처진 자세에서 0.3rad/스텝으로 서서히 복귀 — 실기 2회 종단 검증함(토크 ON+hold 후 스텝 이동, "arm reached home pose" 로그 확인). 평소엔 꺼둠(그림 8.12/Safety Manager에서 실제로 쓸 때 켜는 걸로).
  **아직 안 한 것**: depth를 Nav2 costmap 관측 소스로 실제로 연결하는 것(8.12), MoveIt2/IK
- [x] **URDF 실제 메쉬/조인트 반영 (2026-10-03)**: `jetrover_description`에 Hiwonder 공식 메쉬+xacro 통합 완료(4번 섹션 참고). `joint_limits.yaml`은 `~/AI_secretary_robot/src/control/jetrover_arm_moveit/config/joint_limits.yaml`에 이미 있음(가져오기는 아직 안 함). ID3은 pulse=5로 끝단 근접 — 안전 pulse 범위 확정은 아직
- [ ] IK
- [~] MoveIt Setup Assistant (2026-10-06): `src/jetrover_manipulation/`에 SRDF/kinematics(TRAC-IK)/joint_limits/OMPL/controllers/launch(plan_only|real)를 Humble 참고 설정에서 Jazzy용으로 작성, SRDF-URDF 일치 검증·빌드까지. **MoveIt 설치 후 plan_only 계획 시험 통과(관절/위치 목표, 실행 없음). 5자유도라 TRAC-IK 대신 KDL position_only_ik 사용.** 충돌 매트릭스는 host Setup Assistant로 재생성해 합침(그리퍼 연동부는 수동 보존), host RViz 연동·충돌 검출 확인.
- [ ] PlanningScene, Collision model
- [ ] RRTConnect, Pose goal
- [~] 실제 arm trajectory (2026-10-06): 실행 브리지 + base_node `arm/command_timed` 구현, 단위 7개·dry_run 종단 시험 통과. **실기 왕복 시험 통과**(joint1 ±0.10, joint2 ±0.15 rad, 4/4 SUCCESS, 배터리 9.97 V). RViz 큰 목표/그리퍼/충전 후 반복은 아직.
- [x] Gripper (ID10으로 확인됨)

## 15. Grasp (1차: Segmentation + Depth + Geometry + Rule-based)
- [ ] Object centroid, orientation estimate
- [ ] pre-grasp / grasp / retreat pose
- [ ] top grasp, side grasp
- [ ] collision check
- [ ] grasp success verification
- [ ] (고도화) AnyGrasp / GraspNet 계열 비교 — 우선순위 낮음

## 16. MoveIt Servo / Visual Servoing
- [ ] MoveIt Servo
- [ ] Cartesian velocity
- [ ] target pose error
- [ ] Visual Servo loop
- [ ] safety velocity limit

## 17. Mission Behavior Tree (BehaviorTree.CPP)
목표: FetchObject = CheckRobotReady → NavigateToDesk → AlignToDesk → DetectObject → EstimatePose → Pick → VerifyGrasp → NavigateToUser → Deliver
- [ ] BehaviorTree.CPP
- [ ] Mission Manager
- [ ] Navigate / Detect / Grasp Action wrapper
- [ ] Retry, Timeout, Fallback, Recovery, Cancel
- [ ] Emergency abort

## 18. FastAPI Backend (React → REST/WebSocket → FastAPI → ROS2 Bridge → Robot)
개발 순서(9단계, 전체 통합 이후)상 아직 착수 안 함. 상세: `prd/jetinspect-m.md` 17절, `prd/jetinspect-m-pipelines.md` 18절.
- [ ] FastAPI project
- [ ] /api/status, /api/mission, /api/navigation/goal, /api/mission/cancel, /api/robot/stop
- [ ] WebSocket
- [ ] ROS2 bridge, ROS2 Action Client
- [ ] Diagnostics aggregation
- FastAPI가 직접 PWM이나 motor packet을 보내지는 않는다.

## 19. React 관제 UI (React + TypeScript + Vite)
- [ ] Dashboard, Robot online/offline
- [ ] Battery, STM32 heartbeat
- [ ] Map, Robot pose, Global path
- [ ] Camera, Detection
- [ ] Current Mission, BT current node
- [ ] CPU/GPU/RAM, Temperature
- [ ] Errors, Mission history
- [ ] Emergency stop / mission cancel

## 20. Robot Screen UI (본체 HMI, Chromium kiosk mode)
2026-10-10 확인: 본체 디스플레이는 **1024×600(DP-1), 터치 없음** → **출력 전용 화면**. 조작(Home/Cancel/Stop, Auto/Manual)은
게임패드·웹(13단계 관제 페이지)·음성으로. 비상정지는 화면에 의존하지 않는다. 현장 시험 모니터링은 host RViz로 해결(별도 화면 불필요).
- [ ] Battery, Robot state, Current mission
- [ ] Camera / 점검 결과(게이지 사진+판정값, Stack Light 상태)
- [ ] Auto / Manual **표시**(전환은 게임패드/웹)
- [ ] Home / Cancel / Stop **상태 표시**(입력은 게임패드/웹/음성)
- [ ] 간단한 음성 상태 표시(듣는 중/말하는 중)
- [ ] (데모용, 선택) 로봇 표정 화면

## 21. Database (초기 MySQL → 최종 PostgreSQL + VectorDB — 2026-09-28 확정, `prd/jetinspect-m.md` 17절)
**신뢰수준: 계획.** SQLite 단일DB안(직전 결정)은 폐기. 초기 개발은 MySQL + SQLAlchemy로 빠르게 가고,
최종 단계에서 PostgreSQL로 이전 + RAG용 별도 VectorDB를 붙인다(제품 미정 — 24번 섹션).
- [ ] MySQL로 초기 스키마 구현: missions, robot_events, detections, system_metrics, alerts
- [ ] locations, documents, document_chunks
- [ ] (최종 단계) PostgreSQL로 마이그레이션

## 22. Semantic Map (desk, charger, door, delivery_station, storage)
- [ ] 장소 이름, x, y, yaw, type, description
- 목표: "책상으로 가" → LLM → desk → DB(x,y,yaw) → Nav2

## 23. LLM / VLM
- LLM: [ ] 자연어 명령 분석 · [ ] Structured JSON · [ ] Mission 생성 · [ ] Tool calling · [ ] BT에 parameter 전달
- VLM: [ ] Scene understanding · [ ] Target disambiguation · [ ] 이미지 질의응답 · [ ] object semantic 판단
- 원칙: VLM → What?, YOLO + Depth → Where?

## 24. RAG (Document → Chunk → Embedding → VectorDB → Top-K → LLM)
자료: JetRover manual, STM32 protocol, STM32 hang NOTES, Nav2 config, MoveIt setup, Camera/LiDAR manual, Troubleshooting, Calibration 기록
- [ ] Document loader, Chunker, Embedding
- [ ] **VectorDB 제품 조사·결정** — PostgreSQL `pgvector` 확장으로 21번 DB 안에 통합할지, Qdrant/Milvus/Chroma 등 독립 VectorDB로 분리할지 미정(계획)
- [ ] Metadata, Retrieval
- [ ] Reranking 필요 여부 검토
- [ ] RAG API
- [ ] 관제 UI Chat

## 25. Robot Memory
- [ ] Mission memory, Detection memory, Object-location memory
- [ ] Error history, Robot event history
- [ ] 자연어 검색

## 26. Voice AI (Mic → VAD → STT → LLM/Intent → BT → Robot → TTS)
- [x] **하드웨어 확인(2026-09-28)**: 마이크 어레이 = USB `card 0` (XFM-DP-V0.0.18, iFlytek 원거리 마이크 어레이 보드, `arecord -D hw:0,0`), 스피커 = USB `card 1` (GeneralPlus USB Audio Device, `aplay -D plughw:1,0`, mono는 `plughw` 필요 — `hw`는 채널 수 불일치로 실패). 4초 녹음 후 재생 왕복으로 실사용 확인(목소리 들림, 무음 아님)
- [ ] VAD, STT, Intent Router, LLM, TTS — **전부 미착수**. STT/TTS 엔진 자체가 아직 하나도 안 깔려 있음(whisper/vosk 등 확인함, 없음)
- 안전 명령 STOP / CANCEL / HOME은 LLM 없이 deterministic하게 처리한다.

## 27. Diagnostics / Monitoring
- [x] STM32 heartbeat, 배터리 전압(`/battery_state`)
- [ ] /diagnostics
- [ ] IMU Hz, LiDAR Hz, Camera FPS
- [ ] Battery
- [ ] Jetson RAM, CPU, GPU, EMC, Temperature
- [ ] Nav2 State, Mission State
- [ ] Error alert
- 웹 관제와 연결한다.

## 28. Logging / Rosbag
- [ ] rosbag 자동 recording (Mission 시작/종료 시)
- [ ] 오류 발생 전후 기록
- [ ] DB에는 rosbag path만 저장
- [ ] Log rotation, disk usage 관리
- 권장 토픽: /cmd_vel /odom /imu/data_raw /scan /tf /tf_static /detections /diagnostics

## 29. Deployment (개발: SSH + tmux)
- [ ] systemd, 자동 ROS bringup
- [ ] FastAPI 자동 실행, DB 자동 실행, React serving
- [ ] watchdog/restart policy, log rotation
- [ ] boot 후 자동 로봇 준비
- Docker: [ ] FastAPI container · [ ] PostgreSQL container · [ ] React build · [ ] ROS2 container 적용 여부 검토 (로봇 제어까지 Docker화는 후순위)

## 30. Edge AI 최적화 (Jetson Orin Nano 8GB)
- [ ] YOLO PyTorch baseline → ONNX → TensorRT FP16 → (필요 시 INT8)
- [ ] FPS, latency, peak RAM, GPU utilization, temperature, power
- [ ] 여러 노드 동시 실행 stress (Nav2 + Camera + YOLO + MoveIt + FastAPI + DB)

## 31. 최종 시스템 통합
"책상에서 빨간 캔 가져와" → Voice/React → LLM → Structured Mission → BehaviorTree.CPP → NavigateToDesk(Nav2) → AprilTag Align → YOLO → RGB-D → 3D XYZ → TF2 → MoveIt2 → Grasp → Verify → NavigateToUser → Deliver → DB/Web 관제에 결과 기록
- [ ] 전체 시나리오 통합 및 반복 시험
