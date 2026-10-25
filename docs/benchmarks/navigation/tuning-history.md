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
| `wheel_twist_source` (base_node) | **command → auto** (launch 인자 기본값·`base.yaml`·노드 기본값) | 10-11 | 엔코더 odom이 개루프에서 더 정확(E4 직진 0.68 → 0.24 cm/m, E5 왕복 0.1~0.4 cm)하고 Nav2 E6 v2 30회에서 차이 없음(성공 6/15 대 5/15) → 비용 없음. auto는 FUNC 0x21 피드백이 끊기면 명령값으로 폴백하고 전환을 로그로 남김. 실기 확인: 구동 시 공분산 0.0001(엔코더), 피드백 유효 시간을 0.0001 s로 줘 끊김을 흉내 내면 0.05(명령값)·경고 로그. 되돌리려면 `wheel_twist_source:=command` |
| MPPI `VelocityDeadbandCritic` (시험 변형만, 기본값 아님) | 켬 → **끔**(`nav2_params_mppi_nodb.yaml`, `make_variants.sh`) | 10-11 | 자체 펌웨어에서 0.02 m/s도 추종(데드존 소멸) + 상자 앞 망설임 의심. 상자 B 1회: 32 s·회전-직진-회전 그대로 → **가설 지지 못함, 채택 안 함**. 기본 `mppi_followpath.yaml`은 그대로 |
| 컨트롤러 기본값 | **DWB 유지**(MPPI 전환 안 함) | 10-11 | A/B 15회씩: 직선 MPPI 우세, 정면 상자·대각 회전 DWB 우세(`dwb_vs_mppi_20261011.md`). 다음 단일 실험은 goal 허용 오차 0.15 대 0.10 |
| `arm_poll_hz` (base_node) | 5.0 → **20.0** (코드 기본값·`base.yaml`, 실행 중 변경 가능) | 10-11 | T1 폴링 벤치마크(`docs/benchmarks/arm_poll_bench_20261011.md`): 읽기 전용에서 IMU·루프 불변, 프레임 유실 0, 서보 응답률이 5 Hz와 같음. 팔이 움직일 때는 T7에서 확인, 문제면 5~12 Hz |
| goal 허용 오차 (**기본값 적용 10-11**, 되돌리기 `tools/nav/ab_params/nav2_params_tol015.yaml`) | `general_goal_checker.xy_goal_tolerance` 0.15 → **0.10**, `FollowPath.xy_goal_tolerance` 0.12 → **0.08** | 10-11 | 자체 펌웨어에서 모터 데드존 소멸(0.02 m/s 추종). D·C 각 5회: 위치 오차 약 3.5 cm 개선, 10 cm 안 9/10(0.15는 2/10), 정체·진동 없음. 외부 리뷰의 조건부 승인(줄자 독립 확인 3~5회·시험 순서 효과 확인은 남음) |
| (**sim 시험용 변형만, 실기 불변**) `inflation_radius` | 0.25 → **0.30** (global/local) | 2026-10-20 | 0.25는 내접 반경(0.13+여유)과 거의 같아 비용 구배가 없었음. 0.33~0.40은 S2 간격 10~17 cm지만 S4 멈춤 증가 → 0.30 채택. 변형 `nav2_params_sim_avoid.yaml` | troubleshooting/050, `docs/benchmarks/sim/avoidance_precision_20261020.md` |
| (sim 변형) `footprint_padding` | **+0.05** (여유 8~16 cm는 시도 후 폐기) | 2026-10-20 | 7·8 cm도 S4 간격 4~5 cm로 같고 통로만 좁아짐 | 위와 같음 |
| (sim 변형) `depth_cloud.clearing` | true → **false** (global/local) | 2026-10-20 | 레이캐스트가 상자 옆을 지날 때 상자 칸을 지움(코스트맵 스냅샷 확인) | troubleshooting/050 |
| (sim 변형) `BaseObstacle.scale` | 0.1 → **0.05** | 2026-10-20 | S4에서 이동 후보가 상자 쪽 비용으로 회전 후보보다 불리해 제자리 회전에 갇힘 | troubleshooting/051 |
| (sim 변형) `Twirling.scale` | 10 → **30** | 2026-10-20 | 위와 함께 S4 12/12, 최종 20/20. 폐기한 것: Oscillation 평가자 제거(9/12), 팽창 0.33+Twirling 30(AB 3/6) | troubleshooting/051 |
| (sim 전용 launch) depth `min_obstacle_height` | −0.1 → **0.09**, `background_margin_mm` 100, `extrude_depth_m` 0.25 | 2026-10-19 | 바닥 요철·램프 오검출(빈 방 20/24), 상자 두께보다 짧은 압출 | troubleshooting/050 |
| (sim 변형, 2차) DWB 장애물 평가자 | BaseObstacle(scale 0.05) → **ObstacleFootprint(scale 0.05 → 0.02)** | 2026-10-21 | 간격 미달 12회 전부 몸 뒤 모서리가 복귀 구간에서 스침(중심 한 점 검사의 한계). 0.02는 B 출발 직후 느린 옆이동 완화 | troubleshooting/052 |
| (sim 변형, 2차) controller_server `failure_tolerance` | 0(기본) → **1.0** | 2026-10-21 | 한 주기 "No valid trajectories"로 FollowPath 중단 → BT 5 s 대기 반복 | troubleshooting/052 |
| (sim 변형, 2차) local costmap `resolution` / local `footprint_padding` | 0.05 → **0.025** / 0.05 → **0.03** (global 0.05 유지) | 2026-10-21 | 격자 오차로 상자 칸이 커 보여 무효 판정. 여유 0.08은 4/12(폐기), 0.02는 간격 미달 7/12(폐기) | troubleshooting/052 |
| (sim 변형, 2차) collision_monitor `FootprintSlow` | 몸 + 약 10 cm `[[0.28, 0.22],...]` → **몸 + 약 5 cm `[[0.23, 0.18],...]`** | 2026-10-21 | 감속 영역이 계획 간격을 덮어 상자 옆에서 내내 50% 속도(B 출발 7~14 s). 실기 적용 전 안전 검토 필요 | troubleshooting/052 |
| (sim 변형, 2차, 시도 후 폐기) DWB `sim_time` 1.5 → 1.0, Twirling 30 → 20·15 | — | 2026-10-21 | 각각 B 출발 지연(최대 37.8 s), 멈춤 재발(10/12·11/12) | `docs/benchmarks/sim/avoidance_precision_20261020.md` 4절 |
| (sim 변형, 최종) `depth_cloud.clearing` | false → **true** (실기와 같음) | 2026-10-21 | 몸 다각형 검사 뒤에는 켜도 S2 20/20·S4 18/20·S1 10/10, 간격 최소 5.0 cm. 끄면 움직이는 물체 잔상 | troubleshooting/050 |
| (인식, 기본값 불변) `sparse_point_cloud.publish_clearing` / `clearing_stride_factor` | 새 파라미터, 기본 **false** / 2 (sim launch만 true, `SIM_DEPTH_CLEARING`) | 2026-10-22 | 장애물 점만 보내서 지나간 장애물 흔적을 지울 광선이 없었음. 빈 바닥 점을 `depth/points_clear`로 | troubleshooting/053 |
| (sim 변형 `nav2_params_dyn_clr.yaml`) depth 레이어 관측원 `depth_clear` | 추가(marking false, clearing true, min_obstacle_height −0.2) | 2026-10-22 | 흔적 D1 80→3칸, D3 154→0칸. 남은 3칸은 카메라 바닥 시야 끝 너머 | troubleshooting/053 |
| (sim 변형 `nav2_params_sim_dyn.yaml`) BT | `navigate_to_pose_no_backup.xml` → **`navigate_to_pose_wait_obstacle.xml`**(PathLongerOnApproach: 1.1배/5 s 시도 → **1.2배/3 s**) | 2026-10-22 | 갑자기 나타난 장애물 앞에서 멈추고 기다림. 1.1/5 s는 두 번 대기(9~14 s)·재출발 2.1 s | troubleshooting/054 |
| (sim 변형) collision_monitor `TallStop` | 추가: stop, `sources_names: [scan]`, 몸 + 12 cm → **앞 16 / 옆·뒤 12 cm** | 2026-10-22 | 사람에게 5~7 cm까지 붙음(D5). LiDAR에 안 보이는 낮은 상자 회피엔 영향 없음. 대가: 벽 근처 12~16 cm 안 진입 불가 | troubleshooting/054 |
| (sim 변형, 시도 후 폐기) collision_monitor `approach` 1.0 s | — | 2026-10-22 | 사람 간격 개선 없음(5.7~7.1 cm) | 벤치마크 3절 H2 |
| (sim 변형) depth 레이어 plugin | ObstacleLayer → **VoxelLayer**(origin_z 0, z_resolution 0.05, z_voxels 10) | 2026-10-22 | 2D 지우기 광선이 낮은 상자를 지워 S4 간격 6.0→3.9 cm. 3D로 회복(5.3~5.7) | troubleshooting/054 |
| (sim 변형) RotationShim `angular_dist_threshold` | 1.4 → **1.65** | 2026-10-22 | 갑자기 나타난 상자 15 cm 앞에서 다시 출발할 때 87° 제자리 회전 → 간격 3.9 cm. S2/S4 회귀 없음 | troubleshooting/054 |
| (실기 시험 변형 `nav2_params_real_test.yaml`) collision_monitor | `TallStop`(사방 12·앞 16 cm) → **`DirStop`** velocity polygon(holonomic, 앞으로: 앞 16·옆 6 cm, 옆으로: 그쪽 12 cm, 나머지 2 cm; 앞 영역 옆 +2 cm 시도 후 +6) | 2026-10-25 | `TallStop`은 sim 좁은 통로 0/6·실기 B 녹화에서 벽 옆 정지 위험. `DirStop` 통로 6/6, D5 사람 간격 평균 7.3(+2) → 9.0 cm(+6). 공식 설정은 그대로 | troubleshooting/054 6절 |
| (인식 launch, 기본값 불변) `camera.launch.py` 인자 `depth_publish_clearing`(false) / `depth_extrude_m`(0.15) | 새 인자 | 2026-10-25 | 실기 시험에서 `true` / `0.25`로 sim과 같은 조건 | `prd/real-avoidance-test-procedure.md` |
| (실기 시험 변형 `nav2_params_real_test.yaml`) depth_cloud `min_obstacle_height` | −0.1 → **0.06** (두 코스트맵) | 2026-10-25 | 실기 B02: 카메라 바닥 시야 끝 바닥 오검출(높이 최대 5 cm)이 상자 옆을 막아 68 cm 우회. 이후 B03~05 우회 42~47 cm. 공식 설정은 그대로 | troubleshooting/055 |
| **공식 `nav2_params.yaml` 반영 (2026-10-25, 사용자 승인)** — 실기 시험 통과 설정 중 회피·안전 | `inflation_radius` 0.25→**0.30**, footprint_padding global **+0.05** / local **+0.03**, local `resolution` 0.05→**0.025**, DWB `BaseObstacle`(0.1)→**`ObstacleFootprint`(0.02)**, `Twirling.scale` 10→**30**, `failure_tolerance` 0→**1.0**, RotationShim `angular_dist_threshold` 1.4→**1.65**, BT `navigate_to_pose_no_backup.xml`→**`navigate_to_pose_wait_obstacle.xml`**, collision_monitor `FootprintSlow` 몸+10→**몸+5 cm**·**`DirStop`** 추가, depth 레이어 ObstacleLayer→**VoxelLayer** + **`depth_clear`** 관측원, depth `min_obstacle_height` −0.1→**0.06** | 2026-10-25 | 실기 B 5/5·사람 가로지르기 5회 접촉 0(`docs/benchmarks/navigation/real_avoid_20261025.md`), sim 8.15/8.16. **목표 허용 오차 0.10/0.08은 유지**(정밀 접근이 미션/BT에 붙기 전까지). 카메라 launch 기본값도 `depth_publish_clearing` false→**true**, `depth_extrude_m` 0.15→**0.25**. sim launch의 depth 최소 높이 치환은 0.06도 0.09로 | troubleshooting/050~055 |
| `precise_approach` `relocalize` (새 파라미터) | **true**(기본), `relocalize_radius_m` 0.3, `relocalize_timeout_s` 60. sim 실행기는 false | 2026-10-25 | AMCL이 이동을 5~7 % 짧게 잡아 실제로 8~9 cm 지나침 → 접근 전 스캔 매칭 재위치로 −3~+1 cm(실기 4회 줄자) | troubleshooting/055 |
| (sim·실기 시험 변형) Smac `GridBased.tolerance` | 0.25 → **0.05** 시험 | 2026-10-25 | 0.25는 근거 기록 없음. 목표 근처가 막히면 0.25 m 안 빈 곳까지만 경로를 만들어 목표 30 cm 앞에서 성공(실기 D09, sim D7). 0.05: sim D7 6/6 목표 도착, 회귀 없음. 실기 확인 후 공식 반영 결정 | troubleshooting/055 |
| (sim·실기 시험 변형) depth 레이어 입력 | `/depth_cam/depth/points_sparse` → **`points_low`**(`depth_scan_filter.py`: LiDAR 점 10 cm 안 depth 점 제거) | 2026-10-25 | 사람이 비킨 뒤 다리 depth 흔적(카메라 바닥 광선보다 높은 3D 칸)이 안 지워져 20~25 s 기어감. sim D7 6/6·낮은 상자 회귀 없음. collision_monitor는 원래 점 유지 | troubleshooting/055 5절 |

## 해석 시 주의
- 위 표의 이유 중 **"추정"** 표시는 실제로 검증되지 않았다 (특히 모터 데드존 가설).
- 값들은 서로 얽혀 있다(속도 ↔ 감지 거리 ↔ inflation ↔ footprint ↔ collision_monitor). 하나를 바꾸면 baseline이 무효가 되므로, baseline 시험 중에는 변경하지 않는다.
- 엔코더 odom 적용 후에는 목표 근처 정지 문제(데드존 가설)가 달라질 수 있어 `xy/yaw_goal_tolerance`를 다시 평가해야 한다.
