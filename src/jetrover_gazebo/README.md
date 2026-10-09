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
ros2 run teleop_twist_keyboard teleop_twist_keyboard      # /cmd_vel(Twist). Shift+J/L = 옆이동
```
확인(시험 계획 5번): `i` 전진, Shift+J 왼쪽/Shift+L 오른쪽 **옆이동 방향이 맞는지**(반대거나 돌면서 가면 xacro의 fdir1 부호 문제),
`ros2 topic hz /scan /imu/data_raw /depth_cam/depth/image_raw /odom`, RViz에서 TF/스캔.

## 4. Nav2 (시뮬레이션 시간)
```bash
ros2 launch jetrover_navigation nav2.launch.py use_sim_time:=true \
  params_file:=$HOME/jetrover_ws/tools/nav/ab_params/nav2_params_mppi.yaml
python3 tools/nav/straight_trial.py SIM_mppi --goal 1.0 1.45       # 실기 F2와 같은 A→B
```
자동 위치 추정(scan_match_init)도 그대로 동작한다(같은 지도).

## 5. depth 장애물(선택)
sparse_point_cloud는 "기준 depth와 비교" 방식이라 시뮬레이션용 기준이 필요하다:
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
| `scripts/map_to_world.py` | 지도 → 월드 (`--box X Y SX SY SZ`로 장애물) |
| `scripts/cmd_vel_to_stamped.py`, `depth_float_to_mm.py`, `arm_hold.py` | 보조 노드 |
| `worlds/lap2_room.sdf`, `lap2_room_box.sdf` | 생성된 월드(상자: 중심 (1.21, 1.00), 0.28×0.25×0.10 m) |

## 알려진 한계 / 확인 필요(L0까지만 검증, host 실행 전)
- 마찰 방향(fdir1) 부호는 공식 데모 값 — 실제 옆이동 방향은 host에서 확인.
- 시뮬레이션에는 모터 데드존·open-loop odom·서보 백래시가 없다(실기 문제 일부는 재현 안 됨).
- 그리퍼 연동 관절(mimic)은 물리적으로 자유 — 주행 시험에는 영향 없음.
