# PRD: RRC 보드 자체 펌웨어 완성 + micro-ROS 적용

작성 2026-10-05. 근거: 사용자가 준 `firmware_source/decompile/JetRover_Hiwonder_Official_Pack.zip`(Ghidra 결과 + 재구성 C 골격),
Hiwonder 공식 문서 저장소(`Hiwonder-docs/ROS-Robot-Control-Board` 07746775, `source/docs/1~3_*.md`),
기존 `firmware/rrc_m4/lib/protocol/`(RRC 코덱), 실기에서 확인한 프로토콜(`AGENTS.md` 확정 사실).
이 문서는 1번 섹션 "자체 STM32 펌웨어 재작성"의 후속 PRD이며 `~/.claude/plans/enchanted-chasing-sky.md`를 대체하지 않고 이어간다.

## 목표
1. 재구성 C 골격의 **미구현/미확정 부분을 전부 채워** STM32F407(RRC 보드)용 펌웨어를 빌드 가능한 상태로 만든다
   (모터 4축 PID, 엔코더, 메카넘, IMU, 배터리, 부저/LED, 버튼, PWM 서보, 버스 서보, SBUS, USB 게임패드, 블루투스, LCD, 안전기능).
2. 통신 계층을 추상화해 **micro-ROS(주) + RRC(대체/디버그/공장 호환)** 구조를 만든다. 모터/PID/IMU/Safety는 통신을 모른다.
3. hang 원인 후보(태스크 단위 데드락)를 구조적으로 막는다: 태스크별 heartbeat 기반 IWDG, 명령 timeout(MCU 내부), 통신 복구.

## 확정된 설계 결정 (사용자 지시 2026-10-05)
- **micro-ROS = Primary, RRC = Fallback/Debug/Factory compat.** 같은 UART에 두 프로토콜을 섞지 않는다.
- 두 통신 계층은 **공통 API `robot_set_velocity()` / `robot_set_wheel_rps()` 로만** 제어부에 들어간다. 통신이 모터를 직접 만지지 않는다.
- 빌드 옵션 `COMM_MODE`: `RRC`(USART3 1 Mbaud, 기존 `jetrover_base`와 와이어 호환, 첫 flash용) / `MICROROS`(USART3 1 Mbaud XRCE-DDS
  UART DMA, RRC는 USART1 115200 = ISP 포트에서 디버그/대체 경로).
- 핀맵은 **정적 분석 + Hiwonder 공식 문서 교차검증**으로 확정/추정 구분(`firmware_source/PINMAP.md`). SWD 실측은 ST-Link 도착 후.
- 이번 작업 범위는 **코드 + 빌드 + 호스트 테스트 + Jetson 쪽 agent/launch까지**. **flash와 모터 시험은 하지 않는다** (별도 승인).

## 범위
- `firmware/rrc_m4/`: core(순수 C, 호스트 테스트) / drivers(HAL) / comm(rrc, microros) / app(FreeRTOS) / port(보드 핀 테이블)
- STM32CubeF4 HAL/CMSIS/USB Host, FreeRTOS-Kernel vendor (BSD/MIT, 출처 기록)
- micro-ROS static library 빌드(Jetson 네이티브, docker 불가) + 노드: `/cmd_vel` 구독, `/imu/data_raw`, `/wheel_states`(rps), `/battery_state`, `/diagnostics` 발행, PID/부저/LED 서비스
- Jetson: `micro_ros_agent` 설치/launch, `jetrover_base`와의 전환 방법(launch 인자), 문서
- 문서: `firmware_source/PINMAP.md`, 체크리스트, troubleshooting

## 비범위
- 실제 flash, 모터 구동 시험, 바닥 주행 (승인 후 별도 단계)
- 기존 `jetrover_base`(RRC) 변경 — micro-ROS 경로는 별도 launch로 추가하고 기존 경로는 그대로 둔다
- Nav2/EKF 쪽 변경 (엔코더 피드백이 생기면 wheel odom 전환은 별도 작업)

## 제약
- 안전 규칙: flash/모터 시험은 승인 필요, 원본 백업(`RosRobotControllerM4_dumped_backup.bin`)은 이미 존재
- Motor2~4의 PWM 쌍/극성, PID 게인, ticks_per_circle, IMU 칩(MPU6050/QMI8658)은 **추정/미확정** → 부팅 시 자동 판별(IMU)
  또는 설정 테이블 + 브링업 진단 모드로 검증 후 사용. 확정 전 기본값은 모터 출력 비활성(`MOTOR_ENABLE` 빌드 플래그 0).
- RAM 192KB(CCM 64KB 포함)/Flash 512KB 안에서 micro-ROS + FreeRTOS + USB Host가 들어가야 함 → 빌드 후 `size` 보고

## 완료 기준
- L0: 호스트 단위 테스트 전부 통과, ARM 빌드 2종(RRC/MICROROS) 성공 + `size` 기록, 링커 영역 초과 없음
- L1: 호스트에서 RRC 코덱+공통 API+안전 timeout 시뮬레이션, micro-ROS agent와 PC-호스트 빌드 클라이언트 왕복(가능한 범위)
- 체크리스트 `[x]`는 **실기 검증 후에만**. 이번 작업 결과는 전부 `[~]`(코드/빌드까지)로 기록한다.
