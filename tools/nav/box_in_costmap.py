#!/usr/bin/env python3
# 한글: 출발 전에 로봇 앞 장애물(상자)이 global costmap에 들어가 있는지 확인한다(지도에 없는 lethal 칸 수). 읽기만 한다.
"""Count sensor-marked lethal cells (not in the static map) in front of the robot in the global costmap.

Usage: python3 tools/nav/box_in_costmap.py [--ahead 0.2 1.0] [--side 0.5]
Waits up to --wait s until at least --min cells are present (exit 0), else exit 1.
"""
import argparse
import math
import sys
import time

import numpy as np
from nav_msgs.msg import OccupancyGrid
import rclpy
from rclpy.qos import DurabilityPolicy, QoSProfile
import tf2_ros


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ahead', type=float, nargs=2, default=(0.2, 1.0))
    ap.add_argument('--side', type=float, default=0.5)
    ap.add_argument('--min', type=int, default=3)
    ap.add_argument('--wait', type=float, default=10.0)
    args = ap.parse_args()
    rclpy.init()
    n = rclpy.create_node('box_in_costmap')
    d = {}
    q = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
    n.create_subscription(OccupancyGrid, '/global_costmap/costmap', lambda m: d.__setitem__('g', m), q)
    n.create_subscription(OccupancyGrid, '/map', lambda m: d.__setitem__('m', m), q)
    buf = tf2_ros.Buffer()
    tf2_ros.TransformListener(buf, n)
    t0 = time.time()
    count = 0
    while time.time() - t0 < args.wait:
        rclpy.spin_once(n, timeout_sec=0.2)
        if 'g' not in d or 'm' not in d:
            continue
        try:
            tr = buf.lookup_transform('map', 'base_footprint', rclpy.time.Time())
        except Exception:  # noqa: BLE001
            continue
        g, m = d['g'], d['m']
        G = np.array(g.data).reshape(g.info.height, g.info.width)
        M = np.array(m.data).reshape(m.info.height, m.info.width)
        if G.shape != M.shape:
            break
        r = g.info.resolution
        ys, xs = np.nonzero((G == 100) & (M != 100))
        X = g.info.origin.position.x + (xs + 0.5) * r
        Y = g.info.origin.position.y + (ys + 0.5) * r
        x0, y0 = tr.transform.translation.x, tr.transform.translation.y
        qq = tr.transform.rotation
        yaw = math.atan2(2 * qq.w * qq.z, 1 - 2 * qq.z * qq.z)
        fwd = (X - x0) * math.cos(yaw) + (Y - y0) * math.sin(yaw)
        side = -(X - x0) * math.sin(yaw) + (Y - y0) * math.cos(yaw)
        sel = (fwd > args.ahead[0]) & (fwd < args.ahead[1]) & (np.abs(side) < args.side)
        count = int(sel.sum())
        if count >= args.min:
            print(f'obstacle in global costmap: {count} cells, ahead {fwd[sel].min():.2f}-{fwd[sel].max():.2f} m, '
                  f'side {side[sel].min():+.2f}..{side[sel].max():+.2f} m')
            sys.exit(0)
    print(f'no obstacle in global costmap ahead ({count} cells)')
    sys.exit(1)


if __name__ == '__main__':
    main()
