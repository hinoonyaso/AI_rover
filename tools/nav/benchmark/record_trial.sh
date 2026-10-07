#!/usr/bin/env bash
# 한글: Nav2 baseline 시험 1회분을 rosbag으로 기록하고 meta.json 틀을 만든다. 로봇은 움직이지 않는다(기록만).
# Usage: record_trial.sh <tag> <scenario A|B|C> <trial#> <goal_x> <goal_y> <goal_yaw_deg>
#   e.g. record_trial.sh baseline_openloop A 1 2.0 0.5 0
# Start this BEFORE sending the Nav2 goal (line_goal.py / RViz), stop with Ctrl+C after the robot stops,
# then edit meta.json (outcome, collision, recoveries, measured_final).
set -euo pipefail
[ $# -eq 6 ] || { sed -n 2,6p "$0"; exit 1; }
tag=$1; sc=$2; n=$(printf '%02d' "$3"); gx=$4; gy=$5; gyaw=$6
dir="bags/${tag}/trial_${sc}${n}"
[ -e "$dir" ] && { echo "$dir already exists" >&2; exit 1; }
mkdir -p "bags/${tag}"
# 한글: bag 폴더는 ros2 bag이 만들어야 해서 meta는 기록 후 옆에 둔다(폴더 생성 후 복사).
topics="/tf /tf_static /odom /amcl_pose /cmd_vel /cmd_vel_nav /cmd_vel_smoothed /joint_states /scan /plan /received_global_plan \
/depth_cam/depth/points_sparse /global_costmap/costmap /local_costmap/costmap /collision_monitor_state"
trap 'cat > "$dir/meta.json" <<JSON
{"scenario": "'"$sc"'", "trial": '"$((10#$n))"', "goal": {"x": '"$gx"', "y": '"$gy"', "yaw_deg": '"$gyaw"'},
 "outcome": "TODO success|fail|abort", "collision": false, "recoveries": 0,
 "measured_final": null, "notes": ""}
JSON
echo "meta template written: $dir/meta.json (edit it)"' EXIT
ros2 bag record -o "$dir" $topics
