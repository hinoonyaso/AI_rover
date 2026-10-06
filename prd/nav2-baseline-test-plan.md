# TEST_PLAN: Nav2 baseline (open-loop odom 기준점)

상위 문서: `prd/slam-nav2.md`, `prd/slam-nav2-test-plan.md`(8.9~8.11). 이 문서는 8.9/8.10을 **재현 가능한 15회 시험**으로 구체화한다.
신뢰 수준: **계획** (시험 전).

## 왜 지금 하는가
현재 localization 입력은 `cmd_vel` 적분 open-loop `wheel_twist` + IMU다. 자체 STM32 펌웨어의 엔코더가 실기 검증되면
`엔코더 rps → mecanum_forward() → 실측 wheel twist`로 바뀐다. 바꾸기 **전에** 같은 조건으로 측정해 두어야 개선량을 수치로 말할 수 있다.
같은 시험을 엔코더 적용 후 동일하게 반복한다 (태그: `baseline_openloop` → `encoder_ekf`).

## 고정 조건 (바꾸면 baseline이 무효)
- 지도: `maps/lap2_20261005`, 같은 `nav2_params.yaml`/`amcl.yaml`(시험 시작 시 git 커밋 해시를 `notes`에 기록), 같은 배터리 구간(≥11 V 권장, 10 V 미만이면 충전).
- 속도 제한은 현재 설정 그대로(`max_linear 0.2`). 시험 도중 파라미터를 고치지 않는다 — 고치면 그 시점부터 새 태그로 다시 시작.
- 시작 자세는 바닥에 테이프로 표시, 매 시험 시작 전 AMCL이 수렴했는지 확인(`/amcl_pose` 공분산).
- 팔은 home pose(`arm_home_pose_rad`), 카메라 전방 (depth 시험 전제).

## 시나리오 (3 × 5 = 15회)
| ID | 내용 | 보는 것 | 안전 메모 |
|---|---|---|---|
| A | 장애물 없는 고정 직선 경로 (약 2 m) | Localization/odom/goal tracking | 통상 |
| B | 직선 경로 위 LiDAR엔 안 보이고 depth에만 보이는 낮은 상자 1개 (매 시험 같은 위치) | depth → costmap → 재계획 → 우회, 직선 복귀(`line_goal.py`) | 상자 위치를 바닥에 표시, 충돌/접촉 시 중단 후 기록 |
| C | 좁은 공간: 과거 의자 다리 충돌 재현 상황 | 센서 융합, footprint/inflation, collision_monitor | **처음엔 장애물을 여유 있게(≥ 0.5 m 통로)** 두고 시작, 사용자가 전원 스위치 옆 |

모든 시험은 L4(바닥 주행). `AGENTS.md` 안전 규칙: 사전 고지, 주변 공간 확보, 사용자가 전원 스위치 옆, 이상 시 즉시 정지.
`record_trial.sh`는 기록만 하며 로봇을 움직이지 않는다. 목표 전송(`tools/nav/line_goal.py`/RViz)은 별도로, 사용자 승인 후에만 한다.

## 지표 (7개)
Success Rate · Collision Rate · Goal Position Error [cm] · Goal Yaw Error [deg] · CTE RMS [cm] · Completion Time [s] · Recovery Count.
- Success/Collision/Recovery는 **사람이 판정**해 `meta.json`에 적는다(bag으로 추론 불가). Collision = 접촉 발생 여부.
- Goal 오차 기준 위치는 가능하면 줄자/각도기 **실측**(`measured_final`)을 쓴다 — AMCL pose는 독립적인 정답이 아니다.
  AMCL 값만 있으면 CSV `ground_truth=amcl`로 구분된다.
- CTE는 이동 시작 직후 첫 `/plan`을 기준선으로, 이동 구간의 `/amcl_pose`와의 거리. (장애물 우회 시나리오에선 우회 자체가 CTE로 잡히므로 B/C는 A와 따로 해석.)
- CPU/GPU 사용률은 이번 baseline에서 제외.

## 열린 결정 (시험 전 사용자와 정할 것)
1. **depth off 조건(Before)**: depth 유효 효과를 "충돌 감소"로 증명하려면 depth를 끈 대조군이 필요하다. 그런데 LiDAR에 안 보이는
   낮은 상자 시나리오를 depth off로 돌리면 **충돌이 거의 확실**하다. 한다면 *부드러운 장애물(폼 블록 등)*로 바꾸고 속도를 낮추며 사용자가 전원 스위치 옆에 있을 때만.
   안 하면 Before 근거는 과거 실충돌 1건(troubleshooting/021)뿐이다. 이 경우 포트폴리오에서 "충돌 감소"가 아니라 "재현된 실패 사례 + 이후 반복 성공률"로 서술한다.
2. **목표 좌표/시작 자세**: 시나리오별 고정 좌표(map 프레임)를 시험 전에 확정해 이 문서에 표로 기록한다 (현재 미정).
3. **B/C 장애물 위치**: 지도 `lap2_20261005`의 의자 좌표(x 1.10~1.90, y −0.68~−0.18)와 겹치지 않게 정한다.

## 기록·분석
```bash
# 시험 1회: 기록 시작 → (별도 터미널에서 목표 전송) → 정지 후 Ctrl+C → meta.json 편집
tools/nav/benchmark/record_trial.sh baseline_openloop A 1 2.0 0.5 0
# 15회 후
python3 tools/nav/benchmark/analyze.py bags/baseline_openloop   # -> docs/benchmarks/navigation/baseline_openloop.{csv,md}
```
- bag은 `bags/`(gitignore, 용량 큼). CSV/MD 요약만 git에 커밋.
- 토픽 목록(`/plan`, `/received_global_plan`, `/cmd_vel_nav` 등)은 첫 시험 전에 `ros2 topic list`로 실제 이름을 확인하고 `record_trial.sh`를 맞춘다.

## 완료 기준 (checklist 8.9/8.10을 `[x]`로 바꾸는 조건)
1. 15회 전부 기록(실패/중단 포함 — 실패한 시험을 빼지 않는다), bag + meta.json 보존.
2. `analyze.py` 결과 CSV/MD가 `docs/benchmarks/navigation/`에 커밋됨.
3. 실패/충돌이 있으면 `troubleshooting/`에 기록.
4. 지표 코드(`metrics.py`)가 단위시험 통과 (`python3 tools/nav/benchmark/test_metrics.py`).

## 상태
- [x] 지표 계산 코드 + 단위시험 8개 통과 (2026-10-06, 호스트)
- [~] `analyze.py`/`record_trial.sh` 작성 — **실제 bag으로는 아직 한 번도 실행하지 않았다**(rosbag2 읽기 부분 미검증, 첫 시험 후 확인)
- [ ] 15회 시험 (사용자와 일정 조율 필요)
