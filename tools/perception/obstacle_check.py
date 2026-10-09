#!/usr/bin/env python3
# 한글: depth 장애물 점(/depth_cam/depth/points_sparse)이 로봇 기준 어디에 몇 개 잡히는지 보여준다. 읽기만 한다.
#       상자를 놓고 실행해서 가까운/중간/먼 위치에서 검출되는지 확인할 때 쓴다(홈 자세 변경 후 확인용).
"""Report where the depth obstacle points land in base_footprint (read-only).

Usage: python3 tools/perception/obstacle_check.py [--seconds 3]
Points include the 0.15 m extrusion behind each obstacle face (sparse_point_cloud extrude_depth_m),
so x_min is the face the camera actually sees.
"""
import argparse
import time

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2
import tf2_ros


def quat_to_rot(q):
    x, y, z, w = q.x, q.y, q.z, q.w
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--seconds', type=float, default=3.0)
    args = ap.parse_args()
    rclpy.init()
    node = Node('obstacle_check')
    clouds = []
    node.create_subscription(PointCloud2, '/depth_cam/depth/points_sparse',
                             lambda m: clouds.append(m), 10)
    buf = tf2_ros.Buffer()
    tf2_ros.TransformListener(buf, node)
    t0 = time.time()
    while time.time() - t0 < args.seconds:
        rclpy.spin_once(node, timeout_sec=0.05)
    if not clouds:
        raise SystemExit('no /depth_cam/depth/points_sparse (home-pose gate closed?)')
    counts = [c.width * c.height for c in clouds]
    m = max(clouds, key=lambda c: c.width * c.height)
    print(f'frames {len(clouds)}, points/frame min {min(counts)} max {max(counts)}')
    if m.width * m.height == 0:
        print('no obstacle points')
        return
    tf = None
    while tf is None and time.time() - t0 < args.seconds + 10:
        try:
            tf = buf.lookup_transform('base_footprint', m.header.frame_id, rclpy.time.Time())
        except Exception:  # noqa: BLE001
            rclpy.spin_once(node, timeout_sec=0.1)
    if tf is None:
        raise SystemExit('no TF base_footprint <- ' + m.header.frame_id)
    p = np.array([[q[0], q[1], q[2]] for q in point_cloud2.read_points(
        m, field_names=('x', 'y', 'z'), skip_nans=True)], dtype=float)
    r = quat_to_rot(tf.transform.rotation)
    t = np.array([tf.transform.translation.x, tf.transform.translation.y,
                  tf.transform.translation.z])
    b = p @ r.T + t
    print(f'x (forward) min {b[:, 0].min():.2f}  max {b[:, 0].max():.2f} m   '
          f'(robot front at 0.18 m)')
    print(f'y (left)    min {b[:, 1].min():+.2f}  max {b[:, 1].max():+.2f} m')
    print(f'z (height)  min {b[:, 2].min():.2f}  max {b[:, 2].max():.2f} m')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
