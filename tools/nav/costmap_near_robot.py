#!/usr/bin/env python3
"""Print costmap values around a point given in the robot frame (read-only, real robot or sim).

  python3 tools/nav/costmap_near_robot.py --ahead 0.8 --left 0.0 --half 0.25 [--topic /local_costmap/costmap]

Reads one costmap message, transforms the point (base_footprint) into the costmap frame with TF and
prints the grid around it, north up in the costmap frame. Values: 0 free, 1..98 inflation, 99
inscribed, 100 lethal, -1 unknown. Used to check whether a low object in front of the stationary
robot is in the costmap (troubleshooting/061). It never commands motion.

한글: 로봇 기준 지점 주변의 코스트맵 값을 출력한다(읽기 전용). 정지한 로봇 앞의 낮은 물체가 코스트맵에
들어가는지 확인할 때 쓴다(061). 움직임 명령을 보내지 않는다.
"""
import argparse
import math
import sys
import time


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--ahead', type=float, required=True, help='m forward of base_footprint')
    ap.add_argument('--left', type=float, default=0.0, help='m to the left of base_footprint')
    ap.add_argument('--half', type=float, default=0.25)
    ap.add_argument('--topic', default='/local_costmap/costmap')
    ap.add_argument('--wait', type=float, default=15.0)
    args = ap.parse_args()

    import rclpy
    from rclpy.node import Node
    from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
    from nav_msgs.msg import OccupancyGrid
    import tf2_ros

    rclpy.init()
    node = Node('costmap_near_robot')
    grids = []
    qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL)
    node.create_subscription(OccupancyGrid, args.topic, grids.append, qos)
    buf = tf2_ros.Buffer()
    tf2_ros.TransformListener(buf, node)
    end = time.time() + args.wait
    tf = None
    while time.time() < end and (not grids or tf is None):
        rclpy.spin_once(node, timeout_sec=0.1)
        if grids:
            try:
                tf = buf.lookup_transform(grids[-1].header.frame_id, 'base_footprint', rclpy.time.Time())
            except Exception:  # noqa: BLE001 - keep waiting for TF
                tf = None
    if not grids or tf is None:
        print(f'no costmap on {args.topic} or no TF to base_footprint')
        return 1
    grid = grids[-1]
    q = tf.transform.rotation
    yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
    px = tf.transform.translation.x + args.ahead * math.cos(yaw) - args.left * math.sin(yaw)
    py = tf.transform.translation.y + args.ahead * math.sin(yaw) + args.left * math.cos(yaw)
    info = grid.info
    res = info.resolution
    steps = int(round(args.half / res))
    print(f'{args.topic} ({grid.header.frame_id}, {res * 100:.1f} cm) around robot-frame ({args.ahead:+.2f}, {args.left:+.2f}) '
          f'= map ({px:.2f}, {py:.2f}), robot yaw {math.degrees(yaw):.0f} deg; rows north->south')
    marked = 0
    for j in range(steps, -steps - 1, -1):
        row = []
        for i in range(-steps, steps + 1):
            cx = int((px + i * res - info.origin.position.x) / res)
            cy = int((py + j * res - info.origin.position.y) / res)
            if 0 <= cx < info.width and 0 <= cy < info.height:
                v = grid.data[cy * info.width + cx]
                marked += v >= 99
                row.append(f'{v:4d}')
            else:
                row.append('   .')
        print(''.join(row))
    print(f'cells >= 99 (inscribed/lethal) in this window: {marked}')
    node.destroy_node()
    rclpy.try_shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())
