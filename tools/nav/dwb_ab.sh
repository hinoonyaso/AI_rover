#!/usr/bin/env bash
# 한글: Nav2 실행 중에 DWB 옆이동(vy)을 재시작 없이 켜고 끄는 A/B 시험 스위치(troubleshooting/031).
#       로봇을 움직이지 않는다 — 파라미터만 바꾼다. 실제 주행은 그 다음 line_goal.py/RViz로.
# Runtime A/B switch for DWB lateral motion (no Nav2 restart; these DWB kinematics params are dynamic).
# Usage: dwb_ab.sh show | vy_off | vy_on
#   vy_off : min/max_vel_y = 0 -> DWB behaves like a diff-drive (A/B diagnosis only, NOT a final setting)
#   vy_on  : back to nav2_params.yaml values (+-0.2)
# Run tools/nav/cmd_chain_monitor.py alongside and compare "vy-flips" and the path in RViz.
set -euo pipefail
node=/controller_server
p=FollowPath
case "${1:-show}" in
  show)
    for k in min_vel_y max_vel_y max_vel_x max_speed_xy min_speed_xy trajectory_generator_name; do
      printf '%-28s ' "$p.$k"; ros2 param get $node $p.$k
    done ;;
  vy_off)
    ros2 param set $node $p.min_vel_y 0.0
    ros2 param set $node $p.max_vel_y 0.0 ;;
  vy_on)
    ros2 param set $node $p.min_vel_y -0.2
    ros2 param set $node $p.max_vel_y 0.2 ;;
  *) sed -n 4,8p "$0"; exit 1 ;;
esac
