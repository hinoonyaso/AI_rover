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

## 디지털 트윈 확장 (2026-10-09 사용자 승인, Phase 2~4)
Phase 1 = 위의 지도→벽 월드(완료, L0). 이후:
- **Phase 2 — RGB-D 스캔(Jetson 녹화, host 처리)**: 스캔용 팔 자세(카메라 수평 근처)로 원본 color/depth/camera_info + /scan + /tf(_static)
  + /joint_states + /odom을 bag으로 녹화(`tools/scan/`). Nav2 끈 상태, 0.05~0.08 m/s. 위치는 odom(open-loop)을 믿지 않고
  host에서 RTAB-Map(RGB-D/ICP 오도메트리 + 루프 클로저)으로 추정 → Open3D TSDF로 메쉬.
- **Phase 3 — Blender(host, 사용자)**: 정리·텍스처·감량, visual/collision 분리. 결과는 git(LFS)으로 공유:
  `src/jetrover_gazebo/models/room_lap2/`(규칙은 그 README).
- **좌표 정합**: 메쉬의 LiDAR 높이 단면을 SLAM 지도와 2D ICP로 맞춰 T_map←scan과 잔차를 낸다(`tools/scan/validate_room_alignment.py`).
  목표: 주요 벽 기준 잔차 중앙값 ≤ 5 cm. 정합 후에야 A/B 등 지도 좌표를 시뮬레이션에서 재사용.
- **Phase 4 — Sim-to-Real**: 같은 시작/목표로 Nav2(MPPI/DWB)·LiDAR·depth 장애물 결과를 실기와 비교.
- 비범위: 3DGS(후순위), Isaac Sim(host GPU 사양 부족 추정), 실시간 트윈 동기화.
