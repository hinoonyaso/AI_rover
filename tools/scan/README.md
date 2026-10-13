# tools/scan — 방 3D 스캔과 지도 정합 (prd/gazebo-sim.md Phase 2~3)

신뢰 수준: 녹화·host 처리·자동 에셋·Gazebo 확인 **실시**(2026-10-14 room1: 정합 잔차 중앙값 4.4 cm PASS, `docs/benchmarks/sim/room_scan_20261014.md`). Blender 수작업 정리는 미실시.

## 1. 녹화 (Jetson)
1. `robot.launch.py arm_command_enabled:=true`(+ 홈 이동), `camera.launch.py colorizer:=false`. **Nav2는 띄우지 않는다**(CPU).
   AMCL만 필요하면 `localization.launch.py`(지도 좌표 초기값으로 쓸 수 있음).
2. 팔을 **스캔 자세**로(`tools/perception/arm_set_joint.py`, 값은 아래 "스캔 자세"). 이때 장애물 depth 게이트는 닫히지만 녹화와 무관.
3. `tools/scan/record_room_scan.sh room1` → `bags/room_scan/room1_<날짜>/`(mcap, 2 GB 분할). 원본 15~30 Hz, 분당 약 1 GB(추정).
4. 키보드 텔레옵(`cmd_vel_timeout:=1.0`)으로 **0.05~0.08 m/s, 회전은 천천히**. 벽을 따라 한 바퀴 → 방 가운데에서 제자리 360°
   → 같은 곳 다시 지나가기(루프 클로저). 가구 모서리·문틀처럼 특징 있는 곳을 여러 번 보이게.
5. 끝나면 팔 홈 복귀. host로 복사: `rsync -a --partial bags/room_scan/room1_<날짜> sang@<host>:~/scans/`(12 GB, Wi-Fi로 약 1시간 — 끊겨도 이어받음).

## 2. 3D 복원 (host, RTAB-Map + Open3D)
- 설치(2026-10-14 결정: host의 Python 작업은 **uv 환경**에서 한다 — 시스템 Python에 `pip install` 하지 않는다):
  - RTAB-Map 단계(ROS 필요): `sudo apt install ros-jazzy-rtabmap-ros`, 시스템 ROS 환경(`source /opt/ros/jazzy/setup.bash`)에서 실행. apt 패키지라 uv로 설치되지 않는다.
  - Open3D 단계(TSDF, `validate_room_alignment.py`): ROS와 무관하므로 깨끗한 uv venv에서 실행.
    ```bash
    cd ~/scans && uv venv .venv && source .venv/bin/activate
    uv pip install "open3d==0.19.0" "numpy<2" scipy pyyaml
    ```
    **Open3D 0.19.0 고정**: 0.20.0(pip, numpy 2.5)은 `ScalableTSDFVolume`/tensor `VoxelBlockGrid`가 정상 RGB-D 한 장에서도
    빈 메쉬를 낸다(2026-10-14 host 확인, 같은 프레임이 0.19에선 5.8천 정점). (venv에서 ROS 파이썬 패키지가 필요하면
    `uv venv --system-site-packages` + ROS setup — 미검증.)
- 로봇 odom은 2026-10-11부터 엔코더+자이로 EKF다(E4/E5: 직진 1 m 오차 0.24 cm, 360° 회전 ±0.3°; 다만 4 m 사각형을 돌면 EKF는 원점 복귀 0.1~0.4 cm라고 믿는데 줄자로는 실제 3~5 cm·최대 4° 어긋남 — 메카넘 롤러 미끄러짐은 엔코더에 안 잡힌다). 방 한 바퀴(15~20 m, **추정**: 수십 cm까지 누적 가능)에서는 벽이 겹치므로 RTAB-Map에 **초기값으로**(TF odom→base_footprint) 주고 2D LiDAR ICP(이웃 링크 보정) + 시각 루프 클로저로 누적 오차를 보정하게 한다.
- 실행(2026-10-14 host에서 첫 조각으로 끝까지 확인):
  ```bash
  cd ~/scans
  tools/host_rtabmap.sh room1_<날짜> out 0.5        # bag 재생(0.5배속) + RTAB-Map -> out/rtabmap.db, ROS_DOMAIN_ID=88 localhost 격리
  source /opt/ros/jazzy/setup.bash && rtabmap-export --images_id --poses_camera --output_dir out/export out/rtabmap.db
  source .venv/bin/activate && python tools/tsdf_from_rtabmap.py out/export out/room.ply   # voxel 0.01, sdf_trunc 0.04, depth ≤ 3 m
  ```
  (host_rtabmap.sh/tsdf_from_rtabmap.py/align2d.py/validate_room_alignment.py는 이 폴더에서 `~/scans/tools/`로 복사해 쓴다.)
  TF: depth 카메라 위치는 팔 관절값으로 계산되고 카메라 드라이버가 자기 프레임을 `/tf`로 보낸다 — bag에 /tf, /tf_static 필요.
  결과 `room.ply`: RTAB-Map map 프레임(= 녹화 시작 시 odom), z-up, 바닥 z≈0, 미터.

(2026-10-14 첫 전체 처리: 노드 362, 메쉬 140만 삼각형 — `docs/benchmarks/sim/room_scan_20261014.md`.)

## 3. 지도와 정합 (host)
```bash
python3 tools/scan/validate_room_alignment.py room.ply maps/lap2_20261005.yaml --apply room_in_map.ply
```
메쉬를 LiDAR 높이(0.15~0.25 m)에서 잘라 SLAM 지도와 **점-선 ICP**로 맞춰 T_map←scan과 잔차를 출력(목표: 잔차 중앙값 ≤ 5 cm).
ICP 핵심(`align2d.py`)은 단위시험됨(`test_align2d.py`: 합성 방, 실제 지도에서 20 cm/8° 어긋남까지 1 cm/0.02° 이내 복구).
크게 어긋나면 `--init X Y YAW_DEG`로 대략값을 준다.

## 4. 자동 에셋 + Gazebo 확인 (host, 2026-10-14 실시)
```bash
cd ~/scans && source .venv/bin/activate
python tools/room_assets.py out/room_in_map.ply out/model --crop-map ~/jetrover_ws/maps/lap2_20261005.yaml
deactivate
~/.local/bin/blender -b --python tools/blender_ply_to_glb.py -- out/model/room_visual.ply out/model/meshes/room_visual.glb
cp out/model/meshes/* ~/jetrover_ws/src/jetrover_gazebo/models/room_lap2/meshes/
cd ~/jetrover_ws && python3 src/jetrover_gazebo/scripts/map_to_world.py maps/lap2_20261005.yaml \
  src/jetrover_gazebo/worlds/room_lap2.sdf --room-model room_lap2 --no-walls && colcon build --packages-select jetrover_gazebo
~/scans/tools/host_sim_check.sh room_lap2.sdf ~/scans/final_check 50   # 헤드리스: 컨트롤러, 토픽 Hz, 스캔, 카메라 1장, 0.1 m/s 3 s 주행
```
주의: Open3D가 쓴 glb는 Gazebo가 못 읽고, Blender glTF는 Z-up 그대로 내보내야 한다(troubleshooting/040). 시뮬레이션은 `GZ_IP=127.0.0.1`.

## 5. Blender 정리 → Gazebo (host, 사용자, 미실시)
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
