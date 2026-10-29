#!/usr/bin/env bash
# 한글: host에서 Gazebo(깊이 장애물) + Nav2(컨트롤러 선택, auto_localize:=false)를 띄우고 avoid_trials.py로 회피 주행 시험을 반복한다.
#       끝나면 프로세스 그룹을 종료한다. 실기 로봇은 쓰지 않는다. 사용: CTRL=dwb SCEN=S2 REPEATS=5 bash tools/sim/sim_avoid_run.sh
# Host: Gazebo (depth obstacles) + Nav2 with the chosen controller, then tools/sim/avoid_trials.py.
#   env: CTRL  dwb | mppi | mppi_nolr | <path to a params yaml>   (default dwb = nav2_params.yaml)
#        TAG   label in the CSV (default = CTRL)     SCEN S1|S2|S4|all|D1..D12|N50|dyn or a comma list (default S2)     REPEATS (default 3)
#        APPROACH 1: also run the precise approach node and call it after Nav2
#        TIMEOUT wall-clock seconds per leg (default 90; a blocked goal with the precise BT needs ~200)
#        BT  NavigateToPose.behavior_tree for each goal (starts the precise approach node; the BT calls it)
#        APPROACH_ARGS extra --ros-args for that node, e.g. '-p max_start_dist_m:=0.0' to force a failure (9.5 retry check)
#        GTLOC 1 (default) ground-truth localization / 0 AMCL   GTNOISE position error sigma m for GTLOC=1
#        RUNCMD command to run instead of the trials   PARAMS extra Nav2 params file overriding CTRL   GUI=true to show Gazebo   LOGDIR (default /tmp)
source /opt/ros/jazzy/setup.bash; source ~/jetrover_ws/install/setup.bash
CTRL=${CTRL:-dwb}; TAG=${TAG:-$CTRL}; LOGDIR=${LOGDIR:-/tmp}
case "$CTRL" in
  dwb) PF="" ;;
  mppi|mppi_nolr|mppi_nodb) PF="params_file:=$HOME/jetrover_ws/tools/nav/ab_params/nav2_params_${CTRL}.yaml" ;;
  *) PF="params_file:=$CTRL" ;;
esac
[ -n "${PARAMS:-}" ] && PF="params_file:=$PARAMS"
export ROS_DOMAIN_ID=31 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST GZ_IP=127.0.0.1 GZ_PARTITION=avoid$$
# 이전 실행이 남아 있으면(같은 ROS 도메인의 노드 이름 충돌로 Nav2가 안 뜨거나 결과가 오염됨) 시작하지 않는다(2026-10-22).
# Refuse to start over leftovers of an earlier run (duplicate node names in the same domain broke the Nav2 bringup).
LEFT=$(ps -eo args | grep -cE '^(gz sim|/opt/ros/jazzy/lib/nav2_|/opt/ros/jazzy/lib/ros_gz_bridge/parameter_bridge)')
if [ "$LEFT" != 0 ]; then echo "leftover simulation/Nav2 processes: $LEFT - stop them first"; exit 1; fi
set -m
G=""; BR=""; N=""; L=""; AP=""; W=""
# 정리: 외부 timeout/Ctrl-C로 끊겨도 실행된다(trap). 2026-10-22: timeout으로 래퍼만 죽어 Gazebo·Nav2·브리지가 남았었다.
# Cleanup also runs when the wrapper is interrupted (an outer `timeout` used to leave Gazebo, Nav2 and bridges behind).
cleanup() {
  trap - EXIT INT TERM
  [ -n "$W" ] && kill -INT -- -$W 2>/dev/null
  [ -n "$AP" ] && { kill -INT -- -$AP 2>/dev/null; sleep 2; kill -KILL -- -$AP 2>/dev/null; }
  [ -n "$L" ] && kill -INT $L 2>/dev/null
  [ -n "$BR" ] && kill -INT -- -$BR 2>/dev/null
  [ -n "$N" ] && kill -INT -- -$N 2>/dev/null
  [ -n "$G" ] && kill -INT -- -$G 2>/dev/null
  sleep 10
  for g in $W $AP $BR $N $G; do kill -TERM -- -$g 2>/dev/null; done; sleep 3
  for g in $W $AP $BR $N $G; do kill -KILL -- -$g 2>/dev/null; done
  echo "gz left: $(ps -eo args | grep -c '^gz sim')"
}
trap cleanup EXIT
trap 'exit 130' INT TERM
ros2 launch jetrover_gazebo sim.launch.py world:=room_lap2_objects.sdf gui:=${GUI:-false} depth_obstacles:=true \
  x:=1.02 y:=0.37 yaw:=1.449 > $LOGDIR/av_gz.log 2>&1 &
G=$!; sleep 40
# 동적 장애물(8.16) 구동용 set_pose 서비스 브리지. 정지 상자 시험엔 쓰이지 않지만 항상 띄워 둔다(가벼움).
# set_pose service bridge for the dynamic-obstacle driver (unused by the static scenarios, always started: cheap).
ros2 run ros_gz_bridge parameter_bridge /world/jetrover_room/set_pose@ros_gz_interfaces/srv/SetEntityPose > $LOGDIR/av_bridge.log 2>&1 &
BR=$!
# Nav2가 정말 준비됐는지 확인한다(2026-10-19): 시작할 때 라이프사이클 전환이 시간 초과돼 지도를 못 받는 실행이 있었고, 그러면
# 플래너가 "Costmap timed out waiting for update"만 내서 시험 결과가 로봇 동작이 아니라 시작 실패에 오염된다. 안 되면 한 번 재시작.
# Wait until Nav2 is really up; one startup race left the global costmap without a map. Restart once if needed.
nav2_ready() {
  for i in $(seq 40); do
    ok=1
    for n in map_server amcl planner_server controller_server bt_navigator; do
      st=$(timeout 5 ros2 lifecycle get /$n 2>/dev/null | head -1)
      [ "${st%% *}" = active ] || ok=0
    done
    if [ $ok = 1 ] && timeout 10 ros2 topic echo --once --field info.width /global_costmap/costmap >/dev/null 2>&1; then return 0; fi
    sleep 3
  done
  return 1
}
N=""
for attempt in 1 2; do
  ros2 launch jetrover_navigation nav2.launch.py use_sim_time:=true auto_localize:=false precise_approach:=false $PF > $LOGDIR/av_nav.log 2>&1 &
  N=$!
  if nav2_ready; then echo "Nav2 ready (attempt $attempt)"; break; fi
  echo "Nav2 not ready after attempt $attempt"; kill -INT -- -$N 2>/dev/null; sleep 8; kill -KILL -- -$N 2>/dev/null; N=""
done
if [ -z "$N" ]; then
  echo "Nav2 failed to start"; exit 1
fi
sleep 5
cd ~/jetrover_ws
# 정답 위치 추정(기본 켬): AMCL이 스캔 월드에서 회전 뒤 12~24 cm 어긋나서(troubleshooting/046) 회피 평가를 가린다. GTLOC=0이면 AMCL.
# Ground-truth localization (default on): AMCL drifts 12-24 cm after a rotation in the scan world. GTLOC=0 keeps AMCL; GTNOISE=m adds error.
if [ "${GTLOC:-1}" = 1 ]; then
  ros2 param set /amcl tf_broadcast false > $LOGDIR/av_gtloc.log 2>&1
  python3 tools/sim/gt_localization.py --noise "${GTNOISE:-0}" >> $LOGDIR/av_gtloc.log 2>&1 &
  L=$!; sleep 4
fi
if [ "${APPROACH:-0}" = 1 ] || [ -n "${BT:-}" ]; then
  # BT(정밀 도착 BT 파일)를 주면 그 BT가 이 노드를 부른다 / the precise-arrival BT calls this node
  # relocalize 끔: sim은 정답 위치를 쓴다(스캔 매칭 재위치는 실기 AMCL용) / sim uses ground-truth localization
  ros2 run jetrover_navigation precise_approach.py --ros-args -p use_sim_time:=true -p relocalize:=false ${APPROACH_ARGS:-} > $LOGDIR/av_approach.log 2>&1 &
  AP=$!; sleep 4
fi
# 시험은 백그라운드로 돌리고 wait: 전경 명령 중엔 bash가 신호(trap)를 늦게 처리한다. / run in the background so traps fire promptly
# 서브셸로 감싸 $!가 프로세스 그룹 리더가 되게 한다 / subshell so that $! is the process-group leader
(
if [ -n "${RUNCMD:-}" ]; then bash -c "$RUNCMD" 2>&1 | grep -v "^\s*$"        # e.g. RUNCMD='python3 tools/sim/amcl_drift_check.py --spin --drive'
else python3 tools/sim/avoid_trials.py run --tag "$TAG" --scenario "${SCEN:-S2}" --repeats "${REPEATS:-3}" --timeout "${TIMEOUT:-90}" $([ "${APPROACH:-0}" = 1 ] && echo --approach) $([ -n "${BT:-}" ] && echo --bt "$BT") 2>&1 | grep -v "^\s*$"; fi
) &
W=$!
wait $W
