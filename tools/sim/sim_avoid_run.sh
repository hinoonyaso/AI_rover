#!/usr/bin/env bash
# 한글: host에서 Gazebo(깊이 장애물) + Nav2(컨트롤러 선택, auto_localize:=false)를 띄우고 avoid_trials.py로 회피 주행 시험을 반복한다.
#       끝나면 프로세스 그룹을 종료한다. 실기 로봇은 쓰지 않는다. 사용: CTRL=dwb SCEN=S2 REPEATS=5 bash tools/sim/sim_avoid_run.sh
# Host: Gazebo (depth obstacles) + Nav2 with the chosen controller, then tools/sim/avoid_trials.py.
#   env: CTRL  dwb | mppi | mppi_nolr | <path to a params yaml>   (default dwb = nav2_params.yaml)
#        TAG   label in the CSV (default = CTRL)     SCEN S1|S2|S4|all (default S2)     REPEATS (default 3)
#        APPROACH 1: also run the precise approach node and call it after Nav2
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
set -m
ros2 launch jetrover_gazebo sim.launch.py world:=room_lap2_objects.sdf gui:=${GUI:-false} depth_obstacles:=true \
  x:=1.02 y:=0.37 yaw:=1.449 > $LOGDIR/av_gz.log 2>&1 &
G=$!; sleep 40
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
  ros2 launch jetrover_navigation nav2.launch.py use_sim_time:=true auto_localize:=false $PF > $LOGDIR/av_nav.log 2>&1 &
  N=$!
  if nav2_ready; then echo "Nav2 ready (attempt $attempt)"; break; fi
  echo "Nav2 not ready after attempt $attempt"; kill -INT -- -$N 2>/dev/null; sleep 8; kill -KILL -- -$N 2>/dev/null; N=""
done
if [ -z "$N" ]; then
  echo "Nav2 failed to start"; kill -INT -- -$G 2>/dev/null; sleep 8; kill -KILL -- -$G 2>/dev/null; echo "gz left: $(ps -eo args | grep -c '^gz sim')"; exit 1
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
if [ "${APPROACH:-0}" = 1 ]; then
  ros2 run jetrover_navigation precise_approach.py --ros-args -p use_sim_time:=true > $LOGDIR/av_approach.log 2>&1 &
  AP=$!; sleep 4
fi
if [ -n "${RUNCMD:-}" ]; then bash -c "$RUNCMD" 2>&1 | grep -v "^\s*$"        # e.g. RUNCMD='python3 tools/sim/amcl_drift_check.py --spin --drive'
else python3 tools/sim/avoid_trials.py run --tag "$TAG" --scenario "${SCEN:-S2}" --repeats "${REPEATS:-3}" $([ "${APPROACH:-0}" = 1 ] && echo --approach) 2>&1 | grep -v "^\s*$"; fi
[ -n "${AP:-}" ] && { kill -INT -- -$AP 2>/dev/null; sleep 2; kill -KILL -- -$AP 2>/dev/null; }
[ -n "${L:-}" ] && kill -INT $L 2>/dev/null
kill -INT -- -$N 2>/dev/null; kill -INT -- -$G 2>/dev/null; sleep 10
kill -TERM -- -$N -$G 2>/dev/null; sleep 3; kill -KILL -- -$N -$G 2>/dev/null
echo "gz left: $(ps -eo args | grep -c '^gz sim')"
