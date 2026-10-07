#!/usr/bin/env bash
# 한글: 떠 있는 nav2.launch.py와 자식 노드를 모두 종료한다(pgrep -f가 자기 셸을 잡는 문제 회피용 스크립트).
pat='ros2 launch [j]etrover_navigation nav2.launch.py'
for L in $(pgrep -f "$pat"); do kill -INT $(ps -o pid= --ppid "$L") "$L" 2>/dev/null; done
for i in $(seq 1 25); do pgrep -x controller_serv >/dev/null || pgrep -x amcl >/dev/null || exit 0; sleep 1; done
echo "nav2 still running" >&2; exit 1
