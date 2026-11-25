#!/bin/bash
# Host: Gazebo (dashboard world, depth obstacles) spawned at START + Nav2 with the sim variant
# (same DirStop/BT as the official real config), then wall_escape_probe.py. Cleans up its groups.
# 한글: 호스트에서 시작 자세에 로봇을 둔 Gazebo + Nav2(공식 실기와 같은 DirStop/BT의 시뮬 변형)를 띄우고
# wall_escape_probe.py를 실행한 뒤 프로세스 그룹을 정리한다.
#   bash tools/sim/wall_escape_run.sh "1.0 1.45 90" "1.0 0.95 90" [seconds] [params.yaml]
# (no set -u: the ROS setup scripts reference unset variables)
cd "$(dirname "$0")/../.."
START=($1); GOAL=($2); SECS=${3:-90}; PARAMS=${4:-tools/nav/ab_params/nav2_params_sim_tol05.yaml}
unset PYTHONPATH
source /opt/ros/jazzy/setup.bash; source install/setup.bash
export ROS_DOMAIN_ID=31 GZ_IP=127.0.0.1 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
LOG=${LOG:-/tmp/wall_escape}; mkdir -p "$LOG"
P=$(python3 -c "
import sys,yaml,pathlib; sys.path.insert(0,'tools/mission')
import gazebo_managed_session as g
c=g.workspace_paths(yaml.safe_load(open('$PARAMS'))); p=pathlib.Path('$LOG')/'params.yaml'; p.write_text(yaml.safe_dump(c,sort_keys=False)); print(p)")
yaw_rad=$(python3 -c "import math;print(math.radians(${START[2]}))")
G=""; N=""
cleanup() { for g in $N $G; do kill -INT -- -$g 2>/dev/null; done; sleep 5; for g in $N $G; do kill -KILL -- -$g 2>/dev/null; done
  echo "gz left: $(ps -eo args | grep -c '^gz sim')"; }
trap cleanup EXIT
setsid ros2 launch jetrover_gazebo sim.launch.py gui:=false depth_obstacles:=true x:=${START[0]} y:=${START[1]} yaw:=$yaw_rad > "$LOG/gz.log" 2>&1 & G=$!
sleep 35
setsid ros2 launch jetrover_navigation nav2.launch.py use_sim_time:=true auto_localize:=false precise_approach:=false params_file:=$P > "$LOG/nav.log" 2>&1 & N=$!
sleep 35
python3 tools/sim/wall_escape_probe.py --start ${START[@]} --goal ${GOAL[@]} --seconds "$SECS"
