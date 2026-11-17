#!/usr/bin/python3
"""Capture one live ROS RGB frame as a temporary JPEG.

한글: ROS RGB 영상의 새 프레임 한 장을 임시 JPEG로 저장한다.
"""
import sys
import time
import cv2
from cv_bridge import CvBridge
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


def main():
    """Wait at most ten seconds for a new sensor frame. / 새 프레임을 최대 10초 기다린다."""
    rclpy.init()
    node = Node('voice_camera_snapshot')
    frame = []
    bridge = CvBridge()
    def receive(message):
        if not frame:
            frame.append(bridge.imgmsg_to_cv2(message, desired_encoding='bgr8'))
    node.create_subscription(Image, '/depth_cam/color/image_raw', receive, qos_profile_sensor_data)
    try:
        deadline = time.monotonic() + 10
        while not frame and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.2)
        if not frame or not cv2.imwrite(sys.argv[1], frame[0], [cv2.IMWRITE_JPEG_QUALITY, 85]):
            raise RuntimeError('카메라 프레임을 저장하지 못했습니다')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
