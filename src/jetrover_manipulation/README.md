# jetrover_manipulation

MoveIt2 설정(5자유도 팔 `arm` = joint1~5, 그리퍼 `gripper` = r_joint). Jazzy.
참고: `~/AI_secretary_robot/src/control/jetrover_arm_moveit` (Humble)를 Jazzy 형식으로 옮김.

## 상태 (2026-10-06)
- [x] 설정 파일 작성 + SRDF가 URDF 링크/조인트와 일치하는지 검증, 패키지 빌드
- [x] MoveIt apt 설치(사용자, 2026-10-06)
- [x] move_group 기동 + plan_only 계획 시험: 관절 목표 OK, 위치 목표 5곳 OK(실행 안 함). 발견: TRAC-IK는 5자유도에서 위치 목표가 전부 실패 -> KDL `position_only_ik: true`로 교체(kinematics.yaml 주석). 관절 한계는 ±1.70(실제 팔이 1.688에 놓일 수 있어 ±1.65면 계획 거부)
- [x] 충돌 매트릭스: host Setup Assistant 생성본 126쌍 + 이전 목록의 그리퍼 연동부 19쌍 합침(2026-10-06). 생성본만 쓰면 그리퍼 링크 쌍(l_in-l_link 등)이 접촉으로 잡혀 시작 상태 충돌로 모든 계획이 실패했음. 재시험: 계획 4곳 OK, 몸통 뒤 껍데기와의 충돌은 검출됨
- [x] host RViz MotionPlanning 연동 확인(계획만, 실행은 plan_only가 차단)
- [x] 실행 브리지 구현(2026-10-06): `scripts/trajectory_bridge.py`(Python) + base_node `arm/command_timed`(C++, JointTrajectory 첫 점의
      time_from_start가 이동 시간, 0.1~5 s). 시험: 단위 7개 통과, **dry_run 종단 시험 통과**(move_group -> 브리지 액션 수신, 명령 미발행).
      브리지 안전장치: 시작 자세 불일치/오래된 joint_states/관절 한계/스텝 0.2 rad 초과 시 전송 전 거부, 추종 지연 0.4 rad 초과·취소 시 현재 자세 유지.
- [x] **실기 실행 시험 통과(2026-10-06, 배터리 9.97 V, 사용자가 전원 스위치 옆, 속도 스케일 0.3)**: RViz 경로가 아니라 MoveGroup 액션(스크립트)으로 joint1 +0.10 -> -0.10, joint2 +0.15 -> -0.15 왕복. MoveIt 결과 SUCCESS 4/4, 실제 이동량 0.084/-0.096/0.142/-0.142 rad(서보 해상도 ~0.004~0.017 rad 오차), 브리지 거부/지연 중단 0건, base_node 가드 거부 0건.
- [ ] 더 큰 이동/위치 목표(RViz) 시험, 그리퍼 컨트롤러 시험, 충전 후(>10.5 V) 반복

## 설치 (사용자가 직접 sudo)
```bash
sudo apt install -y ros-jazzy-moveit ros-jazzy-moveit-setup-assistant ros-jazzy-trac-ik-kinematics-plugin \
  ros-jazzy-moveit-simple-controller-manager ros-jazzy-joint-state-publisher
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


## 브리지 안전성 (T4, 2026-10-11, `prd/arm-control-path.md` R7)
- **관절별 신선도**: `/joint_states` 헤더는 base_node가 캐시 값을 계속 재발행해서 항상 최신처럼 보인다. 브리지는 이제 base_node의 `arm/servo_stats`(서보 응답 프레임이 실제로 도착한 시각 기준)의 `age_s`를 구독해, **궤적에 쓰이는 관절 각각**이 `joint_age_limit_s`(기본 1.5 s)보다 오래됐거나 한 번도 응답한 적이 없으면 목표를 거부/중단한다(중단 시 팔 관절만 hold). `arm_poll_hz` 20 Hz에서 연속 무응답 최대 공백이 0.9 s(5 Hz는 2.4 s)라서 **`arm_poll_hz` 12 Hz 이상이 전제**다(`docs/benchmarks/arm_poll_bench_20261011.md`). `arm/servo_stats`가 3 s 넘게 안 오면 그것도 거부. `require_servo_stats:=false`는 base_node 없는 dry run 전용(`execution.launch.py`가 dry_run일 때만 자동으로 끈다).
- **목표 수락은 원자적**: `BusyGate`가 한 번의 잠금 아래에서 확인·설정한다(옛 `_busy`는 수락 콜백에서 확인하고 실행에서 설정해, 팔·그리퍼 목표가 동시에 오면 둘 다 수락될 수 있었다). 실행 중 예외가 나도 `finally`로 해제하고, 120 s 넘은 토큰은 새어 나간 것으로 보고 넘겨받는다.
- **그리퍼는 hold하지 않는다**: 취소·실패 시 "현재 읽은 위치로 이동"은 파지 중 조임을 풀어 물체를 떨어뜨리므로, hold는 팔 관절에만 보낸다.
- **파지 중 목표 거부(T6 c3, 2026-10-14)**: base_node의 `arm/grasp_state`(String)를 구독해, 그리퍼 목표는 `Idle`에서만(파지가 ID 10을 쥐는 동안은 HOLDING이어도 `arm/release`만 연다), 팔 목표는 `Check/Closing/Squeeze/Releasing/Failed`에서 거부하고 `Idle/Holding`에서 허용한다(물체를 들고 옮겨야 하므로). 토픽이 한 번도 안 왔으면(파지 기능 없는 옛 base_node) 허용, 받은 뒤 3 s 넘게 끊기면 거부. base_node도 같은 판정을 한 번 더 한다(두 겹). 실제 노드 스모크: 네 상태 모두 기대대로.
- 시험: `test/test_bridge_logic.py`(관절 신선도 6, 경쟁 조건 3, hold 정책 4 + 기존 7; ROS 없이 실행, CI 포함)와 실제 노드 스모크(동시 목표 1개만 수락, 서보 하나만 침묵하면 중단, 복구 후 재수락).
