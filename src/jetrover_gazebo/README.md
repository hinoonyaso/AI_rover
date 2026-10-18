# jetrover_gazebo — JetRover in Gazebo Harmonic (host PC)

PRD: `prd/gazebo-sim.md`, 시험: `prd/gazebo-sim-test-plan.md`. 환경은 Jetson 워크스페이스에서 구축·검증(L0)하고 **실행은 host PC**.

구조: Nav2(/cmd_vel Twist) → `cmd_vel_to_stamped.py` → `mecanum_drive_controller`(ros2_control) → `gz_ros2_control` → Gazebo 바퀴.
메카넘은 공식 데모(`gz_ros2_control_demos` test_mecanum_drive) 방식: 바퀴 충돌 = 구, 롤러 대각 방향 이방성 마찰(mu=1, mu2=0, fdir1).
센서: LiDAR `/scan`(lidar_frame), RGB-D `/depth_cam/color/image_raw`·`/depth_cam/depth/image_raw`(16UC1 mm, 실기와 같은 형식), IMU `/imu/data_raw`.
팔은 base.yaml 홈 자세에 위치 제어로 고정(카메라가 팔 끝). EKF는 실기와 같고 바퀴 속도만 컨트롤러 odometry.
월드는 SLAM 지도(`maps/lap2_20261005`)의 점유 칸을 벽(0.5 m)으로 세운 것 → **지도 좌표 = Gazebo 좌표**, AMCL에 같은 지도.

## 1. host 준비 (1회, sudo — `setup/ENVIRONMENT_SETUP.md`에도 기록)
```bash
sudo apt install -y ros-jazzy-ros-gz ros-jazzy-gz-ros2-control ros-jazzy-gz-ros2-control-demos \
  ros-jazzy-ros2-control ros-jazzy-ros2-controllers ros-jazzy-navigation2 ros-jazzy-nav2-bringup \
  ros-jazzy-robot-localization ros-jazzy-xacro ros-jazzy-teleop-twist-keyboard python3-scipy
```
**반드시 `~/jetrover_ws`에 clone** (Nav2 설정의 BT XML 경로가 `/home/sang/jetrover_ws/install/...` 절대경로):
```bash
git clone https://github.com/hinoonyaso/AI_rover.git ~/jetrover_ws   # 이미 있으면 git pull
cd ~/jetrover_ws && source /opt/ros/jazzy/setup.bash
colcon build --packages-select jetrover_description jetrover_base jetrover_perception \
  jetrover_navigation jetrover_nav_plugins jetrover_gazebo
source install/setup.bash && tools/nav/ab_params/make_variants.sh   # nav2_params_mppi.yaml 생성
```
(OrbbecSDK_ROS2, jetrover_microros는 host에 빌드하지 않는다 — `--packages-select` 그대로.)

**실기와 토픽이 섞이지 않게 다른 도메인**을 쓴다(로봇은 `ROS_DOMAIN_ID=25`):
```bash
export ROS_DOMAIN_ID=31   # 시뮬레이션 터미널마다
export GZ_IP=127.0.0.1    # gz-transport loopback만 — 없으면 host에서 월드 로딩 중 멈춘 적 있음(troubleshooting/040)
# 노트북 host(Intel 화면 + GTX 1050): GUI를 NVIDIA로 — 없으면 스캔 방 텍스처가 회색, RTF 0.52(troubleshooting/040)
export __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia
```

## 2. 공식 데모로 host 확인 (선택)
```bash
ros2 launch gz_ros2_control_demos mecanum_drive_example.launch.py
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true
```

## 3. JetRover 시뮬레이션
```bash
ros2 launch jetrover_gazebo sim.launch.py                 # 상자 있는 월드, 시작점 A (1.02, 0.37, 83°)
ros2 launch jetrover_gazebo sim.launch.py world:=lap2_room.sdf    # 상자 없는 방
ros2 launch jetrover_gazebo sim.launch.py world:=room_lap2.sdf    # 스캔한 방(메쉬 + 구운 텍스처, 2026-10-14 자동 1차본 — 아래 표)
ros2 launch jetrover_gazebo sim.launch.py world:=room_lap2_objects.sdf   # + Nav 상자 33×22×11 cm(A→B 경로), 팔 시험 큐브 R/G/B
ros2 launch jetrover_gazebo sim.launch.py world:=room_lap2_objects.sdf x:=0.45 y:=0.75 yaw:=1.5708   # 팔 시험 자리(큐브 0.25 m 앞)
# MoveIt으로 팔 움직이기(2026-10-17): 실기 브리지와 같은 이름의 궤적 컨트롤러(arm_controller, gripper_controller)를 띄운다
ros2 launch jetrover_gazebo sim.launch.py world:=room_lap2_objects.sdf arm_mode:=moveit x:=0.45 y:=0.75 yaw:=1.5708
ros2 launch jetrover_manipulation move_group.launch.py mode:=real use_sim_time:=true   # 다른 터미널
python3 tools/manipulation/moveit_t7.py joint-goals --count 3                           # 실기와 같은 시험 도구
# 카메라로 찾아 집기(2026-10-18): 색 큐브 검출 → IK → MoveIt → 닫기 → 들기 → 바닥 다시 보기(남아 있으면 FAIL)
ros2 run jetrover_perception cube_detector.py --ros-args -p use_sim_time:=true          # cubes/red|green|blue
python3 tools/manipulation/pick_detected.py red --gripper sim                            # 3자리 3/3, docs/benchmarks/sim/pick_detected_20261018.md
ros2 run teleop_twist_keyboard teleop_twist_keyboard      # /cmd_vel(Twist). Shift+J/L = 옆이동
```
그리퍼 effort: `sim.launch.py`가 xacro에 `gripper_effort:=2`(N·m)를 넘긴다. 공식 URDF 값 1000이면 손가락이 사실상
무한한 힘으로 조여 큐브가 튕겨 나갔다(troubleshooting/043). 실기 URDF는 1000 그대로다(실기에서는 쓰지 않는 값).

확인(시험 계획 5번): `i` 전진, Shift+J 왼쪽/Shift+L 오른쪽 **옆이동 방향이 맞는지**(반대거나 돌면서 가면 xacro의 fdir1 부호 문제),
`ros2 topic hz /scan /imu/data_raw /depth_cam/depth/image_raw /odom`, RViz에서 TF/스캔.

## 4. Nav2 (시뮬레이션 시간)
```bash
ros2 launch jetrover_navigation nav2.launch.py use_sim_time:=true \
  params_file:=$HOME/jetrover_ws/tools/nav/ab_params/nav2_params_mppi.yaml
python3 tools/nav/straight_trial.py SIM_mppi --goal 1.0 1.45       # 실기 F2와 같은 A→B
```
자동 위치 추정(scan_match_init)도 그대로 동작한다(같은 지도).
컨트롤러 비교 시나리오(S1 직진, S2 상자 왕복, S3 F2-4 정체 지점 × dwb/mppi/mppi_nolr)는 `tools/sim/README.md`.

## 5. depth 장애물(선택)
sparse_point_cloud는 "기준 depth와 비교" 방식이라 시뮬레이션용 기준이 필요하다.
**현재 기준(2026-10-18)**: `config/depth_background_ref_sim.npy` — `room_lap2_objects.sdf`, 로봇 A (1.02, 0.37, 83°), 홈 자세,
Nav 상자(`object_0`)를 z −3으로 치운 뒤 30프레임 중앙값. 확인: 상자 앞 0.37 m에서 점의 84 %가 상자 안, local costmap 상자 칸 35/35
(`tools/sim/check_depth_obstacles.py`). 상자 높이 11 cm는 LiDAR에 안 보여서 이 경로로만 회피한다. 원래 절차(상자 없는 월드):
```bash
ros2 launch jetrover_gazebo sim.launch.py world:=lap2_room.sdf     # 상자 없음, 로봇 앞 비어 있게
python3 tools/perception/capture_depth_reference.py --out src/jetrover_gazebo/config/depth_background_ref_sim.npy
colcon build --packages-select jetrover_gazebo
ros2 launch jetrover_gazebo sim.launch.py depth_obstacles:=true
```

## 파일
| 파일 | 내용 |
|---|---|
| `urdf/jetrover_sim.urdf.xacro` | 실기 URDF(`sim_mode:=true`) + ros2_control + 마찰 + 센서 |
| `config/sim_controllers.yaml` | joint_state_broadcaster, mecanum_drive_controller(r 0.0485, lx+ly 0.2096), arm 위치 |
| `config/sim_bridge.yaml` | Gazebo ↔ ROS 토픽 |
| `config/sim_ekf.yaml` | 실기 ekf.yaml + 컨트롤러 odometry |
| `scripts/map_to_world.py` | 지도 → 월드 (`--box X Y SX SY SZ` 고정 장애물, `--object X Y SX SY SZ R G B MASS` 색·질량 있는 물체) |
| `scripts/cmd_vel_to_stamped.py`, `depth_float_to_mm.py`, `arm_hold.py` | 보조 노드 |
| `worlds/lap2_room.sdf`, `lap2_room_box.sdf` | 생성된 월드(상자: 중심 (1.21, 1.00), 0.28×0.25×0.10 m) |
| `worlds/room_lap2.sdf`, `models/room_lap2/` | 스캔 방(`tools/scan`, 기록 `docs/benchmarks/sim/room_scan_20261014.md`). 메쉬는 Git LFS(host만) |
| `models/room_lap2_fill/` | 스캔 방 바닥 흰 구멍 채움(합성, `tools/scan/room_fill.py`): 텍스처 바닥 판. visual만, LiDAR에는 안 보임(벽 채움은 기본 끔) |
| `worlds/room_lap2_objects.sdf` | 스캔 방 + Nav 상자(1.21, 1.00) + 팔 시험 큐브 R/G/B(0.37/0.45/0.53, 1.00). 생성 명령은 기록 문서 |

## 알려진 한계 / 확인 필요(L0까지만 검증, host 실행 전)
- 마찰 방향(fdir1) 부호는 공식 데모 값 — 실제 옆이동 방향은 host에서 확인.
- 시뮬레이션에는 모터 데드존·open-loop odom·서보 백래시가 없다(실기 문제 일부는 재현 안 됨).
- 그리퍼 연동 관절(mimic): DART가 mimic 제약을 지원하지 않아 `r_joint`만 움직였다 → 손가락 5개 관절을 ros2_control에 상태 인터페이스로
  등록해 gz_ros2_control이 따라 움직이게 함(2026-10-14). 큐브 집기 3/3(`tools/sim/README.md`). 실제 4절 링크를 배율 ±1로 근사한 것이라
  집는 힘·미끄러짐은 실기와 다를 수 있다. 로그의 `does not support mimic constraints` 오류는 남지만 무해.
