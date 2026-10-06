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
