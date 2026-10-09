#!/usr/bin/env python3
# 한글: 직진 흔들림 A/B 시험 1회. 현재 위치(AMCL)에서 정면으로 DIST m 앞을 NavigateToPose로 보내고
#       (경유점 없음 = DWB 자체 동작), 주행 중 vy 좌우 뒤집힘, 횡방향 이탈, map->odom 점프를 계산한다.
#       로봇이 실제로 움직인다 — 사람이 전원 스위치 옆에 있을 때만. Ctrl+C면 목표 취소(정지).
"""One straight-line wobble trial (troubleshooting/031, checklist 8.13.2). THE ROBOT MOVES.

Usage: python3 tools/nav/straight_trial.py <tag> [--dist 1.0] [--bag]
  goal = current AMCL pose + dist along the current heading, same heading (no rotation needed)
Metrics (printed and appended to Log/wobble_trials.csv):
  vy_flips          sign changes of cmd_vel_nav.linear.y (|vy| > 0.01)
  vy_rms / vy_max   lateral command from DWB
  wz_rms            yaw-rate command
  lat_max_map       max |perpendicular distance| from the start line, map frame (incl. AMCL)
  lat_max_odom      same in odom frame (smooth, open-loop)
  jumps             map->odom corrections > 3 cm or > 2 deg
  start_yaw_err     robot heading vs the start->goal line at the start (deg)
  yaw_dev_max       max |heading - line| while translating (0.2 m along the line .. 0.2 m before goal):
                    body turned away from the travel direction = diagonal/crab driving (deg)
  diag50_frac       fraction of moving commands > 50 deg off the body front (LateralRatioCritic
                    test: < 5 %), tools/nav/trial_metrics.py
(v2 CSV: Log/wobble_trials_v2.csv, 2026-10-08, after RotationShim; v3 Log/wobble_trials_v3.csv
 2026-10-10, + diag50_frac)
"""
import argparse
import csv
import math
import os
import signal
import subprocess
import sys
import time

from geometry_msgs.msg import PoseStamped, Twist
from nav2_msgs.action import NavigateToPose
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
import tf2_ros

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trial_metrics import diag_frac  # noqa: E402

TIMEOUT_S = 60.0
# 2026-10-10: + scan / depth obstacle points / costmaps -- F2-4 (troubleshooting/034) stalled 40 s
# and the bag could not show what blocked it. 한글: 멈춘 원인(무엇이 막았는지)을 bag으로 볼 수 있게 추가.
BAG_TOPICS = ('/tf /tf_static /odom /amcl_pose /cmd_vel /cmd_vel_nav /cmd_vel_smoothed /plan '
              '/collision_monitor_state /joint_states /scan /depth_cam/depth/points_sparse '
              '/local_costmap/costmap /local_costmap/costmap_updates '
              '/global_costmap/costmap /global_costmap/costmap_updates').split()


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


class Trial(Node):
    def __init__(self):
        super().__init__('straight_trial')
        self.buf = tf2_ros.Buffer()
        self.tfl = tf2_ros.TransformListener(self.buf, self)
        self.cmd = []  # (t, vx, vy, wz) from cmd_vel_nav
        self.out = []  # (t, vx, vy, wz) final cmd_vel
        self.create_subscription(Twist, '/cmd_vel_nav', lambda m: self.cmd.append(
            (time.time(), m.linear.x, m.linear.y, m.angular.z)), 50)
        self.create_subscription(Twist, '/cmd_vel', lambda m: self.out.append(
            (time.time(), m.linear.x, m.linear.y, m.angular.z)), 50)

    def pose(self, parent, child='base_footprint'):
        try:
            t = self.buf.lookup_transform(parent, child, rclpy.time.Time())
        except Exception:  # noqa: BLE001
            return None
        return (t.transform.translation.x, t.transform.translation.y, yaw_of(t.transform.rotation))

    def spin(self, secs):
        t0 = time.time()
        while time.time() - t0 < secs:
            rclpy.spin_once(self, timeout_sec=0.02)


def lateral(p, start):
    x0, y0, h = start
    return -(p[0] - x0) * math.sin(h) + (p[1] - y0) * math.cos(h)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('tag', help='condition label, e.g. C_standard, A_limited, B_vy_off')
    ap.add_argument('--dist', type=float, default=1.0)
    ap.add_argument('--bag', action='store_true', help='also record a rosbag under bags/wobble/')
    ap.add_argument('--turn', action='store_true',
                    help='only rotate in place (180 deg, or to face --goal); not logged')
    ap.add_argument('--goal', type=float, nargs=2, metavar=('X', 'Y'),
                    help='fixed map goal instead of --dist ahead; heading = start->goal line')
    ap.add_argument('--timeout', type=float, default=TIMEOUT_S,
                    help='s (wall clock) before the goal is canceled; raise it in a slow simulation')
    args = ap.parse_args()

    rclpy.init()
    node = Trial()
    # wait up to 10 s for TF (slow under CPU load) / 부하가 높으면 TF가 늦게 와서 최대 10초 대기
    start_map = start_odom = None
    t_wait = time.time()
    while (start_map is None or start_odom is None) and time.time() - t_wait < 10.0:
        node.spin(0.5)
        start_map, start_odom = node.pose('map'), node.pose('odom')
    if start_map is None or start_odom is None:
        raise SystemExit('no map/odom -> base_footprint TF (AMCL/EKF running?)')
    if args.goal:
        # 한글: 고정 목표점. 진행 방향 = 시작점->목표점 직선. --turn이면 그 방향으로 제자리 회전만.
        line_yaw = math.atan2(args.goal[1] - start_map[1], args.goal[0] - start_map[0])
        gx, gy = (start_map[0], start_map[1]) if args.turn else tuple(args.goal)
        gyaw = line_yaw
    else:
        dist = 0.0 if args.turn else args.dist
        gx = start_map[0] + dist * math.cos(start_map[2])
        gy = start_map[1] + dist * math.sin(start_map[2])
        gyaw = start_map[2] + (math.pi if args.turn else 0.0)  # 한글: --turn이면 제자리 180도 회전만
    # lateral deviation is measured from the start->goal line / 횡이탈은 시작점->목표 직선 기준
    line_map = (start_map[0], start_map[1], gyaw)
    line_odom = (start_odom[0], start_odom[1], start_odom[2] + (gyaw - start_map[2]))
    print(f'start map ({start_map[0]:.2f}, {start_map[1]:.2f}, {math.degrees(start_map[2]):.0f}deg)'
          f' -> goal ({gx:.2f}, {gy:.2f}, {math.degrees(gyaw):.0f}deg)')

    bag = None
    stamp = time.strftime('%Y%m%d_%H%M%S')
    if args.bag:
        out = f'bags/wobble/{args.tag}_{stamp}'
        os.makedirs('bags/wobble', exist_ok=True)
        bag = subprocess.Popen(['ros2', 'bag', 'record', '-o', out] + BAG_TOPICS,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               preexec_fn=os.setsid)
        node.spin(3.0)

    client = ActionClient(node, NavigateToPose, 'navigate_to_pose')
    if not client.wait_for_server(timeout_sec=10.0):
        raise SystemExit('navigate_to_pose not available')
    goal = NavigateToPose.Goal()
    goal.pose = PoseStamped()
    goal.pose.header.frame_id = 'map'
    goal.pose.pose.position.x, goal.pose.pose.position.y = gx, gy
    goal.pose.pose.orientation.z = math.sin(gyaw / 2)
    goal.pose.pose.orientation.w = math.cos(gyaw / 2)

    node.cmd.clear()
    node.out.clear()
    track_map, track_odom, jumps = [], [], 0
    prev_mo = node.pose('map', 'odom')
    status, handle, t0 = None, None, time.time()
    try:
        send = client.send_goal_async(goal)
        rclpy.spin_until_future_complete(node, send)
        handle = send.result()
        if not handle.accepted:
            status = 'rejected'
        else:
            res = handle.get_result_async()
            next_sample = 0.0
            while not res.done():
                rclpy.spin_once(node, timeout_sec=0.02)
                now = time.time()
                if now >= next_sample:  # 10 Hz pose sampling / 10 Hz로 위치 기록
                    next_sample = now + 0.1
                    pm, po, mo = node.pose('map'), node.pose('odom'), node.pose('map', 'odom')
                    if pm:
                        track_map.append(pm)
                    if po:
                        track_odom.append(po)
                    if mo and prev_mo:
                        dyaw = abs(math.atan2(math.sin(mo[2] - prev_mo[2]), math.cos(mo[2] - prev_mo[2])))
                        if math.hypot(mo[0] - prev_mo[0], mo[1] - prev_mo[1]) > 0.03 or dyaw > math.radians(2):
                            jumps += 1
                    prev_mo = mo or prev_mo
                if now - t0 > args.timeout:
                    handle.cancel_goal_async()
                    status = 'timeout'
                    break
            if status is None:
                status = {4: 'succeeded', 5: 'canceled', 6: 'aborted'}.get(
                    res.result().status, str(res.result().status))
    except KeyboardInterrupt:
        if handle is not None:
            handle.cancel_goal_async()  # 한글: Ctrl+C면 목표 취소 → 정지
        status = 'interrupted'
    finally:
        elapsed = time.time() - t0
        node.spin(2.0)
        if bag is not None:
            os.killpg(bag.pid, signal.SIGINT)
            try:
                bag.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(bag.pid, signal.SIGKILL)

    if args.turn:
        final = node.pose('map')
        err = math.degrees(abs(math.atan2(math.sin(final[2] - gyaw), math.cos(final[2] - gyaw))))
        print(f'turn {status}: now ({final[0]:.2f}, {final[1]:.2f}, {math.degrees(final[2]):.0f}deg),'
              f' {err:.0f} deg off target')
        node.destroy_node()
        rclpy.shutdown()
        return
    flips, last = 0, 0
    for _, _, vy, _ in node.cmd:
        s = 0 if abs(vy) < 0.01 else (1 if vy > 0 else -1)
        if s and last and s != last:
            flips += 1
        if s:
            last = s
    n = max(len(node.cmd), 1)
    vy_rms = math.sqrt(sum(c[2] ** 2 for c in node.cmd) / n)
    vy_max = max((abs(c[2]) for c in node.cmd), default=0.0)
    wz_rms = math.sqrt(sum(c[3] ** 2 for c in node.cmd) / n)
    lat_map = max((abs(lateral(p, line_map)) for p in track_map), default=float('nan'))
    lat_odom = max((abs(lateral(p, line_odom)) for p in track_odom), default=float('nan'))
    final = node.pose('map')
    pos_err = math.hypot(final[0] - gx, final[1] - gy) if final else float('nan')

    def ang(a):
        return math.degrees(abs(math.atan2(math.sin(a), math.cos(a))))
    start_yaw_err = ang(start_map[2] - gyaw)
    total = math.hypot(gx - start_map[0], gy - start_map[1])
    # only the translating middle part: 0.2 m progressed along the line .. 0.2 m before the goal
    # (2026-10-09: with ">5 cm from start" the in-place turn leaked in -> 50-60 deg)
    # 한글: 직선 방향 진행량 0.2 m ~ 목표 0.2 m 전 구간만(제자리 회전 구간 제외)
    def along(p):
        return (p[0] - start_map[0]) * math.cos(gyaw) + (p[1] - start_map[1]) * math.sin(gyaw)
    devs = [ang(p[2] - gyaw) for p in track_map
            if 0.2 < along(p) < total - 0.2]
    yaw_dev = max(devs, default=float('nan'))
    row = {'time': stamp, 'tag': args.tag, 'status': status, 'elapsed_s': round(elapsed, 1),
           'vy_flips': flips, 'vy_flips_per_min': round(flips / max(elapsed, 1e-3) * 60, 1),
           'vy_rms': round(vy_rms, 4), 'vy_max': round(vy_max, 3), 'wz_rms': round(wz_rms, 3),
           'lat_max_map_cm': round(lat_map * 100, 1), 'lat_max_odom_cm': round(lat_odom * 100, 1),
           'jumps': jumps, 'pos_err_cm': round(pos_err * 100, 1), 'n_cmd': len(node.cmd),
           'start_yaw_err_deg': round(start_yaw_err, 1), 'yaw_dev_max_deg': round(yaw_dev, 1),
           'diag50_frac': round(diag_frac([(c[1], c[2]) for c in node.cmd]), 3)}
    for k, v in row.items():
        print(f'  {k:18s} {v}')
    os.makedirs('Log', exist_ok=True)
    # v3 (2026-10-10): + diag50_frac (v2: Log/wobble_trials_v2.csv, v1: Log/wobble_trials.csv)
    path = 'Log/wobble_trials_v3.csv'
    new = not os.path.exists(path)
    with open(path, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)
    print(f'appended to {path}')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
