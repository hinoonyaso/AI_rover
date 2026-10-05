#!/bin/bash
# Launches everything the remote host's RViz needs: base+EKF+LiDAR, Nav2
# (localization+navigation), and the RGB-D camera. Run this in the foreground
# on the Jetson; Ctrl+C stops all three launches cleanly.
#
# Needs FASTRTPS_DEFAULT_PROFILES_FILE set (normally already in ~/.bashrc,
# troubleshooting/018) -- set explicitly here too so this also works from a
# non-interactive shell.
set -e

cd ~/jetrover_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash

export ROS_DOMAIN_ID=25
export FASTRTPS_DEFAULT_PROFILES_FILE=~/jetrover_ws/setup/fastdds_wifi_only.xml

# Each ros2 launch spawns many child node processes that a plain `kill` on the
# launch PID does not reach (troubleshooting/017). setsid puts each launch in
# its own process group so Ctrl+C can kill the whole group, not just the
# wrapper process.
pgids=()
cleanup() {
  echo "stopping..."
  for pgid in "${pgids[@]}"; do
    kill -TERM -- "-$pgid" 2>/dev/null
  done
  sleep 2
  for pgid in "${pgids[@]}"; do
    kill -KILL -- "-$pgid" 2>/dev/null
  done
}
trap cleanup EXIT INT TERM

setsid ros2 launch jetrover_bringup robot.launch.py &
pgids+=($!)
sleep 6

setsid ros2 launch jetrover_navigation nav2.launch.py &
pgids+=($!)
sleep 3

setsid ros2 launch jetrover_perception camera.launch.py &
pgids+=($!)

echo "all launched (base/EKF/LiDAR, Nav2, camera). Ctrl+C to stop everything."
wait
