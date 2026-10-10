# TEST_PLAN: 엔코더 기반 wheel odometry

레벨 정의는 `AGENTS.md` 그대로. **목표치는 초안**이며 첫 측정 후 확정한다(근거 없는 합격선을 미리 박지 않는다).

| Parent Task | 레벨 | 시험 | 통과 기준(초안) |
|---|---|---|---|
| E0 호스트 변환 ✅(2026-10-06 L0) | L0/L1 | C++ `mecanum_forward` 단위시험(있음), Python `mecanum_forward` 교차검증 시험(추가 필요), 가상 `/rrc/wheel_rps` → `/wheel_twist` | 두 구현이 동일 입력에서 1e-6 이내 일치, IK→FK 왕복 복원 |
| E1 통신 (MOTOR_ENABLE=0) | L2 | flash(승인) 후 IMU/배터리/엔코더 값이 호스트에 도착, 손으로 바퀴 회전 | 엔코더 값이 바퀴를 돌릴 때 변하고 정지 시 안정. **바퀴 1회전 ticks 실측**, 모터별 부호 기록 |
| E2 바퀴 띄운 속도 응답 | L3 | 명령 rps 단계 입력(예: 0.5, 1.0, 1.5 rev/s)에서 측정 rps | 정상상태 오차·응답시간을 수치로 기록(합격선은 첫 측정 후). runaway 래치 오작동 없음 |
| E3 전체 안전 | L3 | 명령 timeout(MCU), e-stop, 엔코더 이상 감지 | 호스트 명령 중단 시 MCU가 자체 정지 (vendor 펌웨어에 없던 기능) |
| E4 바닥 직선/옆/회전 ✅(2026-10-10, `docs/benchmarks/navigation/encoder_odom_e4_20261010.md`) | L4 (0.05 m/s부터) | 직진 1 m, 옆 1 m, 제자리 360°를 open-loop odom / encoder odom / 줄자·각도기로 비교, 각 5회 | encoder odom 오차 ≤ open-loop 오차 (수치로). 회전은 현재 약 81%라는 기준선과 비교 |
| E5 EKF 통합 ✅(2026-10-10, `docs/benchmarks/navigation/encoder_odom_e5_square_20261010.md`) | L4 | EKF 출력 `odom`의 드리프트(왕복 후 원점 복귀 오차), 공분산 근거 확인 | 공분산을 E4 오차 분산에서 산출해 기록 |
| E6 Nav2 재시험 | L4 | `prd/nav2-baseline-test-plan.md`와 동일 15회, 태그 `encoder_ekf` | Before/After 표 (성공률, 충돌, goal 오차, CTE RMS, 시간, recovery). 개선이 없거나 악화되면 그 사실도 기록하고 원인 분석 |

## 비교 프로토콜 (공정성)
- 같은 지도/같은 파라미터/같은 시작·목표 좌표/같은 배터리 구간. 변경점은 **odom 소스 하나**여야 한다.
- 엔코더 도입으로 `xy_goal_tolerance` 등 다른 파라미터를 같이 바꾸면 비교가 무효 → 필요하면 별도 실험으로 분리.
- 시험 순서를 번갈아(open-loop/encoder 교차) 배터리 전압 영향을 분산시키는 것을 권장.

## 안전 메모
E1 이후 전부 사용자 사전 고지·승인. E2/E3는 바퀴를 띄운 상태, E4/E6은 주변 공간 확보. 이상 시 RST 버튼(STM32 hang 복구 경로)과 전원 스위치.
