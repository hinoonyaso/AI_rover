# tools/scan — 방 3D 스캔과 지도 정합 (prd/gazebo-sim.md Phase 2~3)

신뢰 수준: **계획**(도구는 L0 검증, 실제 스캔·host 처리는 미실시 — host 단계 명령은 처음 돌릴 때 조정 필요).

## 1. 녹화 (Jetson)
1. `robot.launch.py arm_command_enabled:=true`(+ 홈 이동), `camera.launch.py colorizer:=false`. **Nav2는 띄우지 않는다**(CPU).
   AMCL만 필요하면 `localization.launch.py`(지도 좌표 초기값으로 쓸 수 있음).
2. 팔을 **스캔 자세**로(`tools/perception/arm_set_joint.py`, 값은 아래 "스캔 자세"). 이때 장애물 depth 게이트는 닫히지만 녹화와 무관.
3. `tools/scan/record_room_scan.sh room1` → `bags/room_scan/room1_<날짜>/`(mcap, 2 GB 분할). 원본 15~30 Hz, 분당 약 1 GB(추정).
4. 키보드 텔레옵(`cmd_vel_timeout:=1.0`)으로 **0.05~0.08 m/s, 회전은 천천히**. 벽을 따라 한 바퀴 → 방 가운데에서 제자리 360°
   → 같은 곳 다시 지나가기(루프 클로저). 가구 모서리·문틀처럼 특징 있는 곳을 여러 번 보이게.
5. 끝나면 팔 홈 복귀. host로 복사: `scp -r bags/room_scan/room1_* <host>:~/scans/`.

## 2. 3D 복원 (host, RTAB-Map + Open3D)
- 설치: `sudo apt install ros-jazzy-rtabmap-ros`, `pip install open3d`.
- 로봇 odom은 open-loop라 믿지 않는다. RTAB-Map에 **초기값으로만** 주고 LiDAR ICP + 시각 특징 + 루프 클로저로 보정하게 한다(예시, 조정 필요):
  ```bash
  ros2 launch rtabmap_launch rtabmap.launch.py use_sim_time:=true \
    rgb_topic:=/depth_cam/color/image_raw depth_topic:=/depth_cam/depth/image_raw \
    camera_info_topic:=/depth_cam/color/camera_info frame_id:=base_footprint \
    subscribe_scan:=true scan_topic:=/scan visual_odometry:=false odom_topic:=/odom \
    approx_sync:=true rtabmap_args:="--delete_db_on_start --Reg/Strategy 2 --RGBD/NeighborLinkRefining true"
  ros2 bag play bags/room_scan/room1_* --clock
  ```
  (TF 트리의 depth 카메라는 팔 관절값으로 계산되므로 /tf, /tf_static, /joint_states가 bag에 있어야 한다.)
- 내보내기: rtabmap-databaseViewer → Export clouds/meshes(PLY, 미터). 또는 RTAB-Map 포즈 + 원본 RGB-D로 Open3D `ScalableTSDFVolume`
  (voxel 0.01, sdf_trunc 0.04)에서 메쉬 추출. 결과: `room.ply`(z-up, 바닥 z=0, 미터).

## 3. 지도와 정합 (host)
```bash
python3 tools/scan/validate_room_alignment.py room.ply maps/lap2_20261005.yaml --apply room_in_map.ply
```
메쉬를 LiDAR 높이(0.15~0.25 m)에서 잘라 SLAM 지도와 **점-선 ICP**로 맞춰 T_map←scan과 잔차를 출력(목표: 잔차 중앙값 ≤ 5 cm).
ICP 핵심(`align2d.py`)은 단위시험됨(`test_align2d.py`: 합성 방, 실제 지도에서 20 cm/8° 어긋남까지 1 cm/0.02° 이내 복구).
크게 어긋나면 `--init X Y YAW_DEG`로 대략값을 준다.

## 4. Blender → Gazebo (host, 사용자)
`room_in_map.ply`를 정리해 `src/jetrover_gazebo/models/room_lap2/`의 규칙(README)대로 visual/collision 내보내기 → Git LFS로 커밋.
월드: `python3 src/jetrover_gazebo/scripts/map_to_world.py maps/lap2_20261005.yaml src/jetrover_gazebo/worlds/room_lap2.sdf --room-model room_lap2 --no-walls`.

## 스캔 자세
2026-10-10 결정(측정 비교: `docs/benchmarks/perception/scan_pose_20261010.md`): 카메라 높이 0.52 m, 아래로 약 6°.
```
# 홈 -> 스캔 자세 (팔이 움직임, 이 순서대로: 이동 중 카메라 높이 >= 0.26 m)
python3 tools/perception/arm_set_joint.py joint4 1.5
python3 tools/perception/arm_set_joint.py joint2 -0.15
python3 tools/perception/arm_set_joint.py joint3 0.30
# 스캔 자세 -> 홈 (역순)
python3 tools/perception/arm_set_joint.py joint3 1.6629
python3 tools/perception/arm_set_joint.py joint2 -0.6618
python3 tools/perception/arm_set_joint.py joint4 1.45
```
팔을 세운 상태라 무게중심이 높다 — 0.05~0.08 m/s 텔레옵만. 이 자세에선 depth 장애물 게이트가 닫힌다.
