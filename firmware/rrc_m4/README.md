# rrc_m4 — STM32F407 RRC 보드 자체 펌웨어 (코드/빌드 완료, 실기 검증 전)

PRD: `prd/rrc-microros-firmware.md`, 시험 계획: `prd/rrc-microros-firmware-test-plan.md`, 핀맵과 신뢰 수준: `firmware_source/PINMAP.md`.
**아직 한 번도 보드에 올리지 않았다.** 이 디렉터리의 결과는 L0(빌드 + 호스트 단위 시험)까지 확인된 것이다.

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
LCD 제어 핀 배정, 게임패드 HID 리포트 레이아웃, 부저 능동/수동 여부.

## 라이선스/출처
`lib/*`와 `app/*`는 이 프로젝트에서 새로 작성했다(공식 문서의 공개된 알고리즘/프로토콜 설명을 근거로 함, Hiwonder 코드를 복사하지 않음).
`third_party/`는 `third_party/README.md` 참고(BSD-3-Clause/Apache-2.0/MIT).
