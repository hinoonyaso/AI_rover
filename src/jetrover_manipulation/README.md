# jetrover_manipulation

MoveIt2 설정(5자유도 팔 `arm` = joint1~5, 그리퍼 `gripper` = r_joint). Jazzy.
참고: `~/AI_secretary_robot/src/control/jetrover_arm_moveit` (Humble)를 Jazzy 형식으로 옮김.

## 상태 (2026-10-06)
- [x] 설정 파일 작성 + SRDF가 URDF 링크/조인트와 일치하는지 검증, 패키지 빌드
- [x] MoveIt apt 설치(사용자, 2026-10-06)
- [x] move_group 기동 + plan_only 계획 시험: 관절 목표 OK, 위치 목표 5곳 OK(실행 안 함). 발견: TRAC-IK는 5자유도에서 위치 목표가 전부 실패 -> KDL `position_only_ik: true`로 교체(kinematics.yaml 주석). 관절 한계는 ±1.70(실제 팔이 1.688에 놓일 수 있어 ±1.65면 계획 거부)
- [x] IK 솔버는 **pick_ik**(2026-10-07에 KDL position_only에서 바꿈 — 위치는 정확히, 방향은 가중치로; 근거는 `config/kinematics.yaml` 주석).
      **Jetson에 `ros-jazzy-pick-ik`가 없어서** 그동안 move_group 팔 IK가 없었다(관절 목표만 써서 T7엔 영향 없었음) → 2026-10-15 설치.
      확인(`compute_ik`, 계획만): pregrasp 자세 FK 위치·방향 → 원래 관절값 재현(위치 0.3 mm), +3 cm 앞·5 cm 왼쪽 5 cm 아래도 성공(≤ 1.0 mm, 그리퍼 아래 방향 1.4°).
- [x] 충돌 매트릭스: host Setup Assistant 생성본 126쌍 + 이전 목록의 그리퍼 연동부 19쌍 합침(2026-10-06). 생성본만 쓰면 그리퍼 링크 쌍(l_in-l_link 등)이 접촉으로 잡혀 시작 상태 충돌로 모든 계획이 실패했음. 재시험: 계획 4곳 OK, 몸통 뒤 껍데기와의 충돌은 검출됨
- [x] host RViz MotionPlanning 연동 확인(계획만, 실행은 plan_only가 차단)
- [x] 실행 브리지 구현(2026-10-06): `scripts/trajectory_bridge.py`(Python) + base_node `arm/command_timed`(C++, JointTrajectory 첫 점의
      time_from_start가 이동 시간, 0.1~5 s). 시험: 단위 7개 통과, **dry_run 종단 시험 통과**(move_group -> 브리지 액션 수신, 명령 미발행).
      브리지 안전장치: 시작 자세 불일치/오래된 joint_states/관절 한계/스텝 0.2 rad 초과 시 전송 전 거부, 추종 지연 0.4 rad 초과·취소 시 현재 자세 유지.
- [x] **실기 실행 시험 통과(2026-10-06, 배터리 9.97 V, 사용자가 전원 스위치 옆, 속도 스케일 0.3)**: RViz 경로가 아니라 MoveGroup 액션(스크립트)으로 joint1 +0.10 -> -0.10, joint2 +0.15 -> -0.15 왕복. MoveIt 결과 SUCCESS 4/4, 실제 이동량 0.084/-0.096/0.142/-0.142 rad(서보 해상도 ~0.004~0.017 rad 오차), 브리지 거부/지연 중단 0건, base_node 가드 거부 0건.
- [ ] 더 큰 이동/위치 목표(RViz) 시험, 그리퍼 컨트롤러 시험, 충전 후(>10.5 V) 반복
- [x] T7 준비(2026-10-15): SRDF `home`을 base.yaml 값으로(joint4 1.6043→1.45), 바닥 큐브 자세 `pregrasp_floor`(끝단 0.15 m)·
      `grasp_floor`(0.025 m)·`gripper_open`(펄스 200) 추가 — 큐브 중심이 base_footprint 앞 0.25 m, `tools/sim/arm_ik.py`로 URDF에서 계산
      (실기 서보 오프셋 미반영). 시험 도구 `tools/manipulation/moveit_t7.py`(joint-goals / named / gripper / sequence; 정착 오차 ≤ 0.05 rad,
      `arm/servo_stats` 온도 80 ℃ 중단, IMU 공백). **L1**(가짜 RRC pty + base_node + move_group real + 브리지): 23/23 —
      관절 목표 오차 ≤ 0.021 rad, home↔pregrasp 13 s(scale 0.3), 그리퍼 열기·닫기, 집기 시퀀스 11/11(파지 접촉 523, 들기 후 Holding 유지).
- [x] T7 실기(L2, 2026-10-15): 관절 목표 12/12, 이름 자세 10왕복, 그리퍼 10/10, 집기 시퀀스 4/5(큐브는 베이스 모터에서 정면 24 cm, 그리퍼 바로 아래). 시험 사이엔 `rest_upright`(관절 모두 0)로 식힌다 — `docs/benchmarks/moveit_t7_20261015.md`

## 설치 (사용자가 직접 sudo)
```bash
sudo apt install -y ros-jazzy-moveit ros-jazzy-moveit-setup-assistant ros-jazzy-trac-ik-kinematics-plugin \
  ros-jazzy-moveit-simple-controller-manager ros-jazzy-joint-state-publisher ros-jazzy-pick-ik
```

## 실행
```bash
cd ~/jetrover_ws && colcon build --packages-select jetrover_manipulation && source install/setup.bash
ros2 launch jetrover_manipulation move_group.launch.py            # plan_only: 팔을 안 움직임 (base_node가 /joint_states를 냄)
ros2 launch jetrover_manipulation move_group.launch.py fake_joint_states:=true  # 로봇 없이
ros2 launch jetrover_manipulation move_group.launch.py mode:=real # base_node 가동 + 브리지 구현 후
```
RViz(MotionPlanning)는 host에서 같은 ROS_DOMAIN_ID로 띄운다.

## SRDF 파일 (Setup Assistant 산출물 보관)
- `config/jetrover.srdf`: 실사용(그룹/자세 + 합친 충돌 매트릭스)
- `config/jetrover.setup_assistant.srdf`: Setup Assistant 원본 그대로(수정 금지)
- `config/jetrover.conservative_before_sa.srdf`: 이전 보수적 버전
재생성 절차와 주의(그리퍼 연동부 쌍 유지)는 `troubleshooting/030-moveit-setup-and-srdf-collision-matrix.md`.

## 실행 (실기, 팔이 움직임 -- 승인 후)
1. base_node(실제로 쓴 명령: `-p arm_command_enabled:=true -p arm_move_home_on_start:=true -p arm_poll_hz:=12.0`): `arm_command_enabled:=true`, `arm_poll_hz:=12.0`(기본 5 Hz면 관절당 갱신이 ~1.2 s라 base_node 스텝 가드에 걸림),
   `arm_move_home_on_start:=true`(팔이 클램프 안의 홈 자세로 들어가야 함; 현재 팔이 joint3=1.688로 클램프 1.676 밖이면 브리지가 거부).
2. `ros2 launch jetrover_manipulation move_group.launch.py mode:=real`
3. `ros2 launch jetrover_manipulation execution.launch.py dry_run:=false` (기본은 true = 명령 미발행)
4. RViz에서 **아주 작은** 목표(joint1 ±0.1 rad)부터 Plan -> Execute.
MoveIt 컨트롤러: arm_controller(default), gripper_controller(default: false -- 둘 다 default면 move_group이 segfault).


## 카메라로 찾아 집기 (`tools/manipulation/pick_detected.py`, 2026-10-17~18, 시뮬레이션만)
`jetrover_perception/scripts/cube_detector.py`(HSV 색 영역 + 정렬된 depth 중앙값 → TF로 `base_footprint`의
`cubes/<색>`)를 쓴다. 순서: SRDF `look_floor`(카메라 높이 0.30 m, 73° 아래, 앞 0.27 m를 봄) → 검출 중앙값 →
`tools/sim/arm_ik.py`(URDF 수치 IK, 그리퍼 아래 향함, 관절 탐색 ±1.65)로 위 0.15 m와 `--grasp-z`(기본 0.045)를 푼다
→ MoveIt → 닫기 → 들기 → `look_floor`에서 5 s 다시 본다(바닥 높이 검출 ≥ 2건이면 FAIL).
- `end_effector_link`는 손끝보다 약 3.5 cm 위에 있다. `--grasp-z` 0.045면 손끝이 바닥 위 약 1 cm다(0.025는 바닥 1 cm 아래였다, troubleshooting/043).
- 위에서 잡을 수 있는 범위는 로봇 중심에서 약 0.30 m 이내다(기울기가 15°를 넘으면 IK 단계에서 거부).
- Gazebo: 3자리 3/3(`docs/benchmarks/sim/pick_detected_20261018.md`). **실기 미시험**: 실제 큐브 색이 HSV 기본값에 맞는지
  확인해야 하고, `--gripper real`(접촉 파지 Action)로 실행한다. 팔이 움직이므로 사용자가 있을 때만 한다.

### 실기 (2026-10-18): 교시 보정 후 자동 집기 3/3
- 필요: base_node(`arm_command_enabled`), 카메라, `cube_detector.py -p pitch_offset_deg:=4.9`, `move_group mode:=real`, `execution.launch.py dry_run:=false`.
- `python3 tools/manipulation/pick_detected.py red --gripper real`: 실기 기본 보정 `--offset −0.035 +0.026`, `--tip-z 0.034`, `--floor-z −0.034`.
  집은 뒤에는 큐브를 손으로 받치고 `ros2 service call /arm/release jetrover_interfaces/srv/Release "{}"`를 호출한다.
- 큐브 방향(2026-10-18): 검출기가 `cubes/<색>_yaw`를 내고 집기가 손목을 큐브 면에 맞춘다(|joint5| ≤ 0.45 rad, `--max-wrist`; 넘으면 손가락이 카메라 장착부에 닿는다).
  몸체 앞끝에 너무 가까운 큐브(목표 x < 0.21 m)는 거부한다(`--min-x`). `--no-yaw`로 끌 수 있다. `docs/benchmarks/arm_cube_yaw_20261018.md`.
- 보정을 다시 구할 때: `ros2 run joy joy_node --ros-args -p autorepeat_rate:=50.0` + `tools/manipulation/gamepad_jog.py`로
  큐브를 잡는 자세를 교시(Y)하고, 놓은 뒤 look_floor에서 검출(X)한다. 조작법은 스크립트 도움말에 있다. 수치는 `docs/benchmarks/arm_teach_20261018.md`.

## 브리지 안전성 (T4, 2026-10-11, `prd/arm-control-path.md` R7)
- **관절별 신선도**: `/joint_states` 헤더는 base_node가 캐시 값을 계속 재발행해서 항상 최신처럼 보인다. 브리지는 이제 base_node의 `arm/servo_stats`(서보 응답 프레임이 실제로 도착한 시각 기준)의 `age_s`를 구독해, **궤적에 쓰이는 관절 각각**이 `joint_age_limit_s`(기본 1.5 s)보다 오래됐거나 한 번도 응답한 적이 없으면 목표를 거부/중단한다(중단 시 팔 관절만 hold). `arm_poll_hz` 20 Hz에서 연속 무응답 최대 공백이 0.9 s(5 Hz는 2.4 s)라서 **`arm_poll_hz` 12 Hz 이상이 전제**다(`docs/benchmarks/arm_poll_bench_20261011.md`). `arm/servo_stats`가 3 s 넘게 안 오면 그것도 거부. `require_servo_stats:=false`는 base_node 없는 dry run 전용(`execution.launch.py`가 dry_run일 때만 자동으로 끈다).
- **목표 수락은 원자적**: `BusyGate`가 한 번의 잠금 아래에서 확인·설정한다(옛 `_busy`는 수락 콜백에서 확인하고 실행에서 설정해, 팔·그리퍼 목표가 동시에 오면 둘 다 수락될 수 있었다). 실행 중 예외가 나도 `finally`로 해제하고, 120 s 넘은 토큰은 새어 나간 것으로 보고 넘겨받는다.
- **그리퍼는 hold하지 않는다**: 취소·실패 시 "현재 읽은 위치로 이동"은 파지 중 조임을 풀어 물체를 떨어뜨리므로, hold는 팔 관절에만 보낸다.
- **파지 중 목표 거부(T6 c3, 2026-10-14)**: base_node의 `arm/grasp_state`(String)를 구독해, 그리퍼 목표는 `Idle`에서만(파지가 ID 10을 쥐는 동안은 HOLDING이어도 `arm/release`만 연다), 팔 목표는 `Check/Closing/Squeeze/Releasing/Failed`에서 거부하고 `Idle/Holding`에서 허용한다(물체를 들고 옮겨야 하므로). 토픽이 한 번도 안 왔으면(파지 기능 없는 옛 base_node) 허용, 받은 뒤 3 s 넘게 끊기면 거부. base_node도 같은 판정을 한 번 더 한다(두 겹). 실제 노드 스모크: 네 상태 모두 기대대로.
- 시험: `test/test_bridge_logic.py`(관절 신선도 6, 경쟁 조건 3, hold 정책 4 + 기존 7; ROS 없이 실행, CI 포함)와 실제 노드 스모크(동시 목표 1개만 수락, 서보 하나만 침묵하면 중단, 복구 후 재수락).
