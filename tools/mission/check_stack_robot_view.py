"""Inspect the stationary simulated robot's camera at the trial pose.

한글: 정지한 가상 로봇의 카메라를 시험 자세에서 점검한다.
"""
import json
import os
from pathlib import Path
import sys
import time

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from gazebo_nav_trial import require_simulation

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src/jetrover_perception/scripts'))
from stack_light import classify  # noqa: E402


def main():
    """Collect camera frames and test fixed regions. / 카메라 영상의 고정 영역을 판정한다."""
    require_simulation()
    rclpy.init()
    node = Node('stack_light_robot_view_check')
    frames = []

    def receive(msg):
        now = time.monotonic()
        if frames and now - frames[-1][0] < .3:
            return
        if msg.encoding != 'rgb8' or msg.step != msg.width * 3:
            return
        # Restart the observation window after a dropped or delayed frame.
        # 한글: 영상 간격이 길어지면 관측 창을 다시 시작한다.
        if frames and now - frames[-1][0] > .6:
            frames.clear()
        frames.append((now, np.frombuffer(msg.data, dtype=np.uint8).reshape(
            msg.height, msg.width, 3).copy()))

    node.create_subscription(Image, '/depth_cam/color/image_raw', receive, qos_profile_sensor_data)
    try:
        deadline = time.monotonic() + 45
        while (len(frames) < 9 or frames[-1][0] - frames[0][0] < 2) and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=.1)
        if len(frames) < 9 or frames[-1][0] - frames[0][0] < 2:
            raise RuntimeError('insufficient camera frames')
        image = frames[-1][1]
        cv2.imwrite('/tmp/stack_robot_view_test.png', cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        regions = {'red': (312, 100, 16, 16), 'yellow': (312, 172, 16, 16),
                   'green': (312, 244, 16, 16)}
        result = classify(frames, regions, time.monotonic())
        print(json.dumps({'result': result, 'intervals_s': [round(b[0] - a[0], 3)
                         for a, b in zip(frames, frames[1:])]}))
        if [result[name]['state'] for name in regions] != ['on', 'off', 'on']:
            raise RuntimeError('robot camera fixture result mismatch')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
