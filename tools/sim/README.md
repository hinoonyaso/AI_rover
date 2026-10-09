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
