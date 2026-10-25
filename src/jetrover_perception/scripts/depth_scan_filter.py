#!/usr/bin/env python3
# 한글: depth 장애물 점 중 LiDAR 점 근처(radius_m 안)에 있는 점을 버리고 나머지(LiDAR가 못 보는 낮은 물체)만 다시 보낸다.
#       사람 다리처럼 LiDAR에 잡히는 키 큰 물체는 LiDAR 레이어가 표시·지우기를 맡는다. depth에 남기면 카메라보다 높은 3D 칸은
#       바닥 광선으로 지울 수 없어 사람이 떠난 뒤에도 흔적이 남았다(2026-10-25 실기, troubleshooting/055).
"""
Drop depth obstacle points that lie near a current LiDAR return.

The depth layer should only hold what the LiDAR cannot see (low objects such as a 12 cm box). Tall
obstacles (legs) are already marked and, importantly, cleared by the LiDAR layer; their depth marks
above the camera's floor rays could never be cleared and stayed after a person left.

Subscribes `points_in` (sensor_msgs/PointCloud2, any frame) and `scan` (LaserScan). Points within
`radius_m` (horizontal, in `base_frame`) of any return of a scan newer than `scan_max_age_s` are
removed; the rest is republished on `points_out` in the input frame. Without a fresh scan the cloud
passes through unchanged (fail safe: never hide obstacles because the LiDAR is silent).
"""
import time

import numpy as np


def keep_mask(points_xy, scan_xy, radius):
    """Return a bool mask of points farther than radius (m) from every scan point (2D).

    한글: LiDAR 점에서 radius보다 먼 depth 점만 True.
    """
    points_xy = np.asarray(points_xy, float).reshape(-1, 2)
    scan_xy = np.asarray(scan_xy, float).reshape(-1, 2)
    if len(points_xy) == 0 or len(scan_xy) == 0:
        return np.ones(len(points_xy), bool)
    # 격자 해시 대신 덩어리로 거리 계산(점 수 수천 x 수백) / chunked brute force, a few thousand x a few hundred
    keep = np.ones(len(points_xy), bool)
    r2 = radius * radius
    for i in range(0, len(points_xy), 2048):
        p = points_xy[i:i + 2048]
        d2 = ((p[:, None, :] - scan_xy[None, :, :]) ** 2).sum(-1)
        keep[i:i + 2048] = d2.min(axis=1) > r2
    return keep


def main():
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import LaserScan, PointCloud2
    from sensor_msgs_py import point_cloud2
    import tf2_ros

    def tf_matrix(buf, target, source):
        tr = buf.lookup_transform(target, source, rclpy.time.Time())
        q = tr.transform.rotation
        x, y, z, w = q.x, q.y, q.z, q.w
        rot = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        t = tr.transform.translation
        return rot, np.array([t.x, t.y, t.z])

    class DepthScanFilter(Node):
        def __init__(self):
            super().__init__('depth_scan_filter')
            self.radius = float(self.declare_parameter('radius_m', 0.10).value)
            self.max_age = float(self.declare_parameter('scan_max_age_s', 0.5).value)
            self.base = self.declare_parameter('base_frame', 'base_footprint').value
            self.buf = tf2_ros.Buffer()
            self.tfl = tf2_ros.TransformListener(self.buf, self)
            self.scan_xy, self.scan_t = None, 0.0
            self.pub = self.create_publisher(PointCloud2, 'points_out', 10)
            self.create_subscription(LaserScan, 'scan', self.on_scan, qos_profile_sensor_data)
            self.create_subscription(PointCloud2, 'points_in', self.on_points, 10)
            self.dropped = 0
            self.get_logger().info(f'depth_scan_filter: radius {self.radius} m, base {self.base}')

        def on_scan(self, m):
            try:
                rot, t = tf_matrix(self.buf, self.base, m.header.frame_id)
            except Exception:  # noqa: BLE001
                return
            a = m.angle_min + np.arange(len(m.ranges)) * m.angle_increment
            r = np.array(m.ranges)
            ok = np.isfinite(r) & (r > m.range_min) & (r < m.range_max)
            pts = np.stack([r[ok] * np.cos(a[ok]), r[ok] * np.sin(a[ok]), np.zeros(ok.sum())], 1)
            self.scan_xy = (pts @ rot.T + t)[:, :2]
            self.scan_t = time.monotonic()

        def on_points(self, m):
            pts = np.array([(p[0], p[1], p[2]) for p in point_cloud2.read_points(
                m, field_names=('x', 'y', 'z'), skip_nans=True)], dtype=np.float32).reshape(-1, 3)
            fresh = self.scan_xy is not None and time.monotonic() - self.scan_t < self.max_age
            if len(pts) and fresh:
                try:
                    rot, t = tf_matrix(self.buf, self.base, m.header.frame_id)
                    keep = keep_mask((pts @ rot.T + t)[:, :2], self.scan_xy, self.radius)
                    self.dropped += int((~keep).sum())
                    pts = pts[keep]
                except Exception:  # noqa: BLE001
                    pass       # TF missing: pass through (fail safe) / TF 없으면 그대로 통과
            self.pub.publish(point_cloud2.create_cloud(m.header, m.fields[:3], pts))

    rclpy.init()
    node = DepthScanFilter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
