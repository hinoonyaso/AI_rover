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
"""
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CameraInfo, Image, PointCloud2, PointField
from sensor_msgs_py import point_cloud2


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
        self.stride = self.get_parameter('stride').value
        self.every_nth = self.get_parameter('process_every_nth').value
        self._count = 0
        self.intrinsics = None

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
        fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
        ]
        cloud = point_cloud2.create_cloud(msg.header, fields, points)
        self.pub.publish(cloud)


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
