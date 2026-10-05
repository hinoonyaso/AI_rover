#!/usr/bin/env bash
# 한글: Jetson용 micro_ros_agent를 ~/jetrover_ws/uros_agent_ws에 소스 빌드한다.
# Builds the micro-ROS agent (Jetson side) from source into ~/jetrover_ws/uros_agent_ws (outside src/).
# After this:  source ~/jetrover_ws/uros_agent_ws/install/setup.bash
#              ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyACM0 -b 1000000
set -eo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
WS="${AGENT_WS:-$HOME/jetrover_ws/uros_agent_ws}"
export MAKEFLAGS="-j2"
export PATH="$HERE/shim:$PATH"
source /opt/ros/jazzy/setup.bash
source "$HERE/setup_ws/install/setup.bash"
mkdir -p "$WS" && cd "$WS"
[ -d src/micro-ROS-Agent ] || ros2 run micro_ros_setup create_agent_ws.sh
ros2 run micro_ros_setup build_agent.sh --parallel-workers 1
echo "agent ready: source $WS/install/setup.bash"
