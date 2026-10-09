#!/usr/bin/env bash
# 한글: 방 3D 스캔용 rosbag 녹화(Jetson). 원본 color/depth/camera_info + LiDAR + TF + 관절 + odom + IMU.
#       Nav2는 끄고(robot.launch + camera.launch colorizer:=false만), 팔은 스캔 자세, 0.05~0.08 m/s로 천천히.
# Usage: record_room_scan.sh [name]   -> bags/room_scan/<name>_<date>/ (mcap, 2 GB 단위 분할)
set -euo pipefail
name=${1:-room}
out="bags/room_scan/${name}_$(date +%Y%m%d_%H%M%S)"
topics="/depth_cam/color/image_raw /depth_cam/color/camera_info /depth_cam/depth/image_raw \
/depth_cam/depth/camera_info /scan /tf /tf_static /joint_states /odom /imu/data_raw"
free=$(df --output=avail -BG . | tail -1 | tr -dc 0-9)
[ "$free" -lt 20 ] && { echo "less than 20 GB free" >&2; exit 1; }
for t in /depth_cam/depth/image_raw /depth_cam/color/image_raw /scan; do
  timeout 5 ros2 topic hz "$t" 2>/dev/null | grep -m1 average | sed "s|^|$t |" || echo "WARN: no $t"
done
mkdir -p bags/room_scan
echo "recording to $out (Ctrl+C to stop) ..."
ros2 bag record -s mcap --max-bag-size 2000000000 -o "$out" $topics
