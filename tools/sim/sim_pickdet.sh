#!/usr/bin/env bash
# 한글: host Gazebo에서 빨간 큐브를 (CX, CY, CYAW°)에 놓고, 카메라 검출만으로 집는다(pick_detected.py).
#       끝나면 프로세스 그룹을 종료한다. 실기 팔은 움직이지 않는다. 사용: CX=0.33 CY=1.02 CYAW=30 bash tools/sim/sim_pickdet.sh
# Host: put the red cube at (CX, CY, CYAW deg) in the Gazebo room, then pick it from the camera detection only.
#   env: CX, CY (world m, default 0.33 1.02), CYAW (deg, default 0), PICKARGS (extra pick_detected.py args), GUI=true to show Gazebo,
#        LOGDIR (default /tmp). Robot spawns at the arm-test spot (0.45, 0.75, yaw 90 deg).
source /opt/ros/jazzy/setup.bash; source ~/jetrover_ws/install/setup.bash
LOGDIR=${LOGDIR:-/tmp}
export ROS_DOMAIN_ID=31 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST GZ_IP=127.0.0.1 GZ_PARTITION=pickdet$$
set -m
ros2 launch jetrover_gazebo sim.launch.py world:=room_lap2_objects.sdf gui:=${GUI:-false} arm_mode:=moveit x:=0.45 y:=0.75 yaw:=1.5708 > $LOGDIR/pd_gz.log 2>&1 &
G=$!; sleep 40
QZ=$(python3 -c "import math;print(math.sin(math.radians(${CYAW:-0})/2))")
QW=$(python3 -c "import math;print(math.cos(math.radians(${CYAW:-0})/2))")
gz service -s /world/jetrover_room/set_pose --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 3000 \
  --req "name: \"object_1\", position: {x: ${CX:-0.33}, y: ${CY:-1.02}, z: 0.015}, orientation: {x: 0, y: 0, z: $QZ, w: $QW}" >/dev/null
# 같은 줄의 초록·파랑 큐브는 치운다(옆 큐브가 손가락을 막지 않게) / move the other cubes out of the way
for obj in "object_2 0.45 1.35" "object_3 0.55 1.35"; do set -- $obj
  gz service -s /world/jetrover_room/set_pose --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 3000 \
    --req "name: \"$1\", position: {x: $2, y: $3, z: 0.015}" >/dev/null
done
sleep 2; echo "red cube now (yaw ${CYAW:-0} deg): $(gz model -m object_1 -p | grep -A1 XYZ | tail -1)"
ros2 launch jetrover_manipulation move_group.launch.py mode:=real use_sim_time:=true > $LOGDIR/pd_mg.log 2>&1 &
M=$!; sleep 15
ros2 run jetrover_perception cube_detector.py --ros-args -p use_sim_time:=true > $LOGDIR/pd_det.log 2>&1 &
D=$!; sleep 4
cd $LOGDIR && timeout 300 python3 ~/jetrover_ws/tools/manipulation/pick_detected.py red --gripper sim $PICKARGS 2>&1 | grep -vE "^\s*$|QoS"
echo "red cube after: $(gz model -m object_1 -p | grep -A1 XYZ | tail -1)"
[ "${KEEP:-0}" = 1 ] && { echo "kept running (pgids $G $M, detector $D)"; exit 0; }
kill -INT -- -$D 2>/dev/null; kill -INT -- -$M 2>/dev/null; kill -INT -- -$G 2>/dev/null; sleep 10
kill -TERM -- -$D -$M -$G 2>/dev/null; sleep 3; kill -KILL -- -$D -$M -$G 2>/dev/null
echo "gz left: $(ps -eo args | grep -c '^gz sim')"
