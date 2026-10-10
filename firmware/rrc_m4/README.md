# rrc_m4 — STM32F407 RRC 보드 자체 펌웨어 (코드/빌드 완료, 실기 검증 전)

PRD: `prd/rrc-microros-firmware.md`, 시험 계획: `prd/rrc-microros-firmware-test-plan.md`, 핀맵과 신뢰 수준: `firmware_source/PINMAP.md`.
**2026-10-10 처음 보드에 올림**(RRC, 모터 출력 OFF): 통신·IMU·배터리 텔레메트리, LED, 상태 OLED(SSD1306 128×32 I2C — SPI LCD가 아니었음), 버스 서보 읽기, 모터 fault 핀 정상(troubleshooting/035). 모터 구동·서보 쓰기·버튼·SBUS 등은 미확인.

## 구조

```
lib/protocol  RRC 프레임 코덱 + FUNC 0~9 + 프로젝트 확장 FUNC 0x20~0x23 (순수 C)
lib/core      PID / 엔코더 모터 / 메카넘 / robot_ctrl(안전) / IMU(MPU6050·QMI8658 자동판별) / 버스·PWM 서보 /
              SBUS / 게임패드 / 버튼 / 부저·LED 패턴 / 배터리 / local_drive (순수 C, 호스트 단위 시험)
lib/comm      rrc_adapter: 바이트 → 프레임 → robot_services 호출, 텔레메트리 송신 (순수 C)
app/          STM32 HAL + FreeRTOS: 드라이버(drv_*), 태스크(tasks.c), USB 호스트 게임패드, micro-ROS 노드
third_party/  CMSIS, STM32F4 HAL, USB Host, FreeRTOS (vendor, README에 출처/커밋)
micro_ros/    micro-ROS 정적 라이브러리/에이전트 빌드 스크립트 (README 참고)
cmake/        ARM 툴체인 + 펌웨어 타깃
```
설계 원칙: **통신(micro-ROS, RRC)은 모터/PID/IMU/Safety를 모르고**, 둘 다 `robot_set_velocity()` / `robot_set_wheel_rps()`
공통 API로만 들어간다. 통신이 모터를 직접 만지지 않는다.

## 빌드

호스트 단위 시험(ARM 불필요):
```bash
cmake -S . -B build && cmake --build build
./build/lib/protocol/test_protocol; ./build/lib/core/test_core; ./build/lib/comm/test_comm
```
ARM 펌웨어 (툴체인은 `~/.local/opt/stm32/bin`):
```bash
export PATH="$PATH:$HOME/.local/opt/stm32/bin"
cmake -S . -B build-arm -DCMAKE_TOOLCHAIN_FILE=cmake/arm-none-eabi.cmake -DCOMM_MODE=RRC          # 기존 jetrover_base와 호환
cmake --build build-arm -j2                                                                        # -> build-arm/rrc_m4.{elf,bin,hex}
cmake -S . -B build-arm-uros -DCMAKE_TOOLCHAIN_FILE=cmake/arm-none-eabi.cmake -DCOMM_MODE=MICROROS  # micro_ros/build_microros_lib.sh 먼저
```
옵션: `-DMOTOR_ENABLE=ON`(기본 OFF: 모터 출력 0, L2 브링업용), `-DLOCAL_DRIVE_ENABLE=ON`(블루투스/게임패드/SBUS 직접 주행, 기본 OFF).

## 통신 모드 (`COMM_MODE`)
| | RRC | MICROROS |
|---|---|---|
| USART3 (호스트, `/dev/ttyACM0`, 1 Mbaud) | RRC 프레임 (`jetrover_base`와 와이어 호환) | XRCE-DDS 시리얼(HDLC 프레이밍) — agent 필요 |
| USART1 (ISP 포트, `/dev/ttyACM1`, 115200) | 안 씀 | **RRC fallback/debug** (텔레메트리 전체 + 명령) |
같은 UART에 두 프로토콜을 섞지 않는다. micro-ROS 인터페이스는 `app/inc/comm_microros.h` 상단 주석.

**주의**: ISP 포트(`/dev/ttyACM1`)를 열 때 `DTR=0 & RTS=1`이 되면 STM32가 부트로더로 들어가 멈춘다
(`troubleshooting/001`). pyserial은 `dsrdtr=False`로 열고 `ser.dtr = True; ser.rts = False`를 즉시 지정한다.

## 안전 기능 (벤더 펌웨어에 없던 것)
- 호스트 명령 timeout `CMD_TIMEOUT_MS`(기본 1 s): 명령이 끊기면 MCU가 스스로 바퀴를 정지 (`robot_ctrl.c`)
- e-stop 래치, 저전압 차단(9.5 V, 10.0 V에서 해제), 바퀴 하나라도 runaway/stall이면 전체 정지
- **엔코더 runaway 래치**: 속도 명령이 큰데 PWM이 포화 근처에서 1 s 넘게 실제 속도가 안 따라오면(엔코더 부호 오류 = 양의 되먹임 포함) 래치 (`encoder_motor.c`)
- 감시 태스크가 control/imu/comm_rx/ui heartbeat를 모두 확인할 때만 IWDG(500 ms)를 먹인다. 하나라도 멈추면 모터 PWM을 즉시 0으로 하고 리셋을 기다린다
- 모터 드라이버 fault 핀(PD3) 감시, 명령의 NaN은 0으로 처리, 범위 밖 모터 ID 무시
- 부팅 직후 GPIO는 벤더 펌웨어와 같은 안전 상태, PWM 서보는 첫 명령 전까지 펄스를 내보내지 않음

## 프로토콜 확장 (이 펌웨어만의 FUNC, 벤더/호스트가 모르면 무시)
`0x20` STATUS(10 Hz), `0x21` WHEEL(엔코더 rps/카운터, 50 Hz — 벤더 펌웨어가 안 주던 값), `0x22` DIAG_CMD(e-stop 해제, timeout, PID, raw PWM),
`0x23` RAW_HID(게임패드 원시 리포트). 자세한 바이트는 `lib/protocol/include/rrc_ext.h`.

## 아직 확인되지 않은 것 (브링업에서 확인, `firmware_source/PINMAP.md`의 "추정")
모터 2~4의 PWM 쌍/극성, 엔코더 부호, PID 게인·`ticks_per_circle`, IMU 칩→보드 축 변환, 버스 서보 방향 핀 역할, PWM 서보 핀 순서,
~~LCD 제어 핀 배정~~(화면은 I2C OLED로 확정), 게임패드 HID 리포트 레이아웃, 부저 능동/수동 여부.

## SWD 디버거 첫날 순서 (2026-10-10 작성; 실제 디버거는 J-Link OB 클론)
목표: **지금 칩의 플래시를 SWD로 백업**하고 연결을 확인하는 것까지. 자체 펌웨어 flash는 이 순서가 다 끝난 뒤 **따로 승인**받는다.

| # | 할 일 | 명령/기준 | 멈추는 조건 |
|---|---|---|---|
| 0 | 설치(sudo, 사용자) | `sudo apt install openocd stlink-tools` → `setup/ENVIRONMENT_SETUP.md` 기록(2026-10-10 완료) | |
| 1 | 준비 | base_node/Nav2 종료(`pgrep -x base_node` 없음), **모터 스위치 OFF**, 바퀴 띄움, 배터리 ≥ 10.5 V | |
| 2 | 배선 | 보드 SWD 헤더(`firmware_source/BOARD_CONNECTORS.md` "GPIO expansion and SWD debugging") ↔ 디버거. **2026-10-10 실제 디버거는 J-Link OB 클론**(USB `1366:0101`, 펌웨어 "J-Link ARM-OB STM32" 2012) → **VTref(1번)→보드 3.3V, SWDIO(7), SWCLK(9), GND(4)** 4선(VTref는 전압 감지 입력, 전원 공급 아님. 5V 공급 핀 19번 미연결). ST-Link라면 SWDIO/SWCLK/GND만(3.3V 출력 핀 연결 금지). NRST는 우선 미연결. **SEGGER 공식 툴로 디버거 펌웨어 업데이트 금지**(클론 벽돌 위험) — openocd 사용 | 헤더 핀 순서가 실크와 다르면 멈춤 |
| 3 | 연결 확인 | `openocd -f interface/jlink.cfg -c "transport select swd" -f target/stm32f4x.cfg -c "reset_config none" -c init -c "dap info" -c shutdown` → VTarget 3.3 V, DPIDR 0x2ba01477, Cortex-M4 (2026-10-10 확인됨, halt 없음) | 전압 0 V/IDCODE 없음이면 배선 확인 |
| 4 | **백업** | `tools/stm32_diagnostics/swd_backup.sh` (기본 J-Link, `ADAPTER=stlink` 가능) → `~/firmware_source/swd_backup_<날짜>/` (512 KB를 **두 번** 읽어 해시 일치 확인) | 두 번 읽은 값이 다르면 `SPEED=400`으로 재시도, 그래도 다르면 멈춤(쓰기 시도 금지) |
| 5 | 백업 확인 | `compare.txt`: 앞부분 == `decompile/RosRobotControllerM4.bin`(09-27 재플래시한 vendor 빌드) 예상. 다르면 기록하고 원인 확인 | |
| 6 | 백업 이중화 | 백업 폴더를 host PC에도 복사(`firmware_source`는 git 제외) | 복사 전 flash 금지 |
| 7 | 정상 복귀 확인 | ST-Link 분리 → 전원 재투입 → base_node 기동, IMU/배터리 텔레메트리 정상 | 텔레메트리 없으면 RST 버튼, 그래도 없으면 멈춤 |
| 8 | (기회되면) 바퀴 울림 측정 | 울리고 있을 때만: `tools/stm32_diagnostics/swd_motor_probe.sh 50 100 > Log/swd_motor_probe_<날짜>.txt` (halt 없음, troubleshooting/032) | 첫 실행에서 보드가 리셋되면 이 방식 중단 |
| 9 | 다음 승인 지점 | 자체 펌웨어 `-DMOTOR_ENABLE=OFF` 빌드 flash → 브링업 L2(LED→UART→IMU→배터리), `prd/rrc-microros-firmware-test-plan.md` 7번 | **여기서 사용자 승인** |

**2026-10-10 진행 결과**: 0~5 완료 — 연결(3.3 V, DPIDR 0x2ba01477), 백업 2회 해시 일치, vendor 빌드와 동일(나머지 0xFF), RDP 0.
백업 `~/firmware_source/swd_backup_20261010_130702/`. 6 host 복사 완료(사용자). 7 정상 복귀: 디버거 연결된 채 base.launch → IMU 111 Hz, 배터리 12.55 V(1 Hz), 관절 6개 읽기 정상, silent/오류 로그 없음 → **vendor 펌웨어 그대로 정상 동작**. 다음은 9(자체 펌웨어 flash, 승인 지점).

**2026-10-10 9단계(자체 펌웨어 flash, 사용자 승인·사용자 실행)**: `build-arm-bringup`(RRC, `MOTOR_ENABLE=OFF`).
첫 flash는 lockup(크리스털 16 MHz를 8 MHz로 가정), 두 번째는 0.8초마다 IWDG 리셋(LCD 태스크 스택 넘침) — 둘 다 수정(troubleshooting/035).
세 번째: uptime 연속 증가, IMU/WHEEL 50 Hz, STATUS 10 Hz, 배터리 2 Hz 12.528 V, CRC 오류 0.
flash 명령(사용자 실행, 쓰기): `openocd -f interface/jlink.cfg -c "transport select swd" -c "adapter speed 400" -f target/stm32f4x.cfg -c "reset_config none" -c init -c "reset halt" -c "stm32f2x mass_erase 0" -c "flash write_image build-arm-bringup/rrc_m4.elf" -c "verify_image build-arm-bringup/rrc_m4.elf" -c "reset run" -c shutdown`
(`adapter speed 400`은 target cfg가 2000 kHz로 덮어씀 — 출력의 "clock speed 2000 kHz", 그래도 문제없었음).

롤백: 4번 백업(`st-flash write flash_512k.bin 0x08000000`) 또는 vendor `.hex`(UART1 부트로더, troubleshooting/001). 둘 다 쓰기 작업이라 승인 필요.
주의: 읽기 중 코어가 멈추면 IWDG(약 20 ms)로 리셋될 수 있다 — 모터 스위치를 끄는 이유.

## 라이선스/출처
`lib/*`와 `app/*`는 이 프로젝트에서 새로 작성했다(공식 문서의 공개된 알고리즘/프로토콜 설명을 근거로 함, Hiwonder 코드를 복사하지 않음).
`third_party/`는 `third_party/README.md` 참고(BSD-3-Clause/Apache-2.0/MIT).
