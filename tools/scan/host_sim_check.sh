#!/usr/bin/env bash
# 한글: (host) Gazebo 시뮬레이션을 화면 없이 띄워 로봇 스폰·센서 토픽·컨트롤러를 확인하고 카메라 한 장을 저장한 뒤 끈다.
#       실기(ROS_DOMAIN_ID=25)와 섞이지 않게 31 + localhost 전용.
# (host) Headless Gazebo smoke test: spawn, sensor topics, controllers, one camera frame, then shut down.
#
# Usage: tools/scan/host_sim_check.sh <world.sdf> <out_dir> [run_s] [color]
#   color: 팔을 스캔 자세 B로, RTF/카메라 FPS/GPU 메모리 + 90°씩 카메라 4장(sim_color_check.py)
#          arm at scan pose B, RTF / camera FPS / GPU memory and 4 camera views (sim_color_check.py)
set -e
WORLD=${1:?world}
OUT=${2:?out dir}
RUN_S=${3:-40}
MODE=${4:-basic}
source /opt/ros/jazzy/setup.bash
source "$HOME/jetrover_ws/install/setup.bash"
set -u
set -m
export ROS_DOMAIN_ID=31
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
# gz transport도 실행마다 분리 / separate gz transport partition per run
export GZ_PARTITION=simcheck_$$
# gz-transport를 loopback으로만 — 2026-10-14 host에서 네트워크 discovery 전송이 소켓에서 막혀(sock_alloc_send_pskb)
# 월드가 로딩 중 멈췄다(로봇 없는 빈 월드도). GZ_IP=127.0.0.1이면 2000 스텝 5 s.
# Loopback only: network discovery sends blocked and froze world loading on the host.
export GZ_IP=127.0.0.1
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)

ros2 launch jetrover_gazebo sim.launch.py world:="$WORLD" gui:=false > "$OUT/sim.log" 2>&1 &
LPID=$!
sleep "$RUN_S"
{
  echo "== controllers"; timeout 10 ros2 control list_controllers 2>&1 || true
  # 실시간 비율: /clock 두 번(실시간 10 s 간격) / real-time factor from two /clock samples 10 s apart
  c1=$(timeout 10 ros2 topic echo --once --field clock.sec /clock 2>/dev/null | head -1)
  t1=$(date +%s); sleep 10
  c2=$(timeout 10 ros2 topic echo --once --field clock.sec /clock 2>/dev/null | head -1)
  t2=$(date +%s)
  echo "== rtf sim ${c1:-?} -> ${c2:-?} over $((t2 - t1)) s real"
  for t in /scan /odom /imu/data_raw /depth_cam/color/image_raw /depth_cam/depth/image_raw /joint_states; do
    echo "== hz $t"; timeout 8 ros2 topic hz "$t" 2>&1 | grep -m1 "average rate" || echo "NO DATA"
  done
} > "$OUT/check.txt" 2>&1
# 스캔 거리 통계와 카메라 한 장 / scan range stats and one camera frame
timeout 40 python3 - "$OUT" > "$OUT/sample.txt" 2>&1 <<'EOF' || true
import sys, numpy as np, rclpy
from sensor_msgs.msg import LaserScan, Image
out = sys.argv[1]
rclpy.init(); n = rclpy.create_node('sim_check'); got = {}
n.create_subscription(LaserScan, '/scan', lambda m: got.setdefault('scan', m), 10)
n.create_subscription(Image, '/depth_cam/color/image_raw', lambda m: got.setdefault('img', m), 10)
while len(got) < 2:
    rclpy.spin_once(n, timeout_sec=0.5)
sc = got['scan']; r = np.array(sc.ranges); ok = np.isfinite(r)
np.save(out + '/scan.npy', np.concatenate([[sc.angle_min, sc.angle_increment], r]))
print('scan: %d beams, finite %d, min %.2f median %.2f max %.2f m' % (len(r), ok.sum(), r[ok].min(), np.median(r[ok]), r[ok].max()))
im = got['img']; a = np.frombuffer(im.data, np.uint8).reshape(im.height, im.width, -1)
print('image: %dx%d %s mean %.1f std %.1f' % (im.width, im.height, im.encoding, a.mean(), a.std()))
try:
    from PIL import Image as P
    P.fromarray(a[:, :, :3]).save(out + '/camera.png'); print('saved camera.png')
except Exception as e:
    print('no PIL:', e)
# 짧은 주행: /cmd_vel 0.1 m/s 3 s 후 odom 이동량 / short drive: 0.1 m/s for 3 s, odom displacement
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
od = {}
n.create_subscription(Odometry, '/odom', lambda m: od.update(p=(m.pose.pose.position.x, m.pose.pose.position.y)), 10)
pub = n.create_publisher(Twist, '/cmd_vel', 10)
while 'p' not in od:
    rclpy.spin_once(n, timeout_sec=0.2)
p0 = od['p']
import time
t0 = time.monotonic()
while time.monotonic() - t0 < 3.0:
    tw = Twist(); tw.linear.x = 0.1; pub.publish(tw); rclpy.spin_once(n, timeout_sec=0.1)
for _ in range(10):
    pub.publish(Twist()); rclpy.spin_once(n, timeout_sec=0.1)
p1 = od['p']
print('drive: odom moved %.3f m (commanded 0.1 m/s x 3 s)' % np.hypot(p1[0] - p0[0], p1[1] - p0[1]))
EOF
if [ "$MODE" = color ]; then
  # arm_hold가 0.5 s마다 홈 자세로 되돌리므로 멈춘다 / arm_hold re-sends home every 0.5 s: stop it
  AH=$(pgrep -f "lib/jetrover_gazebo/arm_hold.py" || true)
  [ -n "$AH" ] && kill $AH
  timeout 90 python3 "$(dirname "$0")/sim_color_check.py" "$OUT" > "$OUT/color.txt" 2>&1 || true
  cat "$OUT/color.txt"
fi
kill -INT -- -$LPID || true
sleep 10
# launch는 ruby 래퍼만 끄고 실제 `gz sim` 서버를 고아로 남긴다(2026-10-14, 7개 누적) — 그룹 전체를 확실히 끈다.
# The launch leaves the real `gz sim` server orphaned: terminate the whole process group.
kill -TERM -- -$LPID 2>/dev/null || true
sleep 3
kill -KILL -- -$LPID 2>/dev/null || true
wait $LPID 2>/dev/null || true
cat "$OUT/check.txt" "$OUT/sample.txt"
