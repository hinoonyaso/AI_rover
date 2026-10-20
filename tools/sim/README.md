# tools/sim — Gazebo 주행 시나리오 (host)

실기 배터리를 쓰지 않고 컨트롤러를 비교하는 시나리오. Gazebo 실행 준비는 `src/jetrover_gazebo/README.md` 1~5절
(특히 **5절 depth 기준 촬영** — 상자 높이 10 cm는 LiDAR에 안 보여서 `depth_obstacles:=true`가 필요).

## 시나리오 (`run_scenarios.sh`, 좌표 = 지도 = Gazebo 월드)
| ID | 시작 → 목표 | 무엇을 보나 | 실기 대응 |
|---|---|---|---|
| S1 | (0.55, 0.40, 90°) → (0.55, 1.40), 장애물 없음 | 직진 흔들림(vy 전환, 옆 이탈, 몸 방향 오차) | troubleshooting/031 |
| S2 | A (1.02, 0.37) ↔ B (1.00, 1.45) 왕복, 상자 중심 (1.21, 1.00) | 상자 회피 성공률, 우회 폭, 정면 유지 | 034 F2 시리즈 |
| S3 | (0.47, 0.52, −100°) → (1.00, 0.27) | 목표가 몸 기준 왼쪽 약 75°: 옆이동 대신 회전으로 빠져나오는가 | 034 F2-4 정체 지점 |

## 비교 매트릭스 (컨트롤러마다 Nav2를 다시 띄움)
```bash
export ROS_DOMAIN_ID=31
ros2 launch jetrover_gazebo sim.launch.py depth_obstacles:=true            # 터미널 1 (상자 월드)
tools/nav/ab_params/make_variants.sh                                        # 1회: 변형 파라미터 생성
# 터미널 2: 아래 셋 중 하나
ros2 launch jetrover_navigation nav2.launch.py use_sim_time:=true                                    # dwb (기본)
ros2 launch jetrover_navigation nav2.launch.py use_sim_time:=true \
  params_file:=$HOME/jetrover_ws/tools/nav/ab_params/nav2_params_mppi.yaml                          # mppi
ros2 launch jetrover_navigation nav2.launch.py use_sim_time:=true \
  params_file:=$HOME/jetrover_ws/tools/nav/ab_params/nav2_params_mppi_nolr.yaml                     # mppi_nolr
# 터미널 3
tools/sim/run_scenarios.sh <dwb|mppi|mppi_nolr> all 3      # S1 3회, S2 왕복 3회, S3 3회 (약 15분)
```
결과: `Log/wobble_trials_v3.csv`(태그 `SIM_<ctrl>_<S..>`), bag `bags/wobble/SIM_*`, 끝에 요약 표.

## 판정 기준
| 비교 | 기준 |
|---|---|
| LateralRatioCritic 효과 (mppi vs mppi_nolr) | mppi의 `diag50_frac` < 0.05(S2), S3에서 성공(회전 후 진행) — nolr는 F2-4처럼 정체하거나 diag50이 큼 |
| DWB vs MPPI 공정 비교 | 같은 S1/S2: 성공률, 평균 시간, 최대 옆 이탈, `yaw_dev_max`, vy 전환/분 |
| 실기 F2와의 차이 | S2 mppi 결과가 실기 F2(성공 3/4, 우회 15~18 cm)와 크게 다르면 마찰/센서 모델부터 의심 |

참고(2026-10-10, 실기 bag 재계산): `diag50_frac` — F2-2 0.000, F2-3 0.010, M8 0.010, **F2-4(정체) 0.401**.

## 주의
- 순간이동(`gz service .../set_pose`) 직후 AMCL에 `/initialpose`를 준다. EKF odom은 이어지므로 map→odom이 한 번 크게 바뀌는 건 정상.
- `straight_trial.py`의 시간 초과는 벽시계 기준(여기선 90 s). host가 실시간보다 느리면(`gz` 창의 RTF < 0.8) `--timeout`을 늘린다.

## 팔: 큐브 집기 시험 (`sim_pick_check.sh`, 2026-10-14)
월드 `room_lap2_objects.sdf`(src/jetrover_gazebo/README.md 3절), 로봇은 팔 시험 자리 (0.45, 0.75, 90°)에 스폰.
```bash
tools/sim/sim_pick_check.sh                 # red green blue 각각 새 시뮬레이션에서: 열기 → 큐브 위 15/6 cm → 큐브 높이 → 닫기 → 들어 올림
tools/sim/sim_pick_check.sh green           # 하나만
python3 tools/sim/arm_ik.py /tmp/sim.urdf 0.25 0 0.12 0.06 0.025   # IK만(base_footprint 기준 목표, 그리퍼 아래 방향)
```
판정: 들어 올린 뒤 큐브 z > 0.06 m. 2026-10-14: 3/3 LIFTED(z 0.127~0.128 m), 닫을 때 r_joint 명령 0.30 → 상태 0.336~0.345
(큐브에 막힘 = 접촉). 시뮬레이션 그리퍼: r_joint 클수록 열림(+1.2 ≈ 손가락 간격 6.4 cm, +0.35 ≈ 3 cm).
주의: 실기 서보 데드밴드·백래시·접촉 판정 로직(GraspStateMachine)은 없다 — 관절 위치 명령만으로 집는 시험.
S1(x 0.55 직진)은 상자 월드용 — `room_lap2_objects.sdf`에서는 큐브(0.37~0.53, 1.00)가 경로 옆에 있다.

## 회피 주행 정밀도 시험 (2026-10-20, 체크리스트 8.15, 결과 `docs/benchmarks/sim/avoidance_precision_20261020.md`)
host에서 Gazebo(`depth_obstacles:=true`) + Nav2(`auto_localize:=false`) + 정답 위치 노드 + 정밀 접근 노드를 `sim_avoid_run.sh`가 한 번에 띄우고 시험한다.
```bash
# 한 시나리오 (S1|S2|S4|all), 왕복 n회
TAG=t SCEN=S4 REPEATS=10 APPROACH=1 CTRL=dwb PARAMS=tools/nav/ab_params/nav2_params_sim_avoid.yaml bash tools/sim/sim_avoid_run.sh
# 변형 여러 개를 연속으로 (변형 a = tools/nav/ab_params/nav2_params_a.yaml)
VARIANTS="a b" SCENS="S4 S2" REPEATS=6 bash tools/sim/run_variants.sh > /tmp/log 2>&1
python3 tools/sim/avoid_trials.py summary --tag t
```
- 환경: `RUNCMD`(시험 대신 다른 명령, 예 진단 도구), `GTLOC=0`(AMCL 사용), `GUI=true`, `LOGDIR`.
- 결과: `Log/sim_avoid_trials*.csv`, 시행별 `Log/sim_avoid/*.json`. 성공 = Nav2 성공 + 최소 간격 > 0 + 상자 이동 < 2 cm.
- 지표 정의 `avoid_metrics.py`(단위시험 `python3 -m pytest tools/sim/test_avoid_metrics.py`), 시나리오 좌표는 `avoid_trials.py`의 `SCENARIOS`(위 S2/S4와 다름: A (1.02, 0.30) ↔ B (1.00, 1.25), 상자 (1.21, 0.78) / (1.00, 0.78)).
- 진단: `costmap_snapshot.py`(코스트맵 그림, `--at` 초 / `--near-box` m), `dwb_eval_probe.py`(DWB 평가자 점수), `corridor_width.py`, `costmap_probe.py`, `depth_fp_survey.py`, `check_depth_obstacles.py`, `plant_response.py`.
- 주의: 순간이동 뒤 costmap을 비운다(troubleshooting/049). host 시험 스크립트·로그를 `/tmp`에 두면 재부팅에 사라진다.

