#!/bin/bash
# Record available ROS topics without starting or commanding the robot.
# 한글: 로봇을 기동·제어하지 않고 ROS 토픽만 기록한다.
set -euo pipefail
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-25}"
record_root="$HOME/.local/share/jetinspect-ops/bags"
mkdir -p "$record_root"
exec ros2 bag record -o "$record_root/$(date +%Y%m%d-%H%M%S)" /cmd_vel /odom /imu/data_raw /scan /tf /tf_static /battery_state /diagnostics
