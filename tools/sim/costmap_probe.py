#!/usr/bin/env python3
# 한글: 로봇을 지정한 자리에 놓고 몇 초 기다린 뒤, 지정한 점들 주변의 전역/로컬 코스트맵 값을 표로 출력한다(host).
#       목표 점이 코스트맵에서 막혀 있는지(플래너가 끝점을 옮기는 원인) 확인하는 진단.
"""Costmap values around given points (host, ROS_DOMAIN_ID=31, Nav2 running).

  python3 tools/sim/costmap_probe.py --robot 1.0 1.45 90 --points 1.0,1.45 1.02,0.37 [--wait 6] [--half 0.2]
Values (Nav2 costmap topic): 0 free, 1..98 inflation gradient, 99 inscribed (centre cannot be here), 100 lethal, -1 unknown.
Prints a (2*half/0.05+1)^2 grid per point and per costmap (global, local) around the point, north up.
"""
import argparse
import math
import os
import sys

from nav_msgs.msg import OccupancyGrid
import rclpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import avoid_trials as T  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--robot', type=float, nargs=3, default=[1.0, 1.45, 90.0])
    ap.add_argument('--points', nargs='+', default=['1.0,1.45'])
    ap.add_argument('--wait', type=float, default=6.0)
    ap.add_argument('--half', type=float, default=0.2)
    ap.add_argument('--box', type=float, nargs=2, default=None, help='box centre (default: parked under the floor)')
    args = ap.parse_args()
    rclpy.init()
    node, gt = T.Runner(), T.GroundTruth()
    cost = {}
    node.create_subscription(OccupancyGrid, '/local_costmap/costmap', lambda m: cost.__setitem__('local', m), 1)
    node.create_subscription(OccupancyGrid, '/global_costmap/costmap', lambda m: cost.__setitem__('global', m), 1)
    try:
        node.spin(3.0)
        for c in T.CUBES:
            T.gz_set_pose(c, 0.45, 1.35, -3.0)
        T.gz_set_pose(T.BOX, *(args.box if args.box else (0.45, 1.35)), 0.055 if args.box else -3.0)
        x, y, yaw = args.robot
        T.gz_set_pose('jetrover', x, y, 0.01, yaw)
        node.spin(1.0)
        node.set_initial_pose(x, y, math.radians(yaw))
        node.spin(args.wait)
        for kind in ('global', 'local'):
            m = cost.get(kind)
            if m is None:
                print(f'{kind}: no costmap')
                continue
            info = m.info
            try:
                tr = node.buf.lookup_transform(m.header.frame_id, 'map', rclpy.time.Time())
                q = tr.transform.rotation
                yw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
                c, s, tx, ty = math.cos(yw), math.sin(yw), tr.transform.translation.x, tr.transform.translation.y
            except Exception:  # noqa: BLE001
                c, s, tx, ty = 1.0, 0.0, 0.0, 0.0
            for p in args.points:
                px, py = (float(v) for v in p.split(','))
                print(f'{kind} costmap around ({px:.2f}, {py:.2f}); rows y {py + args.half:.2f} .. {py - args.half:.2f}, cols x {px - args.half:.2f} .. '
                      f'{px + args.half:.2f} step 5 cm')
                n = int(round(args.half / 0.05))
                for j in range(n, -n - 1, -1):
                    row = []
                    for i in range(-n, n + 1):
                        X, Y = px + i * 0.05, py + j * 0.05
                        gx, gy = c * X - s * Y + tx, s * X + c * Y + ty
                        ix, iy = int((gx - info.origin.position.x) / info.resolution), int((gy - info.origin.position.y) / info.resolution)
                        v = m.data[iy * info.width + ix] if 0 <= ix < info.width and 0 <= iy < info.height else -2
                        row.append(f'{v:4d}')
                    print('  ' + ''.join(row) + (f'   y {py + j * 0.05:.2f}'))
    finally:
        gt.stop()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
