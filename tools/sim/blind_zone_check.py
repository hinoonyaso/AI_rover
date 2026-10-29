#!/usr/bin/env python3
# 한글: 체크리스트 8.13.14 진단(host, sim). 로봇을 상자 쪽으로 천천히 몰아 상자가 카메라 바닥 시야 앞(범퍼 바로 앞 사각지대)에
#       들어간 뒤에도 local costmap에 상자가 남는지 본다. 남지 않으면 depth 지우기 광선이 사각지대 상자를 지우는 것 →
#       raytrace_min_range 같은 대책이 필요. /cmd_vel에 직접 내므로 collision_monitor를 거치지 않는다(sim 전용, 실기에 쓰지 말 것).
"""Does a low box that slides into the camera's near blind zone stay in the local costmap? (host, sim only, checklist 8.13.14)

  python3 tools/sim/blind_zone_check.py [--gaps 0.40 0.20 0.10 0.03] [--hold 5]

Places object_0 (33 x 22 x 11 cm, LiDAR-invisible) ahead of the robot at A, then drives straight at 0.05 m/s on /cmd_vel
(bypasses collision_monitor - simulation only) and at each bumper-to-box gap prints the highest local-costmap value over
the box cells (100 lethal, 99 inscribed, 0 free, -1 unknown). After the last gap it holds still for --hold s and prints again.
"""
import argparse
import math
import os
import sys

from geometry_msgs.msg import Twist
from nav_msgs.msg import OccupancyGrid
import rclpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import avoid_trials as T  # noqa: E402

FRONT = 0.15          # URDF front extent of the body (avoid_trials FOOTPRINT_HALF note) / 몸 앞쪽 끝
START = (1.02, 0.30, 90.0)


def box_cost(node, grid, bx, by, half=(0.165, 0.11)):
    """Max costmap value over cells inside the box (map frame), sampled every 2.5 cm. 한글: 상자 칸들의 최대 비용."""
    if grid is None:
        return None
    info = grid.info
    try:
        tr = node.buf.lookup_transform(grid.header.frame_id, 'map', rclpy.time.Time())
        q = tr.transform.rotation
        yw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        c, s, tx, ty = math.cos(yw), math.sin(yw), tr.transform.translation.x, tr.transform.translation.y
    except Exception:  # noqa: BLE001
        return None
    best = -2
    n_x, n_y = int(half[0] / 0.025), int(half[1] / 0.025)
    for i in range(-n_x, n_x + 1):
        for j in range(-n_y, n_y + 1):
            X, Y = bx + i * 0.025, by + j * 0.025
            gx, gy = c * X - s * Y + tx, s * X + c * Y + ty
            ix = int((gx - info.origin.position.x) / info.resolution)
            iy = int((gy - info.origin.position.y) / info.resolution)
            if 0 <= ix < info.width and 0 <= iy < info.height:
                best = max(best, grid.data[iy * info.width + ix])
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--gaps', type=float, nargs='+', default=[0.40, 0.20, 0.10, 0.03])
    ap.add_argument('--hold', type=float, default=5.0)
    args = ap.parse_args()
    rclpy.init()
    node, gt = T.Runner(), T.GroundTruth()
    cost = {}
    node.create_subscription(OccupancyGrid, '/local_costmap/costmap', lambda m: cost.__setitem__('local', m), 1)
    pub = node.create_publisher(Twist, '/cmd_vel', 10)
    try:
        node.spin(3.0)
        for cube in T.CUBES:
            T.gz_set_pose(cube, 0.45, 1.35, -3.0)
        x, y, yaw = START
        # 상자 가까운 면 = 범퍼 + 첫 간격 / box near face at the first gap ahead of the bumper (box long side across the path)
        by = y + FRONT + args.gaps[0] + T.BOX_SIZE[1] / 2
        T.gz_set_pose(T.BOX, x, by, 0.055)
        T.gz_set_pose('jetrover', x, y, 0.01, yaw)
        node.spin(1.0)
        node.set_initial_pose(x, y, math.radians(yaw))
        node.spin(6.0)
        node.clear_costmaps()
        node.spin(4.0)
        for gap in args.gaps:
            # 정답 위치로 간격을 재며 0.05 m/s 전진 / drive until the ground-truth bumper gap reaches `gap`
            for _ in range(600):
                if not gt.latest:
                    node.spin(0.1)
                    continue
                cur = by - T.BOX_SIZE[1] / 2 - (gt.latest[2] + FRONT)
                if cur <= gap:
                    break
                m = Twist()
                m.linear.x = 0.05
                pub.publish(m)
                node.spin(0.1)
            for _ in range(3):
                pub.publish(Twist())
                node.spin(0.1)
            node.spin(1.0)
            cur = by - T.BOX_SIZE[1] / 2 - (gt.latest[2] + FRONT)
            print(f'gap {cur * 100:5.1f} cm: box max local cost {box_cost(node, cost.get("local"), x, by)}', flush=True)
        node.spin(args.hold)
        print(f'after {args.hold:.0f} s still: box max local cost {box_cost(node, cost.get("local"), x, by)}', flush=True)
    finally:
        for _ in range(3):
            pub.publish(Twist())
        gt.stop()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
