#!/usr/bin/env bash
# 한글: (host) room_lap2_objects.sdf를 팔 시험 자리에 헤드리스로 띄워 큐브 집기 시험(sim_pick_check.py) 후 끈다.
#       실기와 섞이지 않게 ROS_DOMAIN_ID=31, gz는 loopback + 실행마다 다른 partition(troubleshooting/040).
# (host) Headless pick-and-lift check at the arm-test spawn, then shut everything down.
#
# Usage: tools/sim/sim_pick_check.sh [red|green|blue ...]   (default: all three, each in a fresh simulation)
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
source /opt/ros/jazzy/setup.bash
source "$HOME/jetrover_ws/install/setup.bash"
set -u
set -m
export ROS_DOMAIN_ID=31 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST GZ_IP=127.0.0.1
URDF=$(mktemp --suffix=.urdf)
xacro "$(ros2 pkg prefix jetrover_gazebo)/share/jetrover_gazebo/urdf/jetrover_sim.urdf.xacro" \
  sim_mode:=true controllers_file:=x > "$URDF"
CUBES=("$@")
[ ${#CUBES[@]} -eq 0 ] && CUBES=(red green blue)
FAIL=0
for c in "${CUBES[@]}"; do
  export GZ_PARTITION=pick_${c}_$$
  ros2 launch jetrover_gazebo sim.launch.py world:=room_lap2_objects.sdf gui:=false \
    x:=0.45 y:=0.75 yaw:=1.5708 > "/tmp/sim_pick_${c}.log" 2>&1 &
  LPID=$!
  sleep 45
  # arm_hold가 홈 자세를 계속 보내므로 멈춘다(패턴을 나눠 써서 이 셸 자신은 안 잡힘)
  # stop arm_hold (pattern split so pgrep never matches this shell)
  AH=$(pgrep -f "jetrover_gazebo/arm_""hold.py" || true)
  [ -n "$AH" ] && kill $AH
  timeout 120 python3 "$HERE/sim_pick_check.py" "$URDF" "$c" || FAIL=1
  kill -INT -- -$LPID || true
  sleep 10
  kill -TERM -- -$LPID 2>/dev/null || true
  sleep 3
  kill -KILL -- -$LPID 2>/dev/null || true
  wait $LPID 2>/dev/null || true
done
rm -f "$URDF"
exit $FAIL
