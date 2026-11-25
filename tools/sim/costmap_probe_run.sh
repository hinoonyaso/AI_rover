#!/bin/bash
# Host: dashboard world + sim Nav2 variant + set_pose bridge, then costmap_probe.py with the given
# arguments (e.g. --robot 0.95 1.42 -79 --points 0.95,1.42 --half 0.3). Cleans up its groups.
# 한글: 호스트에서 대시보드 월드 + 시뮬 Nav2 + set_pose 브리지를 띄우고 costmap_probe.py를 실행한 뒤 정리한다.
#   bash tools/sim/costmap_probe_run.sh --robot X Y YAW_DEG --points X,Y [...]
cd "$(dirname "$0")/../.."
PARAMS=${PARAMS:-tools/nav/ab_params/nav2_params_sim_tol05.yaml}
unset PYTHONPATH
source /opt/ros/jazzy/setup.bash; source install/setup.bash
export ROS_DOMAIN_ID=31 GZ_IP=127.0.0.1 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
LOG=${LOG:-/tmp/costmap_probe}; mkdir -p "$LOG"
P=$(python3 -c "
import sys,yaml,pathlib; sys.path.insert(0,'tools/mission')
import gazebo_managed_session as g
c=g.workspace_paths(yaml.safe_load(open('$PARAMS'))); p=pathlib.Path('$LOG')/'params.yaml'; p.write_text(yaml.safe_dump(c,sort_keys=False)); print(p)")
G=""; B=""; N=""
cleanup() { for g in $N $B $G; do kill -INT -- -$g 2>/dev/null; done; sleep 5; for g in $N $B $G; do kill -KILL -- -$g 2>/dev/null; done
  echo "gz left: $(ps -eo args | grep -c '^gz sim')"; }
trap cleanup EXIT
setsid ros2 launch jetrover_gazebo sim.launch.py gui:=false depth_obstacles:=true > "$LOG/gz.log" 2>&1 & G=$!
sleep 35
setsid ros2 run ros_gz_bridge parameter_bridge /world/jetrover_room/set_pose@ros_gz_interfaces/srv/SetEntityPose > "$LOG/br.log" 2>&1 & B=$!
setsid ros2 launch jetrover_navigation nav2.launch.py use_sim_time:=true auto_localize:=false precise_approach:=false params_file:=$P > "$LOG/nav.log" 2>&1 & N=$!
sleep 40
# PROBE_CMD overrides the probe (e.g. "python3 tools/nav/goal_clearance.py --live 1.30 0.40").
# 한글: PROBE_CMD를 주면 costmap_probe 대신 그 명령을 실행한다.
if [ -n "${PROBE_CMD:-}" ]; then timeout 150 bash -c "$PROBE_CMD"; else timeout 150 python3 tools/sim/costmap_probe.py "$@"; fi
