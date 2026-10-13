#!/usr/bin/env bash
# 한글: (host) 녹화한 bag을 재생하며 RTAB-Map으로 포즈 그래프를 만든다. 결과: <out>/rtabmap.db.
#       로봇 odom(TF odom->base_footprint)은 초기값, 2D LiDAR ICP로 이웃 링크 보정, 시각 루프 클로저로 누적 오차 보정.
#       다른 ROS 장치와 섞이지 않게 ROS_DOMAIN_ID=88 + localhost 전용으로 돈다(host 기본 25/SUBNET에 bag의 /tf를 뿌리지 않는다).
# (host) Replay the recorded bag through RTAB-Map. Isolated DDS domain so the replayed /tf never reaches the robot network.
#
# Usage: tools/scan/host_rtabmap.sh <bag_dir> <out_dir> [play_rate]
set -e
BAG=${1:?bag dir}
OUT=${2:?out dir}
RATE=${3:-0.5}
source /opt/ros/jazzy/setup.bash
set -u
# 비대화형 셸의 백그라운드 작업은 SIGINT를 무시하므로(2026-10-14 시험에서 rtabmap이 안 꺼짐) job control로 별도 프로세스 그룹에 띄운다.
# Background jobs of a non-interactive shell ignore SIGINT: use job control so the launch gets its own process group.
set -m
export ROS_DOMAIN_ID=88
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)

# 키프레임을 촘촘히(5 cm / 0.05 rad, 2 Hz) — 나중에 TSDF에 쓸 이미지가 노드마다 저장된다.
# Dense keyframes: every node keeps its RGB-D frame for the TSDF step.
ros2 launch rtabmap_launch rtabmap.launch.py use_sim_time:=true \
  rgb_topic:=/depth_cam/color/image_raw depth_topic:=/depth_cam/depth/image_raw \
  camera_info_topic:=/depth_cam/color/camera_info \
  frame_id:=base_footprint odom_frame_id:=odom \
  subscribe_scan:=true scan_topic:=/scan \
  visual_odometry:=false icp_odometry:=false \
  approx_sync:=true approx_sync_max_interval:=0.05 topic_queue_size:=30 queue_size:=30 \
  rtabmap_viz:=false rviz:=false wait_for_transform:=1.0 \
  database_path:="$OUT/rtabmap.db" \
  rtabmap_args:="--delete_db_on_start --Reg/Strategy 1 --Reg/Force3DoF true \
    --RGBD/NeighborLinkRefining true --RGBD/ProximityBySpace true \
    --RGBD/LinearUpdate 0.05 --RGBD/AngularUpdate 0.05 --Rtabmap/DetectionRate 2 \
    --Icp/VoxelSize 0.02 --Icp/MaxCorrespondenceDistance 0.1 --Icp/PointToPlane false \
    --Mem/STMSize 30" \
  > "$OUT/rtabmap.log" 2>&1 &
LPID=$!
sleep 8
ros2 bag play "$BAG" --clock --rate "$RATE" \
  --topics /depth_cam/color/image_raw /depth_cam/depth/image_raw /depth_cam/color/camera_info \
           /scan /tf /tf_static /odom > "$OUT/play.log" 2>&1
sleep 5
kill -INT -- -$LPID
wait $LPID || true
ls -la "$OUT/rtabmap.db"
