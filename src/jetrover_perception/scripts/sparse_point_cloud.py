#!/usr/bin/env python3
# 한글: 간격을 둔 depth 영상으로 만드는 가벼운 PointCloud2 + 기준 depth 대비 새 물체만 남기는 self-filter.
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

Self-filtering (2026-10-05, checklist 8.12, troubleshooting/023): with the arm in its home pose
the camera sees the robot's own wheel (that is the point -- it closes the near-field blind
zone, see base.yaml's arm_home_pose_rad comment). Feeding those self-points into Nav2's
obstacle_layer would mark the robot's own footprint as occupied and reintroduce
troubleshooting/020's "Start occupied" problem.

The first attempt at this (transform each point into base_footprint and drop anything inside
the robot's footprint rectangle) was wrong: a real external obstacle placed ~35cm in front of
the robot projects into that same rectangle too (the camera is forward-mounted and tilted
down, so near-field obstacles and the robot's own wheel land in overlapping XY once
transformed), and the robot's wheel height (~9.7cm) overlaps the height range of a real low
obstacle -- so neither XY nor height alone can tell them apart (troubleshooting/023: this
let the robot push an obstacle it never even published as a point).

Instead this compares each pixel's depth against a one-time reference depth image captured
with the arm in its home pose and nothing in front of the robot (`depth_background_ref.npy` --
recapture if the home pose changes). The robot's own wheel/chassis always measures ~the same
depth as that reference (nothing moved). Anything that now measures *closer* than the
reference by more than a margin is something new between the camera and that known
background -- a real obstacle, regardless of where it lands in XY. This has no failure mode
tied to the obstacle's position or height matching the wheel's.
"""
import os

from ament_index_python.packages import get_package_share_directory
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CameraInfo, Image, PointCloud2, PointField
from sensor_msgs_py import point_cloud2


class SparsePointCloud(Node):
    def __init__(self):
        super().__init__('sparse_point_cloud')
        # 한글: stride=8이면 640x360 depth에서 최대 약 3600점(전체는 약 23만점). 3D 투영 연산을 점 수가 적은 단계에서만 한다.
        self.declare_parameter('stride', 8)
        # 한글: 발행 속도를 4프레임에 1번으로 낮춘다(원격 RViz에서 TF 타이밍 경쟁 방지).
        # Publishing at the full depth rate (~25-30Hz) meant a remote viewer
        # (RViz over WiFi) sometimes couldn't resolve the full TF chain in
        # time for a given message's exact stamp -- same class of cross-
        # machine timing race as troubleshooting/018, just for this topic.
        # Harmless (the viewer keeps showing the last good cloud) but noisy.
        # A live view doesn't need more than a few Hz.
        self.declare_parameter('process_every_nth', 4)
        default_ref = os.path.join(
            get_package_share_directory('jetrover_perception'),
            'config', 'depth_background_ref.npy')
        self.declare_parameter('background_depth_path', default_ref)
        # mm, margin above typical depth-sensor noise at this range (troubleshooting/023).
        # 30 -> 60 (2026-10-05): with the wrist-raised home pose the camera sees the far floor, where
        # the noise exceeds 30 mm (~12 false points/frame, 0.9 at 60). A real box is >100 mm closer.
        # 한글: 손목을 든 새 홈 자세는 먼 바닥까지 보여서 노이즈가 커짐 → 거짓 점이 30mm에서 프레임당 약 12개, 60mm에서 약 1개.
        self.declare_parameter('background_margin_mm', 60)
        # 2026-10-05 (회피 시험): the camera only sees an obstacle's FRONT face, so the space behind it
        # stays "free" in the costmap and the robot (and line waypoints) drove into the box body.
        # Every obstacle point is therefore extended along its viewing ray by `extrude_depth_m`.
        # 한글: 카메라는 장애물 앞면만 보므로 시선 방향으로 뒤쪽 extrude_depth_m(기본 0.3m)까지 점을 복제해
        # 몸통도 점유로 취급한다(상자를 치고 지나가던 문제).
        self.declare_parameter('extrude_depth_m', 0.3)
        self.declare_parameter('extrude_step_m', 0.1)
        self.extrude_depth = self.get_parameter('extrude_depth_m').value
        self.extrude_step = self.get_parameter('extrude_step_m').value
        self.stride = self.get_parameter('stride').value
        self.every_nth = self.get_parameter('process_every_nth').value
        self.background_margin_mm = self.get_parameter('background_margin_mm').value
        ref_path = self.get_parameter('background_depth_path').value
        # 한글: 기준 depth 이미지(로봇 홈 자세, 앞에 아무것도 없는 상태)를 불러온다. 홈 자세를 바꾸면 다시 찍어야 한다.
        self.background = np.load(ref_path)
        self.background_sparse = self.background[::self.stride, ::self.stride]
        self.get_logger().info(
            f'loaded background depth reference from {ref_path}, '
            f'valid fraction={float((self.background > 0).mean()):.3f}')
        self._count = 0
        self.intrinsics = None

        self.pub = self.create_publisher(PointCloud2, 'depth/points_sparse', 10)
        self.create_subscription(
            CameraInfo, 'depth/camera_info', self._info_cb, qos_profile_sensor_data)
        self.create_subscription(
            Image, 'depth/image_raw', self._depth_cb, qos_profile_sensor_data)

    # 한글: 카메라 내부 파라미터(fx, fy, cx, cy) 저장.
    def _info_cb(self, msg):
        self.intrinsics = (msg.k[0], msg.k[4], msg.k[2], msg.k[5])  # fx, fy, cx, cy

    # 한글: 기준 depth보다 margin 이상 '가까운' 픽셀만 장애물로 본다. 로봇 자신의 바퀴/섀시나 바닥은 기준과 같아서 제거되고, XY/높이 필터가 실제 장애물까지 지우던 문제(troubleshooting/023)를 피한다.
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
        # 한글: mm → m
        z = depth_sparse.astype(np.float32) / 1000.0  # mm -> m

        # Closer than the known background (wheel/floor with nothing in front) by more than
        # the margin -> something new is there now, real obstacle. Equal to or farther than
        # the background -> the robot's own wheel/chassis or ordinary floor, drop it.
        bg = self.background_sparse
        valid = (
            (depth_sparse > 0) & (bg > 0) &
            (depth_sparse.astype(np.int32) < bg.astype(np.int32) - self.background_margin_mm))
        x = (us[valid] - cx) * z[valid] / fx
        y = (vs[valid] - cy) * z[valid] / fy
        z = z[valid]
        points = np.stack([x, y, z], axis=-1)
        if self.extrude_depth > 0.0 and len(points) > 0:
            norm = np.linalg.norm(points, axis=1, keepdims=True)
            rays = points / np.maximum(norm, 1e-6)
            layers = [points]
            d = self.extrude_step
            while d <= self.extrude_depth + 1e-6:
                layers.append(points + rays * d)  # 같은 시선 위의 더 먼 점들
                d += self.extrude_step
            points = np.concatenate(layers, axis=0)

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
