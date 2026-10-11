#!/usr/bin/env bash
# 한글: 실기 시험용 스택(로봇 → 카메라 → Nav2)을 순서대로 띄우고, 고정 대기 대신 "준비 신호"(로그 줄)가 나오면 바로 다음 단계로 간다.
#       끝에 ready_check.py(종료 코드 Ready Gate)를 돌린다. 실패하면 이 스크립트가 시작한 프로세스를 정리한다(위치 초기화만 미완이면 유지).
#       robot.launch는 arm_move_home_on_start:=true라서 팔이 실제로 움직인다 → 확인을 받는다(--yes로 생략).
# Start robot -> camera -> Nav2, wait for each one's ready log line, then run the ready gate.
# Usage: tools/nav/bringup.sh [--yes] [--expect-goal-tol 0.10] [nav2 params file]     Logs: $LOGDIR (default /tmp/jetrover_bringup)
# Exit: 0 ready; 1 a stage failed (started launches are stopped); 2 only the localisation is missing (everything left running).
# Stop: tools/nav/stop_nav2.sh, then SIGINT the robot/camera launches (see AGENTS.md: no pkill -f in the launching call).
cd ~/jetrover_ws
source install/setup.bash   # before `set -u`: ROS setup scripts read unset variables
set -u
LOGDIR=${LOGDIR:-/tmp/jetrover_bringup}
mkdir -p "$LOGDIR"
YES=0; EXPECT=""; PARAMS=""
while [ $# -gt 0 ]; do
  case "$1" in
    --yes) YES=1 ;;
    --expect-goal-tol) EXPECT="$2"; shift ;;
    *) PARAMS="$1" ;;
  esac
  shift
done

# 중복 기동 방지 / refuse to start on top of a running stack (duplicate node names break lifecycle bring-up)
running=$(pgrep -x -l 'base_node|ekf_node|controller_server|planner_server|amcl|bt_navigator' 2>/dev/null | tr '\n' ' ')
if [ -n "$running" ]; then
  echo "REFUSED: already running: $running"
  echo "  stop first: tools/nav/stop_nav2.sh, then SIGINT the 'ros2 launch jetrover_bringup/jetrover_perception' processes"
  exit 1
fi

if [ "$YES" -ne 1 ]; then
  echo "The arm will MOVE to the home pose (arm_move_home_on_start). Clear the space around the arm and be at the power switch."
  read -r -p "Continue? [y/N] " ans
  case "$ans" in y|Y) ;; *) echo "aborted"; exit 1 ;;
  esac
fi

PIDS=()
cleanup_on_failure() {
  echo "bringup failed -- stopping what this script started"
  bash tools/nav/stop_nav2.sh >/dev/null 2>&1 || true
  for p in "${PIDS[@]}"; do kill -INT "$p" 2>/dev/null || true; done
}

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
PIDS+=($!)
wait_for "$LOGDIR/robot.log" 'current scan mode' 30 'LiDAR scanning' || { cleanup_on_failure; exit 1; }
wait_for "$LOGDIR/robot.log" 'arm reached home pose' 40 'arm home pose' || { cleanup_on_failure; exit 1; }

nohup ros2 launch jetrover_perception camera.launch.py colorizer:=false > "$LOGDIR/camera.log" 2>&1 &
PIDS+=($!)
wait_for "$LOGDIR/camera.log" 'Enable color stream|Enable depth stream' 40 'camera' || { cleanup_on_failure; exit 1; }

if [ -n "$PARAMS" ]; then
  nohup ros2 launch jetrover_navigation nav2.launch.py params_file:="$PARAMS" > "$LOGDIR/nav2.log" 2>&1 &
else
  nohup ros2 launch jetrover_navigation nav2.launch.py > "$LOGDIR/nav2.log" 2>&1 &
fi
PIDS+=($!)
wait_for "$LOGDIR/nav2.log" 'lifecycle_manager_navigation.*Managed nodes are active|Aborting bringup' 60 'Nav2 bring-up' \
  || { cleanup_on_failure; exit 1; }
if grep -q 'Aborting bringup' "$LOGDIR/nav2.log"; then
  echo "Nav2 bring-up aborted:"; grep -E 'ERROR' "$LOGDIR/nav2.log" | tail -3 | cut -c1-200
  cleanup_on_failure; exit 1
fi
wait_for "$LOGDIR/nav2.log" 'scan_match_init.*(AMCL now|NOT confident|not localizing)' 30 'start localisation attempt' || true
grep -E 'scan_match_init.*(AMCL now|NOT confident|not localizing)' "$LOGDIR/nav2.log" | tail -1 \
  | sed 's/.*scan_match_init\]: /  localisation attempt: /'

GATE_ARGS=()
[ -n "$EXPECT" ] && GATE_ARGS+=(--expect-goal-tol "$EXPECT")
if python3 tools/nav/ready_check.py "${GATE_ARGS[@]}"; then
  echo "bringup total $((SECONDS - t_all)) s"
  exit 0
fi
# Everything but the localisation is fine? (the robot may simply not be on the start mark yet: run_trial.py scan-matches it)
if python3 tools/nav/ready_check.py --no-loc "${GATE_ARGS[@]}" >/dev/null 2>&1; then
  echo "Only the localisation is missing: place the robot on the start mark (run_trial.py scan-matches the start). Stack left running."
  echo "bringup total $((SECONDS - t_all)) s"
  exit 2
fi
cleanup_on_failure
exit 1
