#!/usr/bin/env python3
"""Print the highest marked voxel layer per cell ahead of the robot (read-only, real robot or sim).

  python3 tools/nav/voxel_near_robot.py [--x 0.25 1.30] [--y -0.45 0.45] [--topic /local_costmap/voxel_grid]

Needs the voxel layer's publish_voxel_map: true. Assumes base_footprint == costmap origin frame at
(0, 0, yaw 0), i.e. a stationary check with a static odom -> base_footprint TF (troubleshooting/061).
Digit = highest marked layer (0 = origin_z..+z_resolution), '.' = none; rows +y -> -y.
Nav2 VoxelGrid: a marked voxel z sets bit z and bit z+16; the upper 16 bits are the marked bits.

한글: 로봇 앞 칸마다 표시된 가장 높은 voxel 층을 출력한다(읽기 전용). publish_voxel_map: true 필요.
정지 시험(odom -> base_footprint 정적 TF)에서 base_footprint가 코스트맵 원점이라고 가정한다.
"""
import argparse
import sys
import time

import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--x', type=float, nargs=2, default=(0.25, 1.30))
    ap.add_argument('--y', type=float, nargs=2, default=(-0.45, 0.45))
    ap.add_argument('--topic', default='/local_costmap/voxel_grid')
    args = ap.parse_args()

    import rclpy
    from nav2_msgs.msg import VoxelGrid
    rclpy.init()
    node = rclpy.create_node('voxel_near_robot')
    grids = []
    node.create_subscription(VoxelGrid, args.topic, grids.append, 5)
    end = time.time() + 8
    while time.time() < end and not grids:
        rclpy.spin_once(node, timeout_sec=0.1)
    if not grids:
        print(f'no {args.topic} (publish_voxel_map false?)')
        return 1
    m = grids[-1]
    data = np.array(m.data, dtype=np.uint32).reshape(m.size_y, m.size_x)
    res, ox, oy = m.resolutions.x, m.origin.x, m.origin.y
    print(f'{args.topic} {m.size_x}x{m.size_y}x{m.size_z}, {res * 100:.1f} cm, layer {m.resolutions.z * 100:.0f} cm; '
          f'x {args.x[0]}..{args.x[1]}, rows +y -> -y')
    total = 0
    for y in np.arange(args.y[1], args.y[0] - 1e-9, -res):
        row = ''
        for x in np.arange(args.x[0], args.x[1] + 1e-9, res):
            i, j = int((x - ox) / res), int((y - oy) / res)
            v = int(data[j, i]) if 0 <= i < m.size_x and 0 <= j < m.size_y else 0
            marked = [z for z in range(m.size_z) if v & (1 << (z + 16))]
            total += bool(marked)
            row += str(max(marked)) if marked else '.'
        print(f'{y:+.2f} {row}')
    print(f'marked columns: {total}')
    node.destroy_node()
    rclpy.try_shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())
