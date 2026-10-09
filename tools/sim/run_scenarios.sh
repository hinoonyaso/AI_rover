#!/usr/bin/env bash
# 한글: Gazebo에서 Nav2 주행 시나리오를 반복 실행한다(host). 로봇을 시작점으로 순간이동(gz set_pose) + AMCL 초기 위치를 주고
#       tools/nav/straight_trial.py --goal로 1회씩 주행 → Log/wobble_trials_v3.csv. 컨트롤러는 Nav2를 띄울 때 고른다(아래 README).
# Run Nav2 driving scenarios in Gazebo (host only, ROS_DOMAIN_ID=31). Needs sim.launch.py (box world,
# depth_obstacles:=true) and nav2.launch.py use_sim_time:=true with the controller under test.
# Usage: tools/sim/run_scenarios.sh <ctrl_tag> [S1|S2|S3|all] [repeats]
#   S1 straight lane, no obstacle      (0.55,0.40) -> (0.55,1.40)            wobble baseline
#   S2 box round trip (box right 20 cm) A (1.02,0.37) <-> B (1.00,1.45)        = real F2 series; repeats round trips
#   S3 goal ~75 deg to the side        (0.47,0.52,-100 deg) -> (1.00,0.27)  = where real F2-4 stalled
# Summary per scenario at the end (success, mean time, max lateral, diag50_frac). Coordinates = map = world.
set -euo pipefail
ctrl=${1:?ctrl tag, e.g. dwb / mppi / mppi_nolr}
which=${2:-all}
reps=${3:-3}
cd "$(dirname "$0")/../.."
[ "${ROS_DOMAIN_ID:-}" = "31" ] || { echo "export ROS_DOMAIN_ID=31 first (keep away from the robot)" >&2; exit 1; }

teleport() {  # x y yaw_deg
  local x=$1 y=$2 yaw
  yaw=$(python3 -c "import math; print(math.radians($3))")
  local qz qw
  qz=$(python3 -c "import math; print(math.sin($yaw/2))"); qw=$(python3 -c "import math; print(math.cos($yaw/2))")
  gz service -s /world/jetrover_room/set_pose --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 3000 \
    --req "name: 'jetrover', position: {x: $x, y: $y, z: 0.01}, orientation: {z: $qz, w: $qw}" >/dev/null
  sleep 1
  ros2 topic pub --once /initialpose geometry_msgs/msg/PoseWithCovarianceStamped \
    "{header: {frame_id: map}, pose: {pose: {position: {x: $x, y: $y}, orientation: {z: $qz, w: $qw}},
      covariance: [0.0025,0,0,0,0,0, 0,0.0025,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0.003]}}" >/dev/null
  sleep 3   # AMCL settles / AMCL 수렴 대기
}
trial() {  # tag gx gy
  python3 tools/nav/straight_trial.py "$1" --goal "$2" "$3" --timeout 90 --bag || true
}

run_s1() { for i in $(seq "$reps"); do teleport 0.55 0.40 90; trial "SIM_${ctrl}_S1" 0.55 1.40; done; }
run_s2() {
  teleport 1.02 0.37 83
  for i in $(seq "$reps"); do trial "SIM_${ctrl}_S2_AB" 1.00 1.45; trial "SIM_${ctrl}_S2_BA" 1.02 0.37; done
}
run_s3() { for i in $(seq "$reps"); do teleport 0.47 0.52 -100; trial "SIM_${ctrl}_S3" 1.00 0.27; done; }

case "$which" in
  S1) run_s1 ;; S2) run_s2 ;; S3) run_s3 ;;
  all) run_s1; run_s2; run_s3 ;;
  *) sed -n 4,11p "$0"; exit 1 ;;
esac

python3 - "$ctrl" <<'PY'
import csv, sys, collections, math
ctrl = sys.argv[1]
rows = [r for r in csv.DictReader(open('Log/wobble_trials_v3.csv')) if r['tag'].startswith(f'SIM_{ctrl}_')]
by = collections.defaultdict(list)
for r in rows:
    by[r['tag']].append(r)
print(f'{"tag":26s} {"ok":>5s} {"time s":>7s} {"lat cm":>7s} {"yaw dev":>7s} {"diag50":>7s} {"vy flips/min":>12s}')
def mean(v):
    v = [float(x) for x in v if x not in ('', 'nan')]
    return sum(v) / len(v) if v else math.nan
for tag, rs in sorted(by.items()):
    ok = sum(r['status'] == 'succeeded' for r in rs)
    print(f'{tag:26s} {ok:>2d}/{len(rs):<2d} {mean(r["elapsed_s"] for r in rs):7.1f} '
          f'{max(float(r["lat_max_map_cm"]) for r in rs):7.1f} {mean(r["yaw_dev_max_deg"] for r in rs):7.1f} '
          f'{mean(r["diag50_frac"] for r in rs):7.3f} {mean(r["vy_flips_per_min"] for r in rs):12.1f}')
PY
