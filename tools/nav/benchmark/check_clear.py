#!/usr/bin/env python3
# 한글: 시험 전 점검: 로봇 앞 통로(기본 앞 1.5 m, 폭 ±0.35 m)에 LiDAR 점이 있는지 본다. 사람·고양이·물건이 있으면 출발하지 않는다.
"""Pre-trial check: are there LiDAR hits in the lane ahead of the robot? (read-only)

Usage: python3 tools/nav/benchmark/check_clear.py [--ahead 1.5] [--half-width 0.35]
Exit 0 = clear, 1 = something in the lane (prints where). 2026-10-10 E6: a person / a cat near the goal
made the planner cut the path short and invalidated trials.
"""
import argparse
import math
import sys
import time

import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
import tf2_ros


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--ahead', type=float, default=1.5)
    ap.add_argument('--half-width', type=float, default=0.35)
    args = ap.parse_args()
    rclpy.init()
    node = rclpy.create_node('check_clear')
    scan = {}
    node.create_subscription(LaserScan, '/scan', lambda m: scan.__setitem__('m', m), qos_profile_sensor_data)
    buf = tf2_ros.Buffer()
    tf2_ros.TransformListener(buf, node)
    t0, tf = time.time(), None
    while (tf is None or 'm' not in scan) and time.time() - t0 < 8:
        rclpy.spin_once(node, timeout_sec=0.1)
        if 'm' in scan:
            try:
                tf = buf.lookup_transform('base_footprint', scan['m'].header.frame_id, rclpy.time.Time())
            except Exception:  # noqa: BLE001
                tf = None
    if tf is None:
        sys.exit('no /scan or TF')
    m = scan['m']
    q = tf.transform.rotation
    yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
    hits = []
    for i, r in enumerate(m.ranges):
        if m.range_min < r < m.range_max:
            a = m.angle_min + i * m.angle_increment + yaw
            x = tf.transform.translation.x + r * math.cos(a)
            y = tf.transform.translation.y + r * math.sin(a)
            if 0.2 < x < args.ahead and abs(y) < args.half_width:
                hits.append((x, y))
    if hits:
        near = min(hits)
        print(f'NOT CLEAR: {len(hits)} LiDAR hits in the lane, '
              f'nearest {near[0]:.2f} m ahead, {near[1]:+.2f} m left')
        sys.exit(1)
    print(f'clear: no LiDAR hits within {args.ahead} m ahead, +-{args.half_width} m')


if __name__ == '__main__':
    main()
