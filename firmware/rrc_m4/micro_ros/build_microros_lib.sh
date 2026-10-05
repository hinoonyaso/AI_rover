#!/usr/bin/env bash
# 한글: micro-ROS 정적 라이브러리를 Jetson에서 직접 빌드한다(docker 권한 없음). 2 job으로 제한(메모리 보호).
# Builds libmicroros.a for the STM32F407 natively on the Jetson (no docker: the user is not in the docker group).
# Output: micro_ros/firmware/build/libmicroros.a and micro_ros/firmware/build/include/
# Heavy: clones ~40 repositories and compiles them. Limited to 2 jobs (AGENTS.md memory rule).
set -eo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
export MAKEFLAGS="-j2"
export PATH="$HERE/shim:$PATH:$HOME/.local/opt/stm32/bin"

source /opt/ros/jazzy/setup.bash

# 1) micro_ros_setup tooling (pinned in micro_ros/README.md)
if [ ! -f setup_ws/install/setup.bash ]; then
    mkdir -p setup_ws/src
    [ -e setup_ws/src/micro_ros_setup ] || ln -s "$HERE/setup_src" setup_ws/src/micro_ros_setup
    (cd setup_ws && colcon build --parallel-workers 1)
fi
source setup_ws/install/setup.bash

# 2) firmware workspace (downloads micro-ROS client stack)
if [ ! -d firmware/mcu_ws ]; then
    rm -rf firmware
    ros2 run micro_ros_setup create_firmware_ws.sh generate_lib
fi

# 3) cross build
ros2 run micro_ros_setup build_firmware.sh "$HERE/toolchain.cmake" "$HERE/colcon.meta"
ls -la firmware/build/libmicroros.a
