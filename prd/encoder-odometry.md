# PRD: 엔코더 기반 wheel odometry (open-loop → measured)

신뢰 수준: **계획**. 시험 계획: `prd/encoder-odometry-test-plan.md`. 상위: `docs/ROADMAP.md` 2~3단계,
펌웨어 PRD `prd/rrc-microros-firmware.md`(이 문서는 그 중 "엔코더 피드백을 odom까지 연결"하는 부분만 다룬다).
작업 방식: 3-File System (이 PRD → `checklist/PROJECT_CHECKLIST.md`의 sub-task → TEST_PLAN).

## 목표
`cmd_vel`을 적분한 open-loop `wheel_twist`를, **엔코더에서 측정한 바퀴 속도**로 만든 `wheel_twist`로 대체한다.
같은 Nav2 baseline(15회)을 전/후로 돌려 AMCL/Nav2 성능 개선량을 **수치로** 증명한다.

## 배경 / 문제 (확정: 실측)
- vendor 펌웨어는 엔코더/바퀴 속도를 호스트로 보내지 않는다(캡처·SDK·공식 PDF로 확인). 현재 `wheel_twist` = 명령 속도.
- 실측: 전진·옆이동은 명령과 거의 일치(0.99), **회전은 명령 대비 약 81%**. 마찰/슬립/데드존/전압 영향이 반영 안 됨.
- EKF 입력은 `wheel_twist`(vx, vy)와 자이로 yaw rate뿐 (`jetrover_base/config/ekf.yaml`).
- 보드는 4채널 엔코더 모터를 지원하고(`firmware_source/PINMAP.md`: 엔코더 타이머 확정), 자체 펌웨어에 엔코더→rps 코드가 L0까지 있다.

## 범위
1. 자체 펌웨어(`firmware/rrc_m4`) 엔코더 실기 bring-up: 엔코더 부호, ticks/rev, rps 측정값 검증 (flash는 사용자 승인).
2. 호스트에서 측정 rps → `mecanum_forward()` → `wheel_twist` → EKF 연결 (경로는 아래).
3. 공분산을 실측 오차에서 근거 있게 설정 (현재 `[0.02, 0.02, 0.05]`는 **미검증 값**).
4. Before/After 성능 비교 (Nav2 baseline 동일 조건 재시험).

## 비범위
- `base_node` 전체를 `ros2_control`/`mecanum_drive_controller`로 갈아엎기 (엔코더 baseline 확정 후 별도 PoC로 비교만).
- PID 게인의 최종 최적화, 모터 모델링, 슬립 보정 알고리즘(엔코더 기반 slip 검출 등).
- 엔코더 위치를 EKF의 pose 입력으로 사용 (현재 정책 유지: **open-loop/적분 위치를 EKF pose에 넣지 않는다**, twist만 입력).
- vendor 펌웨어 경로에서 엔코더 얻기 (불가, 위 배경).

## 설계 결정 / 열린 질문
| 항목 | 현재 결정 | 열린 질문 |
|---|---|---|
| 호스트 경로 | **결정(2026-10-10, 사용자): RRC — `base_node`가 FUNC 0x21을 읽어 `wheel_twist` 생성**(`wheel_twist_source: command/encoder/auto`, 기본 command). micro-ROS는 RRC 엔코더 odom·Before/After가 끝난 뒤 **같은 조건 측정 비교**(지연·지터, 메시지 손실, 연결 끊김 시 정지 시간, 재연결, 메모리, Nav2 오차) 후 수치로 나을 때만 전환 | — |
| FK 중복 | C++ `jetrover_base/mecanum.hpp`(단위시험 있음)와 Python `rrc_bridge.py`(별도 시험)에 각각 존재 | 한쪽으로 통합하거나, 같은 입력에서 두 구현이 같은 값을 내는지 교차검증 시험 추가. (수식 부호 규약은 vx/vy는 일치함을 대수적으로 확인, wz 항은 시험으로 확인 필요) |
| 두 백엔드 동시 사용 | 불가(같은 시리얼 포트) | 전환 절차를 launch/문서에 명시 |
| EKF wz | **자이로 yaw rate만 사용 — 유지 확정**(2026-10-10 E4: 360° × 5회에서 자이로 +0.5 ± 0.4°, 엔코더 −7.4 ± 0.6°) | — |
| 공분산 | `[0.02,0.02,0.05]` 미검증 | 직진/옆이동/회전 시험의 오차 분산에서 산출 |
| 엔코더 상수 | **3,996 ticks/rev 실측**(2026-10-10, 30초 10바퀴+10°, 이전 1320 추정 폐기) | 유효 바퀴 지름(현재 0.097 m)은 1 m 이상 반복 주행으로 확정 |
| 부호 | **확정**(2026-10-10): M2 PWM 짝 교체 후 4개 모두 +1, 부호 가드 추가(troubleshooting/036) | — |

## 제약 / 안전
- AGENTS.md 안전 규칙 전부: flash는 승인 후(원본 전체 백업 완료 상태 확인), 모터 시험은 바퀴 띄우고 전원 스위치 옆에서, 정지 `finally`.
- STM32 hang 재발 가능성 계속 감시(`troubleshooting/001`). 새 펌웨어 hang은 별도 기록.
- 기존 동작(vendor 펌웨어 + `jetrover_base`)을 깨지 않는다: 새 경로는 launch 인자로 선택, 기본값은 현재 경로 유지.

## 완료 기준
1. E1~E3(시험 계획)을 통과해 엔코더 부호/ticks/rps 오차가 수치로 문서화됨.
2. `wheel_twist`가 측정 rps로 만들어지고 EKF가 이를 사용, 직진 1 m·회전 360° 시험에서 open-loop 대비 오차 개선이 수치로 기록됨.
3. Nav2 baseline 15회를 `encoder_ekf` 태그로 재시험, `baseline_openloop`과의 비교표가 `docs/benchmarks/navigation/`에 있음.
4. 모든 체크리스트 항목은 실제 로봇에서 검증된 것만 `[x]`.
