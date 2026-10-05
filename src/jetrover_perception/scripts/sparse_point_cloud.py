#!/usr/bin/env python3
"""Lightweight PointCloud2 from a strided (downsampled) depth image.

The camera driver's own enable_point_cloud computes a full-resolution cloud
(up to ~230k points for 640x360) internally and was the direct cause of
troubleshooting/019's silent hangs under the full Nav2 stack -- the heavy
work happens before anything is even published, so downsampling downstream
(e.g. on the host, or with a voxel filter after the fact) doesn't help.

This instead samples every `stride`-th pixel from the already-working
depth/image_raw BEFORE projecting to 3D, so the expensive part (per-pixel
XYZ math) only ever runs on a small fraction of the points. stride=8 on
640x360 depth gives at most 80x45 = 3600 points, vs ~230k for the full
cloud -- close to what a Nav2 voxel/obstacle layer would keep anyway after
its own internal downsampling, so there is little practical loss for that
use case (see PRD 3D XYZ / Safety Manager pipelines, neither of which needs
a dense cloud).

Self-filtering (2026-10-05, checklist 8.12): with the arm in its home pose
the camera sees the robot's own wheel (that is the point -- it closes the
near-field blind zone, see base.yaml's arm_home_pose_rad comment). Feeding
those self-points into Nav2's obstacle_layer would mark the robot's own
footprint as occupied and reintroduce troubleshooting/020's "Start
occupied" problem. Points are transformed into base_footprint and dropped
if they fall inside the configured footprint rectangle before publishing.
"""
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CameraInfo, Image, PointCloud2, PointField
from sensor_msgs_py import point_cloud2
import tf2_ros
from tf2_ros import TransformException


class SparsePointCloud(Node):
    def __init__(self):
        super().__init__('sparse_point_cloud')
        self.declare_parameter('stride', 8)
        # Publishing at the full depth rate (~25-30Hz) meant a remote viewer
        # (RViz over WiFi) sometimes couldn't resolve the full TF chain in
        # time for a given message's exact stamp -- same class of cross-
        # machine timing race as troubleshooting/018, just for this topic.
        # Harmless (the viewer keeps showing the last good cloud) but noisy.
        # A live view doesn't need more than a few Hz.
        self.declare_parameter('process_every_nth', 4)
        # Must match nav2_params.yaml's footprint (jetrover_navigation/config).
        self.declare_parameter('self_filter_frame', 'base_footprint')
        self.declare_parameter('footprint_x', [0.16, -0.16])
        self.declare_parameter('footprint_y', [0.18, -0.18])
        self.stride = self.get_parameter('stride').value
        self.every_nth = self.get_parameter('process_every_nth').value
        self.self_filter_frame = self.get_parameter('self_filter_frame').value
        fx_lim = self.get_parameter('footprint_x').value
        fy_lim = self.get_parameter('footprint_y').value
        self.fp_x_min, self.fp_x_max = min(fx_lim), max(fx_lim)
        self.fp_y_min, self.fp_y_max = min(fy_lim), max(fy_lim)
        self._count = 0
        self.intrinsics = None

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        self.pub = self.create_publisher(PointCloud2, 'depth/points_sparse', 10)
        self.create_subscription(
            CameraInfo, 'depth/camera_info', self._info_cb, qos_profile_sensor_data)
        self.create_subscription(
            Image, 'depth/image_raw', self._depth_cb, qos_profile_sensor_data)

    def _info_cb(self, msg):
        self.intrinsics = (msg.k[0], msg.k[4], msg.k[2], msg.k[5])  # fx, fy, cx, cy

    def _depth_cb(self, msg):
        self._count += 1
        if self._count % self.every_nth != 0:
            return
        if self.intrinsics is None:
            return
        fx, fy, cx, cy = self.intrinsics

        depth = np.frombuffer(msg.data, dtype=np.uint16).reshape(msg.height, msg.width)
        depth_sparse = depth[::self.stride, ::self.stride]

        vs, us = np.indices(depth_sparse.shape)
        us = us * self.stride
        vs = vs * self.stride
        z = depth_sparse.astype(np.float32) / 1000.0  # mm -> m

        valid = depth_sparse > 0
        x = (us[valid] - cx) * z[valid] / fx
        y = (vs[valid] - cy) * z[valid] / fy
        z = z[valid]
        points = np.stack([x, y, z], axis=-1)

        points = self._drop_self_points(points, msg.header.frame_id)
        if points is None:
            return  # TF not ready yet; skip this frame rather than publish unfiltered

        fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
        ]
        cloud = point_cloud2.create_cloud(msg.header, fields, points)
        self.pub.publish(cloud)

    def _drop_self_points(self, points_cam, cam_frame):
        try:
            t = self.tf_buffer.lookup_transform(
                self.self_filter_frame, cam_frame, rclpy.time.Time())
        except TransformException as e:
            self.get_logger().warn(
                f'self-filter TF unavailable ({cam_frame}->{self.self_filter_frame}): {e}',
                throttle_duration_sec=5.0)
            return None

        q = t.transform.rotation
        rot = _quat_to_matrix(q.x, q.y, q.z, q.w)
        trans = np.array([
            t.transform.translation.x, t.transform.translation.y, t.transform.translation.z])
        points_base = points_cam @ rot.T + trans

        inside_footprint = (
            (points_base[:, 0] > self.fp_x_min) & (points_base[:, 0] < self.fp_x_max) &
            (points_base[:, 1] > self.fp_y_min) & (points_base[:, 1] < self.fp_y_max))
        return points_cam[~inside_footprint]


def _quat_to_matrix(x, y, z, w):
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def main():
    rclpy.init()
    node = SparsePointCloud()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
