# PRD: JetRover Gazebo 시뮬레이션 (Harmonic + gz_ros2_control + mecanum_drive_controller)

신뢰 수준: **계획** (2026-10-09 사용자 승인: 환경은 Jetson 워크스페이스에 구축, 실행은 host PC).

## 목적
배터리·로봇 이동 없이 Nav2/MPPI 설정을 반복 시험하고(회귀 시험 포함), 실기와 같은 좌표·같은 상위 스택으로 결과를 비교한다.
엔코더 odom(바퀴 속도 기반) 구성도 실기 전에 시험할 수 있다.

## 구조 (실기와 상위 스택 동일, 맨 아래만 다름)
```
Nav2(MPPI/DWB, costmap, AMCL, scan_match_init) ── /cmd_vel(Twist)
   └ sim: cmd_vel_to_stamped → mecanum_drive_controller(ros2_control) → gz_ros2_control → Gazebo 바퀴
   └ 실기: base_node(메카넘 역기구학) → STM32
EKF(robot_localization) ← sim: 컨트롤러 odom twist + IMU / 실기: wheel_twist + IMU
```
- 메카넘: 공식 데모 방식(바퀴 충돌 = 구, 롤러 방향 이방성 마찰 mu=1/mu2=0/fdir1 대각). 롤러 개별 모델링 안 함.
- 센서: gpu_lidar(/scan, lidar_frame), rgbd_camera(/depth_cam/*, depth는 실기와 같은 16UC1 mm로 변환), imu(/imu/data_raw).
- 팔: 홈 자세에 위치 제어로 고정(카메라 TF가 팔 끝에 달려 있음).
- 월드: SLAM 지도(`maps/lap2_20261005`)의 점유 칸을 벽(높이 0.5 m)으로 세운 SDF → 지도와 같은 좌표, 같은 지도로 AMCL.
- 실기 URDF는 `sim_mode:=false`(기본)에서 지금과 동일해야 한다(바퀴 fixed, 충돌 메쉬).

## 범위 / 비범위
- 범위: `jetrover_gazebo` 패키지(xacro, 월드 생성기, 브리지/컨트롤러/EKF 설정, launch, 보조 노드), `jetrover_description` sim_mode 옵션,
  `jetrover_navigation` use_sim_time 인자, host 실행 문서.
- 비범위: 실기 ros2_control 이행(엔코더 이후, ROADMAP), 롤러 물리, 그리퍼 물리, 강화학습.

## 완료 기준
- L0(Jetson): 빌드, sim_mode=false URDF가 이전과 동일(diff), sim URDF→SDF 변환 성공(`gz sdf -p`), 월드 SDF 검증(`gz sdf -k`), lint.
- L5-sim(host): 키보드로 전/후/좌/우/회전 이동, /scan·depth·imu·odom 토픽, Nav2 직선 왕복과 상자 회피를 실기와 같은 좌표로 재현.
