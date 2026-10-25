#!/usr/bin/env bash
# 한글: Jetson에서 녹화(bag)를 sim 시간으로 재생하며 Nav2(map_server + 주행 노드)를 띄우고 목표를 보내 CPU·제어 주기를 잰다.
#       로봇은 움직이지 않는다(/cmd_vel을 받는 base_node가 없음). 설정 변경의 Jetson 부하 비교용(8.15/8.16 실기 준비, 2026-10-25).
# Replays a recorded run (scan, depth obstacle points, TF, odom) with sim time, runs map_server + Nav2 navigation with PARAMS,
# sends GOAL and reports controller CPU / missed control-loop warnings. Nothing moves: no base_node is running.
#   usage: bash tools/nav/replay_load.sh <params.yaml> <bag dir> [label]      (ROS_DOMAIN_ID 33, map lap2)
PARAMS=$1; BAG=$2; LABEL=${3:-$(basename "$PARAMS" .yaml)}
cd "$(dirname "$0")/../.."
source /opt/ros/jazzy/setup.bash; source install/setup.bash
set -u   # ROS setup 스크립트는 미정의 변수를 쓰므로 그 뒤에 / after sourcing (the setup scripts use unset variables)
# 이 Jetson은 Wi-Fi 전용 Fast DDS 설정(setup/fastdds_wifi_only.xml)을 쓴다. 그 상태로 LOCALHOST 범위를 쓰면 노드끼리 못 찾아
# lifecycle 관리자가 get_state만 기다렸다(2026-10-25). 재생 시험은 이 Jetson 안에서만 하므로 그 설정을 빼고 localhost로.
# The Wi-Fi-only Fast DDS profile plus LOCALHOST discovery hid the nodes from each other; drop the profile for this local test.
unset FASTRTPS_DEFAULT_PROFILES_FILE
export ROS_DOMAIN_ID=33 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
if pgrep -x base_node >/dev/null; then echo "base_node is running - refusing (replay must not reach the robot)"; exit 1; fi
OUT=Log/replay_load; mkdir -p $OUT
TMP=$(mktemp --suffix .yaml)
# 재생은 sim 시간: 파라미터의 use_sim_time: false를 true로 바꾼 임시 파일 / replay runs on sim time
sed 's/use_sim_time: false/use_sim_time: true/' "$PARAMS" > "$TMP"
set -m
# 재생을 먼저(반복): Nav2가 뜨는 동안 /clock과 TF가 있어야 lifecycle 활성화가 진행된다(먼저 띄웠더니 get_state만 기다림).
# Play first (looped) so /clock and TF exist while Nav2 starts; starting Nav2 first left the lifecycle manager waiting.
ros2 bag play "$BAG" --clock --loop -r 1.0 --topics /scan /depth_cam/depth/points_sparse /tf /tf_static /odom > $OUT/${LABEL}_play.log 2>&1 &
P=$!
sleep 3
ros2 run nav2_map_server map_server --ros-args -p yaml_filename:=$PWD/maps/lap2_20261005.yaml -p use_sim_time:=true > $OUT/${LABEL}_map.log 2>&1 &
M=$!
ros2 run nav2_lifecycle_manager lifecycle_manager --ros-args -r __node:=lm_map -p node_names:="['map_server']" -p autostart:=true -p use_sim_time:=true > $OUT/${LABEL}_lm.log 2>&1 &
LM=$!
ros2 launch nav2_bringup navigation_launch.py use_sim_time:=true params_file:=$TMP > $OUT/${LABEL}_nav.log 2>&1 &
N=$!
cleanup() { trap - EXIT INT TERM; for g in $P $N $LM $M; do kill -INT -- -$g 2>/dev/null; done; sleep 6; for g in $P $N $LM $M; do kill -KILL -- -$g 2>/dev/null; done; rm -f "$TMP"; }
trap cleanup EXIT; trap 'exit 130' INT TERM
# Nav2 준비 대기(최대 90 s): 로그의 활성화 메시지로 본다. `ros2 action list`는 다른 환경으로 떠 있던 ros2 daemon에 물어봐서 못 찾았다.
# Wait for "Managed nodes are active" in the log (ros2 action list asked a daemon started with another environment).
for i in $(seq 45); do
  grep -q "Managed nodes are active" $OUT/${LABEL}_nav.log && break
  sleep 2
done
grep -q "Managed nodes are active" $OUT/${LABEL}_nav.log || { echo "Nav2 not up after 90 s"; exit 1; }
sleep 3
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: map}, pose: {position: {x: 1.05, y: 1.40}, orientation: {z: 0.7071, w: 0.7071}}}}" > $OUT/${LABEL}_goal.log 2>&1 &
G=$!
# CPU: controller_server / planner_server(전역 코스트맵) 프로세스, tegrastats 전체 / per-process and whole-system CPU
CP=$(pgrep -f "lib/nav2_controller/controller_server" | head -1); PP=$(pgrep -f "lib/nav2_planner/planner_server" | head -1)
tegrastats --interval 1000 > $OUT/${LABEL}_tegra.log 2>&1 &
T=$!
: > $OUT/${LABEL}_cpu.log
for i in $(seq 25); do
  echo "$(ps -o %cpu= -p $CP 2>/dev/null) $(ps -o %cpu= -p $PP 2>/dev/null) $(top -b -n1 -p $CP | awk 'NR==8{print $9}')" >> $OUT/${LABEL}_cpu.log
  sleep 1
done
kill $T $G 2>/dev/null
echo "== $LABEL"
echo "controller loop missed-rate warnings: $(grep -c 'Control loop missed its desired rate' $OUT/${LABEL}_nav.log)"
grep 'Control loop missed its desired rate' $OUT/${LABEL}_nav.log | grep -oE 'Current loop rate is [0-9.]+' | awk '{print $5}' | sort -n | head -1 | sed 's/^/  slowest loop Hz: /'
awk '{c+=$3; n++; if($3>m)m=$3} END{printf "controller_server CPU (top, %%): mean %.1f max %.1f\n", c/n, m}' $OUT/${LABEL}_cpu.log
grep -oE 'CPU \[[^]]*\]' $OUT/${LABEL}_tegra.log | sed -E 's/CPU \[//; s/\]//; s/@[0-9]+//g; s/%//g' | \
  awk -F, '{s=0; for(i=1;i<=NF;i++) s+=$i; s/=NF; t+=s; n++; if(s>m)m=s} END{printf "all cores (tegrastats, %%): mean %.1f max %.1f\n", t/n, m}'
grep -iE "error|exception" $OUT/${LABEL}_nav.log | grep -v "Message Filter" | head -3
