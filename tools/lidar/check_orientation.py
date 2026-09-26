#!/usr/bin/env python3
"""Where does the LiDAR see the nearest object, in the robot's base_link frame?

Run with the LiDAR driver and robot_state_publisher up (jetrover_bringup lidar.launch.py). Put an
object (e.g. a box) near the robot, then:  python3 check_orientation.py [seconds]
Angles are reported in base_link (0 deg = robot forward, +90 deg = robot left, REP-103), obtained
from the real lidar_frame -> base_link transform, so it checks the URDF mounting yaw end to end.
"""
import math
import sys
import time

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from tf2_ros import Buffer, TransformListener

MAX_RANGE = 1.5  # only look at things closer than this (m)


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def main():
    seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0
    rclpy.init()
    n = Node('lidar_orientation')
    buf = Buffer()
    TransformListener(buf, n)
    scans = []
    n.create_subscription(LaserScan, 'scan', scans.append, qos_profile_sensor_data)
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        rclpy.spin_once(n, timeout_sec=0.05)
    if not scans:
        sys.exit('no /scan: is the LiDAR driver running?')

    frame = scans[-1].header.frame_id
    tf = buf.lookup_transform('base_link', frame, rclpy.time.Time(), Duration(seconds=2.0))
    yaw = yaw_of(tf.transform.rotation)
    tx, ty = tf.transform.translation.x, tf.transform.translation.y
    print(f'{len(scans)} scans; TF base_link <- {frame}: yaw {math.degrees(yaw):+.0f} deg, '
          f'offset ({tx:+.3f}, {ty:+.3f}) m')

    pts = []
    for m in scans:
        for i, r in enumerate(m.ranges):
            if math.isfinite(r) and m.range_min <= r <= min(m.range_max, MAX_RANGE):
                a = m.angle_min + i * m.angle_increment
                pts.append((tx + r * math.cos(a + yaw), ty + r * math.sin(a + yaw)))
    if not pts:
        sys.exit(f'nothing within {MAX_RANGE} m')
    # robot-centred polar view of the closest returns
    polar = sorted((math.hypot(x, y), math.degrees(math.atan2(y, x))) for x, y in pts)
    near = polar[:max(5, len(polar) // 20)]
    mean_a = math.degrees(math.atan2(sum(math.sin(math.radians(a)) for _, a in near),
                                     sum(math.cos(math.radians(a)) for _, a in near)))
    print(f'closest returns (base_link): nearest {near[0][0]:.2f} m; direction of the nearest '
          f'cluster {mean_a:+.0f} deg  (0 = forward, +90 = left, 180 = behind)')
    sectors = {}
    for r, a in polar:
        k = int(((a + 22.5) % 360) // 45)
        sectors[k] = min(sectors.get(k, 99.0), r)
    label = ['front', 'front-left', 'left', 'rear-left', 'rear', 'rear-right', 'right', 'front-right']
    print('nearest per sector:', {label[k]: round(sectors[k], 2) for k in sorted(sectors)})
    rclpy.shutdown()


if __name__ == '__main__':
    main()
