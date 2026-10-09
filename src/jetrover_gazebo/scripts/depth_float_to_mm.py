#!/usr/bin/env python3
# 한글: Gazebo depth(32FC1, m)를 실기와 같은 16UC1(mm, 무효=0)로 바꾸고
#       camera_info를 depth/color 이름으로 다시 낸다.
"""
Convert Gazebo depth (32FC1 metres) to the real camera format (16UC1 mm, invalid = 0).

Republishes camera_info as /depth_cam/depth/camera_info and /depth_cam/color/camera_info with
the optical frame, so sparse_point_cloud and the perception tools run unchanged in simulation.
"""
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CameraInfo, Image

FRAME = 'depth_cam_color_optical_frame'


class DepthConv(Node):
    def __init__(self):
        super().__init__('depth_float_to_mm')
        q = qos_profile_sensor_data
        self.pub_d = self.create_publisher(Image, '/depth_cam/depth/image_raw', q)
        self.pub_ci_d = self.create_publisher(CameraInfo, '/depth_cam/depth/camera_info', q)
        self.pub_ci_c = self.create_publisher(CameraInfo, '/depth_cam/color/camera_info', q)
        self.create_subscription(Image, '/depth_cam/sim/depth_float', self.depth_cb, q)
        self.create_subscription(CameraInfo, '/depth_cam/sim/camera_info', self.info_cb, q)

    def depth_cb(self, msg):
        if msg.encoding != '32FC1':
            self.get_logger().warn(f'unexpected encoding {msg.encoding}',
                                   throttle_duration_sec=5.0)
            return
        d = np.frombuffer(msg.data, dtype=np.float32).reshape(msg.height, msg.width)
        mm = np.where(np.isfinite(d) & (d > 0), np.clip(d * 1000.0, 0, 65535), 0).astype(np.uint16)
        out = Image()
        out.header = msg.header
        out.header.frame_id = FRAME
        out.height, out.width = msg.height, msg.width
        out.encoding = '16UC1'
        out.is_bigendian = 0
        out.step = msg.width * 2
        out.data = mm.tobytes()
        self.pub_d.publish(out)

    def info_cb(self, msg):
        msg.header.frame_id = FRAME
        self.pub_ci_d.publish(msg)
        self.pub_ci_c.publish(msg)


def main():
    rclpy.init()
    rclpy.spin(DepthConv())


if __name__ == '__main__':
    main()
