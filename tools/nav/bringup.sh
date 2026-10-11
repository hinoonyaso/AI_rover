#!/usr/bin/env bash
# 한글: 실기 시험용 스택(로봇 → 카메라 → Nav2)을 순서대로 띄우고, 고정 시간 대신 "준비 신호"(로그 줄)가 나오면 바로 다음 단계로 간다.
#       2026-10-11: 고정 대기(40/25/60 s)로 3분 가까이 걸렸지만 실제 준비는 로봇 7.5 s, Nav2 6.1 s였다.
# Start robot -> camera -> Nav2 and move on as soon as each one logs that it is ready (no fixed sleeps).
# Usage: tools/nav/bringup.sh [nav2 params file]      Logs: $LOGDIR (default /tmp/jetrover_bringup)
# Stop: tools/nav/stop_nav2.sh, then Ctrl+C / SIGINT the robot and camera launches (see AGENTS.md: no pkill -f here).
set -u
cd ~/jetrover_ws
source install/setup.bash
LOGDIR=${LOGDIR:-/tmp/jetrover_bringup}
mkdir -p "$LOGDIR"
PARAMS=${1:-}

wait_for() {  # wait_for <log> <regex> <timeout s> <label>
  local t0=$SECONDS
  until grep -qE "$2" "$1" 2>/dev/null; do
    if (( SECONDS - t0 > $3 )); then echo "TIMEOUT: $4 ($3 s) -- see $1"; return 1; fi
    sleep 0.5
  done
  echo "ready: $4 ($((SECONDS - t0)) s)"
}

t_all=$SECONDS
nohup ros2 launch jetrover_bringup robot.launch.py arm_command_enabled:=true arm_move_home_on_start:=true \
  > "$LOGDIR/robot.log" 2>&1 &
wait_for "$LOGDIR/robot.log" 'current scan mode' 30 'LiDAR scanning' || exit 1
wait_for "$LOGDIR/robot.log" 'arm reached home pose' 40 'arm home pose' || exit 1

nohup ros2 launch jetrover_perception camera.launch.py colorizer:=false > "$LOGDIR/camera.log" 2>&1 &
wait_for "$LOGDIR/camera.log" 'Publishing|publishing|stream' 40 'camera' || exit 1

if [ -n "$PARAMS" ]; then
  nohup ros2 launch jetrover_navigation nav2.launch.py params_file:="$PARAMS" > "$LOGDIR/nav2.log" 2>&1 &
else
  nohup ros2 launch jetrover_navigation nav2.launch.py > "$LOGDIR/nav2.log" 2>&1 &
fi
wait_for "$LOGDIR/nav2.log" 'lifecycle_manager_navigation.*Managed nodes are active' 60 'Nav2 active' || exit 1
wait_for "$LOGDIR/nav2.log" 'scan_match_init.*(AMCL now|NOT confident|not localizing)' 30 'start localization' || true
grep -E 'scan_match_init.*(AMCL now|NOT confident)' "$LOGDIR/nav2.log" | tail -1 | sed 's/.*scan_match_init\]: /  localization: /'
python3 tools/nav/ready_check.py
echo "bringup total $((SECONDS - t_all)) s"
