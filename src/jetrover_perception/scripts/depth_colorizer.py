#!/usr/bin/env python3
"""Republish raw 16UC1 depth (mm) as a colorized bgr8 image for viewing.

web_video_server/rqt_image_view can't render 16UC1 directly (cv_bridge has
no color conversion for it). This clamps/normalizes to [min_range_mm,
max_range_mm] and applies an OpenCV colormap so it streams like a normal
image. See troubleshooting/019 for why depth_cam's point cloud stays off by
default -- this node is a cheap alternative that only needs the already-on
depth stream, no extra camera load.
"""
import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image


class DepthColorizer(Node):
    def __init__(self):
        super().__init__('depth_colorizer')
        self.declare_parameter('min_range_mm', 200)
        self.declare_parameter('max_range_mm', 3000)
        # Processing every frame (30Hz) measurably competed with the camera
        # driver's own CPU use and slowed RGB down (troubleshooting/019's
        # resource-contention issue again, this time self-inflicted). A
        # live-view doesn't need more than this.
        self.declare_parameter('process_every_nth', 3)
        self.min_range = self.get_parameter('min_range_mm').value
        self.max_range = self.get_parameter('max_range_mm').value
        self.every_nth = self.get_parameter('process_every_nth').value
        self._count = 0

        self.bridge = CvBridge()
        self.pub = self.create_publisher(Image, 'depth/image_colorized', 10)
        self.create_subscription(Image, 'depth/image_raw', self._cb, 10)

    def _cb(self, msg):
        self._count += 1
        if self._count % self.every_nth != 0:
            return
        depth = self.bridge.imgmsg_to_cv2(msg, desired_encoding='16UC1')
        clamped = np.clip(depth, self.min_range, self.max_range).astype(np.float32)
        normalized = (clamped - self.min_range) / (self.max_range - self.min_range)
        gray8 = (normalized * 255).astype(np.uint8)
        gray8[depth == 0] = 0  # no-return pixels stay black
        colorized = cv2.applyColorMap(gray8, cv2.COLORMAP_JET)

        out = self.bridge.cv2_to_imgmsg(colorized, encoding='bgr8')
        out.header = msg.header
        self.pub.publish(out)


def main():
    rclpy.init()
    node = DepthColorizer()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
