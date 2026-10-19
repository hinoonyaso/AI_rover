#!/usr/bin/env python3
# 한글: 전역 코스트맵에서 로봇 중심이 갈 수 있는 칸(값 < 99)의 가로 구간을 y 줄마다 출력한다(host). 상자 옆 통로 폭을 재는 진단.
"""Free (robot-centre) intervals of the global costmap per row (host, ROS_DOMAIN_ID=31, Nav2 running).

Costmap values: 0 free, 1..98 inflation gradient, 99 inscribed (centre cannot be here), 100 lethal, -1 unknown.
  python3 tools/sim/corridor_width.py --y 0.6 1.4 --step 0.1 [--x 0.3 1.8]
Prints for each y the x intervals with value < 99, their width, and whether the Gazebo box (33 x 22 cm, ground truth) blocks it.
"""
import argparse
import os
import sys

from nav_msgs.msg import OccupancyGrid
import numpy as np
import rclpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import avoid_trials as T  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--y', type=float, nargs=2, default=[0.5, 1.5])
    ap.add_argument('--step', type=float, default=0.1)
    ap.add_argument('--x', type=float, nargs=2, default=[0.2, 1.9])
    ap.add_argument('--box-x', type=float, default=None, help='box centre x (default: scenario S2)')
    args = ap.parse_args()
    rclpy.init()
    node = T.Runner()
    got = {}
    node.create_subscription(OccupancyGrid, '/global_costmap/costmap', lambda m: got.__setitem__('m', m), 1)
    try:
        t0 = __import__('time').time()
        while 'm' not in got and __import__('time').time() - t0 < 20:
            node.spin(0.2)
        m = got['m']
        info = m.info
        g = np.array(m.data).reshape(info.height, info.width)
        bx = args.box_x if args.box_x is not None else T.SCENARIOS['S2']['box'][0]
        print(f'box x {bx - T.BOX_SIZE[0] / 2:.3f}..{bx + T.BOX_SIZE[0] / 2:.3f}, y {0.89..1.11} (left edge = {bx - T.BOX_SIZE[0] / 2:.3f})')
        y = args.y[0]
        while y <= args.y[1] + 1e-9:
            iy = int((y - info.origin.position.y) / info.resolution)
            xs = np.arange(args.x[0], args.x[1], info.resolution)
            ix = ((xs - info.origin.position.x) / info.resolution).astype(int)
            free = np.array([0 <= iy < info.height and 0 <= i < info.width and 0 <= g[iy, i] < 99 for i in ix])
            segs, start = [], None
            for k, f in enumerate(free):
                if f and start is None:
                    start = k
                if (not f or k == len(free) - 1) and start is not None:
                    end = k if not f else k + 1
                    segs.append((xs[start], xs[end - 1], (end - start) * info.resolution))
                    start = None
            print(f'y {y:.2f}: ' + ('  '.join(f'[{a:.2f}..{b:.2f}] w={w * 100:.0f} cm' for a, b, w in segs) or 'no free cells'))
            y += args.step
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
