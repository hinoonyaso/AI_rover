# nav2_params.yaml 튜닝 이력 (+ MPPI, 관련 perception/base 파라미터)

`src/jetrover_navigation/config/nav2_params.yaml`의 주석에 쌓인 "왜 이 값인가" 기록을 파라미터별로 모은 문서.
**이 값들은 정량 baseline이 아니라 소수 시행(1~3회)에서 나온 경험적 선택이다.** 실제 성능은 `prd/nav2-baseline-test-plan.md`의 15회 시험으로 확정한다.
(설정 파일의 긴 주석을 "짧은 이유 + 이 문서 링크"로 줄이는 작업은 설정 파일 수정이라 별도 승인 후 진행한다. 지금은 이력만 이쪽에 보존.)

| 파라미터 | 변경 | 날짜 | 이유 / 근거 | 관련 |
|---|---|---|---|---|
| `inflation_radius` | 0.3 → (0.15 시도, 내접 반경 경고로 거부) → 0.2 → **0.3** | 2026-10-05 | 0.3은 작은 방에서 "Start occupied". 0.15는 내접 반경(0.17)보다 작아 Nav2가 경고(비용 계산 전제 위반). 이후 플래너용 footprint를 0.40×0.48로 키우자 내접 반경 0.24가 되어 0.2도 오류 → 0.3 | troubleshooting/020 |
| `xy_goal_tolerance` | 0.1 → 0.2 → **0.15** | 2026-10-05 | 0.1은 목표 0.15 m 앞에서 "Failed to make progress"(80초+recovery 7회), 0.2는 도착점이 어긋남. 목표 근처 DWB가 모터 데드존(펌웨어 PWM ±250) 아래 속도를 낸다고 **추정**(미검증) | 028 |
| `yaw_goal_tolerance` | 0.25 → 0.5 → **0.4** | 2026-10-05 | 0.25는 미세조정 장시간, 0.5는 우회 후 20° 틀어진 채 종료 | 028 |
| `min_speed_xy` | 0.0 → **0.05** | 2026-10-05 | 모터 데드존 아래 속도 샘플 방지 (추정) | 028 |
| `max_vel_x` | 0.2 → **0.12** | 2026-10-05 | depth 감지 거리 약 0.5 m라 0.2 m/s에서는 옆으로 비킬 시간 부족 → 상자를 침 | 028 |
| `min_vel_x` | -0.2 → **0.0** | 2026-10-05 | 후방이 LiDAR·depth 모두 사각이라 후진 중 물체를 밀었다 | 022 |
| `behavior_plugins` | [spin, backup, wait] → **[spin, wait]** (+ 기본 BT XML에서 `<BackUp/>` 제거) | 2026-10-05 | BackUp recovery는 `min_vel_x`와 무관하게 후진 `cmd_vel`을 직접 낸다. 기본 BT가 backup 서버에 로드 시점에 연결하므로 BT에서도 같이 제거해야 bt_navigator가 기동 | 022 |
| `BaseObstacle.scale` | 0.02 → **0.1** | 2026-10-05 | 장애물 옆을 아슬아슬하게 지나가 상자를 침 | 028 |
| 가속 한계(DWB, velocity_smoother) | [1.0,1.0,2.0] → **[0.5,0.5,1.0]** | 2026-10-05 | 회피 동작이 "요란" | 028 |
| BT `RemovePassedGoals` radius / 재계산 주기 | 0.7 → **0.12** / 3 s → **1 Hz** | 2026-10-05~06 | 0.3 m 간격 웨이포인트가 즉시 삭제되어 직선 복귀 실패(대각선 종료) | 028, `tools/nav/line_goal.py` |
| global costmap `depth_cloud` | 없음 → **추가** (3 m) | 2026-10-05 | depth가 local에만 있으면 전역 경로가 장애물을 통과, DWB가 앞에서 멈춤 | 026 |
| collision_monitor polygon | 확대 footprint → **실제 크기 + 2~3 cm 여유** `[[0.19,0.21],…]` | 2026-10-05 | 플래너용 확대 footprint(0.40×0.48)를 쓰면 상자(+연장점)가 "안"으로 판정되어 감속/정지 | 028 |
| collision_monitor 소스 | LiDAR만 → **+depth_cloud** (min_height 작게) | 2026-10-05 | 상자가 LiDAR에 안 보여 안전망이 작동한 적이 없었다 | 028 |
| `sparse_point_cloud` `extrude_depth_m` | 0 → **0.3** | 2026-10-05 | 카메라가 앞면만 봐서 몸통이 free로 보임 (휴리스틱) | design/depth-obstacle.md |
| `background_margin_mm` | **60** | 2026-10-05 | depth 노이즈보다 큰 여유 (기준 depth 비교, 30 mm에서 상향) | 023 |
| 홈 자세 `arm_home_pose_rad` | → [0.0, -0.553, 1.688, 1.671, 0.017] | 2026-10-05 | 카메라가 자기 바퀴부터 바닥까지 끊김 없이 보이도록 | checklist 14 |


## 2026-10-06 (커밋 7db53d6, 상자 회피 튜닝) — 이 문서에 늦게 추가
| 파라미터 | 변경 | 이유 / 근거 | 관련 |
|---|---|---|---|
| footprint (global/local) | 0.40×0.48 → **0.36×0.50** | 좁은 방에서 상자 주변 통과 불가 영역이 커서 우회 대신 정지. **실측 아님**(2026-10-09에 과대로 판명) | 028 |
| `inflation_radius` | 0.3 → 0.25 → **0.40** | 상자를 여유 0으로 스치는 경로를 밀어내려고 | 028 |
| `cost_scaling_factor` | 3 → **5** | 위와 같음 | 028 |
| planner `cost_travel_multiplier` | 2 → **4** | 비용 높은 곳을 더 피하게 | 028 |
| `max_vel_theta` (DWB) / smoother wz | 1.0 → **0.4** | 회전 섞으면 모서리가 크게 휩쓸려 안전망/DWB가 정지 | 028 |
| `GoalAlign.scale` / `RotateToGoal.scale` | 24 → **4** / 32 → **8** | 회전을 덜 선호, 메카넘 평행이동 위주 | 028 |
| local `scan.clearing` | true → **false** | LiDAR가 낮은 상자를 지움(→ 2026-10-07 레이어 분리로 대체) | 028, 031 |
| progress checker | 0.3 m/10 s → **0.15 m/20 s** | 느린 곡선 우회가 진행 실패로 중단 | 028 |
| collision_monitor | FootprintApproach → **FootprintStop [[0.17,0.195]…] + FootprintSlow [[0.26,0.28]…] 50%** | approach가 상자 옆 정상 비킴까지 0으로 만듦 | 028 |
| BT XML | ClearingActions·Spin 제거, local clear → Wait | recovery가 상자 기억을 지움 | 028 |
| `extrude_depth_m` (sparse_point_cloud) | 0.3 → **0.15** | 좁은 방에서 연장 영역이 통로를 막음 | 028 |
| `arm_home_pose_rad` | → **[0.0042, -0.6618, 1.6629, 1.6043, 0.0168, -0.0209]** | 손목을 들어 앞 18~51 cm 연속 감지 | 028 |

## 2026-10-07 ~ 10-09 (실기 직진/회피 시험) — troubleshooting 031·034
**DWB / 컨트롤러**
| 파라미터 | 변경 (중간 시도 포함) | 날짜 | 이유 / 근거 |
|---|---|---|---|
| `trajectory_generator_name` | Standard → **LimitedAccelGenerator** (+`sim_period` 0.1) | 10-07 | Standard는 매 주기 vy 전 범위 샘플(sim_time을 가속 시간으로 씀) → 좌우 뒤집힘. A/B 6+6회: 직진 중 몸 방향 오차 중앙값 4.5° vs 29° (10-09) |
| `vy_samples` | 10 → **11** | 10-07 | 현재 vy 기준 대칭 격자 |
| `min_speed_xy` | 0.05 → 0.0 → **0.04** | 10-07 | 0.05는 `min_speed_theta` 0이라 원래 무효(소스 확인). 0.04 + theta와 함께 데드존 가드 |
| `min_speed_theta` | 0.0 → 0.2 → **0.1** | 10-07 | 목표 앞 0.006 m/s 선택·A 끝 출발 실패 대책. 0.2는 LimitedAccel 정지 상태에서 회전 후보 0개(회전 4/4 실패) |
| DWB `xy_goal_tolerance` | (미설정=0.25) → **0.12** | 10-07 | RotateToGoal 자체 허용오차 0.25 > goal checker 0.15 → 목표 15~25 cm 앞에서 정지 |
| `acc_lim_theta` / `decel_lim_theta` | 1.0 / -1.0 → **3.0 / -3.0** | 10-09 | shim이 0.36 rad/s로 넘길 때 LimitedAccel 창(±0.1)으로는 회전을 못 멈춰 ±30° 지그재그. 실제 각가속은 smoother 1.0 유지 |
| critics `Twirling` | 없음 → **scale 10** | 10-09 | DWB가 주행 중 PathAlign 때문에 몸을 돌림 → 방향 유지, 옆 보정은 vy |
| `BaseObstacle.scale` | 0.1 유지 (직진 시험 전용 파일에서만 0.02) | 10-07~09 | 0.1에서 멈춘 원인은 허용오차·데드존이었음 → 기본 0.1로 직진 3/3 |
| `FollowPath.plugin` | DWB → **RotationShimController**(primary DWB) | 10-07 | 출발 시 15~20° 틀어진 채 vy로 따라가 대각선 주행·정면 카메라 사각 |
| shim `angular_dist_threshold` / `disengage` | 0.26/0.09 (15°/5°) → 0.6/0.2 (35°/11°) → **1.05/0.2 (60°/11°)** | 10-07~09 | 회피 중 shim이 제어권을 놓지 않음(데드존 아래 회전으로 5° 못 맞춤) → 35°; 사용자 요구(회전은 큰 방향 전환에서만) → 60° |
| shim `rotate_to_heading_once` | false → true → **false** | 10-09 | 회피 경로 재계획마다 반복 회전 → true; 코너 회전 필요 + 60°/0.6 m로 회피 꺾임 무시 → false |
| shim `forward_sampling_distance` | 0.3 → **0.6** | 10-09 | 장애물 옆 작은 꺾임이 아닌 경로 전체 방향 |
| shim 기타 | `rotate_to_heading_angular_vel` 0.4, `max_angular_accel` 1.0, `simulate_ahead_time` 1.0, `rotate_to_goal_heading` true, `use_path_orientations` false | 10-07 | DWB 한계와 동일, 최종 yaw도 shim |

**Costmap / Planner**
| 파라미터 | 변경 | 날짜 | 이유 / 근거 |
|---|---|---|---|
| local costmap 레이어 | obstacle(scan+depth) → **obstacle_layer(scan, clearing true) + depth_layer(depth)** | 10-07 | scan clearing false로 LiDAR 점이 영원히 쌓여 통로 막힘(lethal 84→17칸) |
| global costmap 레이어 | 같은 분리 | 10-09 | LiDAR가 depth 상자를 지워 전역 경로가 상자 관통 |
| footprint (global/local) | 0.36×0.50 → **0.38×0.28** | 10-09 | 줄자 실측 36×26 cm + 1 cm (이전 값은 미실측 과대) |
| `inflation_radius` | 0.40 → **0.25** | 10-09 | 실측 footprint(내접 0.14)에서 0.40 비용 띠가 우회를 ~40 cm로 밀어냄. **주행 확인 전** |
| `cost_scaling_factor` | 5 → **10** | 10-09 | 비용이 빨리 줄어 장애물에 가깝게 (우회 41→36.5 cm) |
| planner `cost_travel_multiplier` | 4 → **2** | 10-09 | 위와 같음 |
| collision_monitor `FootprintStop` | [[0.17,0.195]…] → **[[0.20,0.15]…]** | 10-09 | 실측 몸 + 약 2 cm |
| collision_monitor `FootprintSlow` | [[0.26,0.28]…] → **[[0.28,0.22]…]** | 10-09 | 실측 몸 + 약 10 cm |
| collision_monitor `visualize` | false → **true** | 10-07 | RViz 확인용 |

**MPPI (`config/mppi_followpath.yaml`, 신규 2026-10-09, Nav2 Jazzy 예제 기반)**
| 파라미터 | 값 | 비고 |
|---|---|---|
| `motion_model` / `time_steps` / `model_dt` / `batch_size` | Omni / 40 / 0.1 / **1000** | batch는 예제 2000의 절반(Orin Nano CPU) — 주기 경고 0회 |
| `vx_max` / `vx_min` / `vy_max` / `wz_max` | 0.12 / **0.0** / 0.12 / 0.4 | 후진 금지 유지 |
| `ax_max` / `ax_min` / `ay_max` / `az_max` | 0.5 / -0.5 / 0.5 / 1.0 | DWB·smoother와 동일 |
| `wz_std` | 0.4 → **0.2** (10-09) | 회피 중 회전 억제 |
| `TwirlingCritic` | 10 → **30** (10-09) | 정면 유지 + 대각 회피(사용자 요구). **주행 확인 전** |
| `VelocityDeadbandCritic` | [0.04, 0.04, 0.1], weight 35 | 모터 데드존 |
| `CostCritic` | weight 3.81, critical 300, footprint 고려, collision 1e6 | 예제값 |
| `PathAngleCritic` | mode 0, max_angle 1.0 rad | 경로 방향 바라보기(57° 넘을 때만) |

**2026-10-09 밤 (회피 M6 → M7)**
| 파라미터 | 변경 | 이유 |
|---|---|---|
| shim `angular_dist_threshold` | 1.05 (60°) → **1.4 (80°)** | M6: 목표 20 cm 앞, 옆 25 cm 치우친 상태에서 목표점 방향이 60°를 넘어 제자리 −60° 회전 |
| MPPI `PathAngleCritic` | 켬 → **끔** (critics 목록에서 제거) | M6: Twirling 30에도 회피 중 몸이 +31°까지 돌아감. 큰 방향 전환은 shim 담당 |
| MPPI `VelocityDeadbandCritic` wz | 0.1 → **0** | M7: PathAngle 끈 뒤에도 회전 0.12~0.16 rad/s 지속(+38°) — |wz|<0.1 벌점이 '0' 대신 '0.1 이상 회전'을 고르게 함 |
| MPPI `threshold_to_consider` | Goal 1.0→**0.35**, GoalAngle 0.5→**0.3**, PathAlign 0.5→**0.3**, PathFollow 1.0→**0.35** | 반복 R2: 1.1 m 시험 구간에서 출발 10~20 cm 뒤 '목표 직행' 모드로 바뀌어 상자 앞에 갇힘(전역 경로는 +18 cm 우회였음). 적용 후 왕복 3/4 성공, 옆 이동 15~18 cm |

**2026-10-09 밤 (메카넘 대각 45° 제한, `prd/mppi-lateral-ratio-critic.md`)**
| 파라미터 | 변경 | 이유 |
|---|---|---|
| MPPI critics | + **LateralRatioCritic**(신규 플러그인 `jetrover_nav_plugins`): max_angle 45°, slack 0.02 m/s, weight 50 | 회피가 vy 0.02~0.06의 완만한 흐름이라 메카넘 활용 부족. 정면 카메라 시야 때문에 45° 이내로 제한(사용자 A안) |
| MPPI `PathAlignCritic.cost_weight` | 14 → **6** | 경로를 느슨하게 따라 장애물 근처에서 45° 이내 옆이동을 직접 고르게 |
| MPPI `PathFollowCritic.cost_weight` | 5 → **3** | 위와 같음 |

**기타**
| 파라미터 | 변경 | 날짜 | 이유 |
|---|---|---|---|
| `arm_home_pose_rad` joint4 | 1.6043 → **1.45** | 10-09 | depth 바닥 시야 0.21~0.62 → 0.26~0.81 m (`benchmarks/perception/home_pose_20261009.md`) |
| `sparse_point_cloud` 홈 자세 게이트 | 신규: tol 0.04 → **0.08 rad**, debounce **1 s**, joint_states timeout 2 s | 10-07 | 0.04는 주행 중 백래시로 열림/닫힘 반복 |
| `motor_stop_frame_on_stop` (base_node) | 신규 true → **false** | 10-08 | 정지 프레임이 바닥 울림을 못 멈춤(032) |
| `scan_match_init` 확신 기준 | score ≥ 0.8 & margin ≥ 0.1, **또는 score ≥ 0.95 & margin ≥ 0.05** | 10-08 | 0.974/0.883이 거부돼서 |
| AMCL (`amcl.yaml`) | 변경 없음 | — | — |
| `wheel_twist_source` (base_node, 신규) | 기본 **command**(이전 동작), 시험 시 encoder | 10-10 | 자체 펌웨어 FUNC 0x21 엔코더 odom(RRC 경로 결정) |
| `wheel_twist_covariance_encoder` (base_node, 신규) | 엔코더 twist 분산 **[1e-4, 2e-4, 1e-3]**(명령값 모드는 0.05/0.05/0.1 유지) | 10-10 | E5: 바닥 vx 순간 표준편차 0.004 m/s, 1 m 치우침 < 0.5 % → 여유 두고 0.01/0.014 m/s. 이전엔 엔코더도 0.05(= 0.22 m/s, 최고속보다 큼) |
| `gyro_bias` (base_node) | [0.197, 0.168, −0.017] → **[0.2075, 0.1660, −0.0162]** rad/s | 10-10 | 자체 펌웨어(rrc_m4) 기준 재측정(30 s 정지). 이전 z는 +0.049°/s 남겨 E5 사각형 42 s에 EKF 방향 +2.1° 드리프트. **vendor 펌웨어로 되돌리면 이전 값** |
| `wheelbase` / `track_width` (base_node) | 0.216 / 0.195 → **0.2120 / 0.1914** (×0.9815) | 10-10 | E4 회전 360°×5: 실제 366.1°(명령 대비 0.9833), 엔코더 358.7°(0.9797) → 회전 팔 길이 약 2 % 과대. 직진·옆이동 무관. **baseline 비교 시 Before/After 모두 같은 값** |

## 해석 시 주의
- 위 표의 이유 중 **"추정"** 표시는 실제로 검증되지 않았다 (특히 모터 데드존 가설).
- 값들은 서로 얽혀 있다(속도 ↔ 감지 거리 ↔ inflation ↔ footprint ↔ collision_monitor). 하나를 바꾸면 baseline이 무효가 되므로, baseline 시험 중에는 변경하지 않는다.
- 엔코더 odom 적용 후에는 목표 근처 정지 문제(데드존 가설)가 달라질 수 있어 `xy/yaw_goal_tolerance`를 다시 평가해야 한다.
