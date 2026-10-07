# 031 — Nav2 직진 중 좌우 흔들림(게걸음) / depth 기준 영상이 팔 자세에 종속 (2026-10-07)

관련: 026, 028(회피 튜닝), 027(팔 토크). 외부 분석(사용자 조사 자료)을 Nav2 Jazzy 소스와 대조해 검증한 결과.

## 증상
1. 키보드(vx만)로는 똑바로 가는데 Nav2로 가면 좌우로 흔들리거나 게걸음처럼 감.
2. depth 장애물 검출(`sparse_point_cloud`)은 홈 자세에서 찍은 기준 depth와 비교하므로, 팔이 홈 자세에서 벗어나면 바닥을 장애물로 보거나 실제 장애물을 놓칠 수 있는데 이를 막는 장치가 없었음.

## 원인
### 확정 (Jazzy 소스로 확인)
- **DWB `StandardTrajectoryGenerator`는 속도 후보를 만들 때 가속 시간으로 `sim_time`(1.5 s)을 쓴다**
  (`standard_traj_generator.cpp`: `velocity_iterator_->startNewIteration(current_velocity, sim_time_)`).
  `acc_lim_y 0.5 × 1.5 s = 0.75 m/s` 창이라 매 주기(10 Hz) **vy 전 범위 −0.2~+0.2가 후보**가 된다.
  현재 vy가 +여도 다음 주기에 −vy를 고를 수 있고, 실제 출력은 velocity_smoother(가속 0.5)가 늦게 따라가므로
  좌우가 번갈아 뒤집히는 흔들림이 생기기 쉬운 구조다. → **흔들림의 유력 원인(추정, 실기 A/B 미실시)**.
- **`min_speed_xy: 0.05`는 아무 효과가 없었다.** `kinematic_parameters.hpp isValidSpeed()`는
  `|v_xy| < min_speed_xy` **그리고** `|ω| < min_speed_theta`일 때만 후보를 버리는데 `min_speed_theta: 0.0`이면 둘째 조건이
  절대 참이 안 된다. 즉 외부 분석의 "min_speed_xy가 큰 보정을 강제한다" 가설은 **폐기**, 028의 "데드존 방지"도 실제로는 작동하지 않았음.

### 확인한 사실 (설정/문서 불일치)
- footprint 실제 값은 `±0.18 × ±0.25` = **0.36×0.50 m(내접 0.18)**. 주석의 "0.36x0.42", "내접 0.21"은 틀렸음 → 주석 정정(값은 그대로, 줄자 실측 전).
- 외부 분석의 "extrusion 0.3 m"는 옛 값. 현재 `extrude_depth_m` 기본값은 **0.15 m**(2026-10-06 변경).

### 추정 (실기 데이터 필요)
- AMCL `map→odom` 보정이 흔들림에 기여하는지: 보정 시점과 `cmd_vel_nav.linear.y` 부호 변화 시점 비교 필요.
- 회피 중 멈춤이 DWB 때문인지 collision_monitor 때문인지: 체인 각 단계를 동시에 봐야 판정 가능.

## 조치 (2026-10-07)
| 항목 | 변경 |
|---|---|
| DWB 생성기 | `trajectory_generator_name: dwb_plugins::LimitedAccelGenerator`, `sim_period: 0.1` → 후보가 현재 속도 ±0.05 m/s 안 |
| vy 샘플 | `vy_samples` 10 → 11 (현재 vy 기준 대칭, 간격 0.01) |
| `min_speed_xy` | 0.05 → 0.0 (원래 무효였음, **동작 변화 없음**, 파일이 실제 동작과 같게) |
| collision_monitor | polygon `visualize: true` (RViz에서 정지/감속 영역 확인) |
| depth 홈 자세 게이트 | `sparse_point_cloud`가 `/joint_states`를 보고 관절1~5가 홈 자세(base.yaml `arm_home_pose_rad`, launch가 읽어 전달) ±0.04 rad 밖이거나 joint_states가 2 s 이상 없으면 **발행을 멈춘다** → collision_monitor가 `source_timeout`(1 s) 후 "invalid source"로 로봇 정지. 잘못된 기준으로 주행하지 않게 하는 의도된 fail-safe |
| 진단 도구 | `tools/nav/cmd_chain_monitor.py`(nav→smoothed→cmd_vel, CM 개입, vy 부호 뒤집힘/10 s, map→odom 점프), `tools/nav/dwb_ab.sh vy_off/vy_on/show`(재시작 없이 vy A/B), `record_trial.sh`에 `/cmd_vel_smoothed`, `/joint_states` 추가 |

**주의(동작 변화)**: LimitedAccelGenerator는 회피 동작 자체도 바꾼다(정지 상태에서 한 주기에 고를 수 있는 속도가 0.05 m/s까지라 출발이 완만). 2026-10-06의 "얼추 됨" 회피 결과는 이 변경 전 설정 기준이므로 회피 시험을 다시 해야 한다. 되돌리려면 `trajectory_generator_name` 줄을 지운다.
**주의(게이트)**: camera.launch만 단독으로 띄우고 base_node가 없으면 `/joint_states`가 없어 클라우드가 안 나온다(의도). 카메라 단독 시험은 `-p home_pose_rad:=[0.0]`(게이트 끔).

## 확인 상태
- L0: YAML 파싱, `colcon build`, `colcon test`(기존 lint 실패 25건 외 신규 없음), 게이트 로직 단위 확인(홈/+0.03 통과, +0.10·joint_states 없음/오래됨 차단).
- **실기 미검증**: 흔들림 개선 여부, 회피 재시험, 게이트가 실제 서보 백래시 범위에서 열려 있는지(로그의 `max error` 값으로 확인).

## 실기 시험 순서 (다음)
1. 빈 공간 직선 goal, `cmd_chain_monitor.py` 켜고 **새 설정(LimitedAccel)** vs `trajectory_generator_name` 제거(옛 설정) 비교 — vy-flips/분, CTE.
2. 같은 조건에서 `dwb_ab.sh vy_off` — 흔들림이 사라지면 lateral 제어 문제 확정.
3. 흔들림 시점과 `map->odom JUMP` 시점 비교(AMCL 영향).
4. 상자 회피 재시험 — 멈출 때 `<<CM-STOP>>`가 찍히는지(collision_monitor) 아니면 nav 자체가 0인지(DWB/planner).

## 2026-10-07 실기 시험 중 추가로 발견/수정한 것
1. **홈 자세 게이트가 주행 중 열림/닫힘 반복** → collision_monitor가 "invalid source"로 3번 정지 → 시험 중단.
   주행 중 관절3 읽기가 0.025~0.042 rad로 흔들림(백래시/진동). 허용오차 0.04 → **0.08 rad + 1초 debounce**.
   (게이트는 큰 자세 변화(0.3~0.6 rad)만 잡고 작은 백래시는 margin 60 mm가 처리. 관절3 0.029 rad 오차에서 거짓 점 0개 실측.)
   팔 홈 이동(`arm_move_home_on_start`) 후 관절3은 목표보다 0.029 rad 모자란 채 끝났다(완료 기준 0.03).
   게이트가 처음 팔이 접힌 상태(관절3 0.654 rad 오차)를 실제로 막는 것도 확인.
2. **CPU 과부하**(load 11, DWB 10 Hz → 3 Hz): camera.launch의 depth_colorizer(028에도 기록). `colorizer:=false` 인자 추가.
3. **local costmap이 오래된 LiDAR 점으로 막힘** (2026-10-06 scan `clearing: false`의 부작용): 3x3 m 창의 대부분이 inscribed/lethal,
   비우자 로봇 0.5 m 내 lethal 84 → 17칸. **scan/depth를 별도 ObstacleLayer로 분리**(`obstacle_layer`=scan, clearing true /
   `depth_layer`=depth). 레이어마다 자기 점만 지우므로 LiDAR가 depth 상자를 못 지운다. global costmap은 아직 한 레이어(회피 단계에서).
4. **좁은 방에서 DWB가 '제자리'를 고름**: `/evaluation` 확인 결과 전진 궤적 798개 전부 유효인데, 전진 시 BaseObstacle 111×0.1=11.1점이
   진행 이득(~2점)보다 커서 제자리 회전(17.0 < 17.1)을 선택 → 시간 초과. 원인은 2026-10-06 회피 튜닝(inflation 0.40, cost_scaling 5,
   BaseObstacle 0.1)이 이 방의 통로 전체를 비용 84+로 만든 것. 직진 흔들림 시험이 이 문제와 섞여서 **아직 결론 없음**.
5. 위치 추정: 시작 시 AMCL 초기값(0.15,-0.02)이 실제와 달랐음. RViz 없이 맞추는 `tools/nav/scan_match_init.py`(스캔-지도 전수 탐색,
   일치도 0.97 vs 2등 0.67) 추가. 시험 중 AMCL이 1 m 틀어진 시점이 있었음(원인 미확인).
6. 도구: `tools/nav/straight_trial.py`(직진 1회 + 지표, `Log/wobble_trials.csv`), `nav2.launch.py params_file:=`,
   `tools/nav/ab_params/make_variants.sh`(생성기만 다른 C 변형).

### 직진 시험 데이터 (유효분)
| 조건 | 결과 | vy 뒤집힘 | vy RMS | 최대 횡이탈(map) |
|---|---|---|---|---|
| C(Standard 생성기) B→A | 성공 18.4 s | 8회(26/분) | 0.035 | 6.7 cm |
| C A→B | 시간 초과(목표 21 cm 앞 기어감) | 3회 | 0.039 | 12.9 cm |
A(LimitedAccel), vy_off 비교는 아직. 다음: 시험 전용 파라미터(BaseObstacle 0.02)로 생성기만 바꿔 비교할지 사용자 결정 대기.

## 2026-10-07 23:40 직진 A/B (시험 전용 파라미터: BaseObstacle 0.02, 둘 다 xy_goal_tolerance 0.12 수정 후)
7. **RotateToGoal 허용오차 충돌 발견/수정**: DWB `FollowPath.xy_goal_tolerance`(미설정 → 기본 0.25) 안에서는 RotateToGoal이 모든 이동 궤적을
   무효로 만드는데 goal checker는 0.15 → 목표 0.15~0.25 m 앞에서 회전만 하다 "Failed to make progress". `/evaluation`에서 1365개 궤적 전부
   RotateToGoal 무효로 확인. **기본 설정에 0.12 추가**. 028의 "항상 목표 0.15 m 앞에서 멈춤"도 같은 원인일 가능성 큼(추정).
8. `scan_match_init.py`는 패키지로 옮겨 localization 시작 시 자동 실행(확신 낮으면 안 보냄). 빨래바구니 등 지도에 없는 물체가 있을 땐
   0.72/차이 0.03으로 거부 → 의도대로 동작.

| 조건 | 회차 | 결과 | vy 뒤집힘 | vy RMS | wz RMS | 횡이탈 | 도착 오차 |
|---|---|---|---|---|---|---|---|
| C Standard | B→A | 성공 13.0 s | 9 (42/분) | 0.041 | 0.20 | 6.0 cm | 10.8 cm |
| C Standard | A→B | 성공 9.2 s | 15 (98/분) | 0.046 | 0.22 | 6.3 cm | 17.6 cm |
| A LimitedAccel | B→A | 성공 15.1 s | **0** | 0.063 | 0.26 | 8.3 cm | **1.8 cm** |
| A LimitedAccel | A→B | 시간 초과, 15.4 cm 앞 정지 | 0 | 0.027 | 0.04 | 10.2 cm | 15.4 cm |
(무효: C 2회·A 2회 — 제자리 회전 실패/이미 목표 근처/A 끝에서 출발 안 함)

**잠정 결론(표본 작음)**: Standard 생성기는 vy 부호가 분당 40~100회 뒤집힘(게걸음), LimitedAccel은 0회. 흔들림 원인이
"매 주기 vy 전 범위 샘플링"이라는 가설과 일치. 단 A는 vy를 한 방향으로 꾸준히 써서 vy RMS는 오히려 큼(횡이탈 비슷).
**남은 문제**: A 끝(y≈0.2)에서 B로 출발을 못 하는 경우(C·A 둘 다), A4의 목표 15 cm 앞 정지(데드존 아래 저속 추정) — 미조사.

## 2026-10-07 23:55 데드존 아래 속도 문제 (A 끝 출발 실패 / 목표 앞 정지)
9. `/evaluation` 실측: 목표 20 cm 앞에서 DWB 최선 vx=0.006 m/s(0.025와 점수 동일 2.70 — 1.5 s 동안 둘 다 costmap 1칸 미만 이동이라 GoalDist가 같음).
   바퀴는 안 도는데 open-loop odom은 움직인 것으로 적분 → AMCL이 되돌림(map→odom 점프 3~4 cm 반복) → 60 s 시간 초과.
   A 끝 출발 실패도 같은 계열(wz 0.02만 출력). **조치: `min_speed_xy` 0.04 + `min_speed_theta` 0.1**(둘 다 미만인 궤적 거부).
   - 처음 0.2 rad/s로 했더니 **제자리 회전 4/4 실패**: LimitedAccel은 정지 상태에서 한 주기에 acc_lim_theta×0.1 s = 0.1 rad/s까지만 샘플 → 회전 후보 0개. 0.1로 낮춤.
   - 0.1 결과(A 조건, 시험 전용 BaseObstacle 0.02): **4회 중 3회 성공(13.6~22 s, 도착 오차 8.6~13 cm), vy 뒤집힘 0, 회전 4/4 성공.**
     실패 1회는 A 끝 (0.90, 0.14)에서 출발 못 함(vy 뒤집힘 21, map→odom 점프 10 — 그 자리가 장애물에 가까워 비좁고 위치도 흔들림).
   - 근본 원인은 엔코더 없는 open-loop odom(명령 = 실제 이동 가정). 엔코더 odom 단계(ROADMAP)에서 다시 본다.

## 2026-10-08 00:20 대각선(게걸음) 주행 원인 → RotationShim 추가 (주행 검증 전, 배터리 9.44 V로 중단)
10. 사용자 관찰 "대각선으로 간다": 출발 전 제자리 회전이 goal yaw 허용오차 0.4 rad(23°) 때문에 15~20° 틀어진 채 성공 처리되고,
    DWB(홀로노믹, GoalAlign 가중치 낮음)는 몸을 돌리지 않고 vy로 경로를 따라감 → 몸이 비스듬한 채 대각선 주행.
    A 조건의 vy RMS가 높았던(0.065~0.075) 이유이기도 함 — vy 지표가 이 효과로 오염돼 있었다.
    **정면 전용 depth 카메라가 진행 방향을 못 보는 안전 문제**이기도 하다.
    조치: `FollowPath`를 `nav2_rotation_shim_controller::RotationShimController`(primary = DWB)로. 경로 방향과 15° 넘게 차이 나면 먼저
    제자리 회전(5° 이내까지, 0.4 rad/s), 최종 yaw 회전도 shim(`rotate_to_goal_heading`). Nav2 기동/플러그인 생성까지만 확인, **주행 시험 전**.
    `straight_trial.py`에 `start_yaw_err_deg`, `yaw_dev_max_deg`(주행 중 몸과 직선의 최대 각도 차 = 대각선 지표) 추가, CSV는 `Log/wobble_trials_v2.csv`.

### 내일 할 일 (순서)
1. 충전 후 `robot.launch.py arm_command_enabled:=true arm_move_home_on_start:=true`(팔 홈, 사람 입회) → `camera.launch.py colorizer:=false`
   → `nav2.launch.py params_file:=$HOME/jetrover_ws/tools/nav/ab_params/nav2_params_wobble_limited.yaml` (자동 위치 추정 로그 확인).
   Nav2 재시작은 `tools/nav/stop_nav2.sh`를 **별도 명령으로** 실행(같은 명령줄에 `ros2 launch jetrover_navigation nav2.launch.py`가 있으면 자기 셸을 죽임).
2. A(LimitedAccel+shim) 6회: `straight_trial.py S_A_limited --goal 1.0 1.45` ↔ `--goal 1.0 0.30` 왕복(회전 단계 불필요, shim이 함).
   확인: 출발 회전 후 yaw_dev_max가 작아졌는지(대각선 해소), vy 뒤집힘, 성공률.
3. C(`nav2_params_wobble_standard.yaml`) 6회 같은 방식 → 표로 비교 → 생성기 채택 확정.
4. 그다음 2단계(장애물 회피): 시험 전용 BaseObstacle 0.02를 기본(0.1)과 어떻게 맞출지, global costmap 레이어 분리, collision monitor 개입 확인.
