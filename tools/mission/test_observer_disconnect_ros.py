"""Test camera stream loss through isolated ROS without a robot.

한글: 로봇 없이 격리 ROS에서 카메라 영상 중단을 시험한다.
"""
import os
import threading
import time

import numpy as np
import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image

from stack_light_observer import observe


def main():
    """Stop a camera stream before enough samples arrive. / 충분한 표본 전에 영상 발행을 중단한다."""
    if (os.environ.get('ROS_DOMAIN_ID') != '98' or
            os.environ.get('ROS_AUTOMATIC_DISCOVERY_RANGE') != 'LOCALHOST' or
            os.environ.get('RMW_IMPLEMENTATION') != 'rmw_fastrtps_cpp' or
            any(os.environ.get(name) for name in ('ROS_STATIC_PEERS', 'ROS_DISCOVERY_SERVER',
                'FASTRTPS_DEFAULT_PROFILES_FILE', 'FASTDDS_DEFAULT_PROFILES_FILE', 'CYCLONEDDS_URI'))):
        raise RuntimeError('isolated ROS domain 98 is required')
    rclpy.init()
    publisher_node = rclpy.create_node('disconnect_test_camera')
    observer_node = rclpy.create_node('disconnect_test_observer')
    publisher = publisher_node.create_publisher(Image, '/depth_cam/color/image_raw', qos_profile_sensor_data)
    sent = []
    received = []
    observer_node.create_subscription(Image, '/depth_cam/color/image_raw', lambda msg: received.append(1),
                                      qos_profile_sensor_data)

    def publish_then_stop():
        until = time.monotonic() + 3
        while publisher.get_subscription_count() == 0 and time.monotonic() < until:
            time.sleep(.05)
        image = np.zeros((360, 640, 3), dtype=np.uint8)
        image[50:80, 205:235] = (255, 0, 0)
        image[100:130, 210:240] = (47, 47, 0)
        image[150:180, 215:245] = (0, 255, 0)
        for _ in range(4):
            msg = Image()
            msg.header.stamp = publisher_node.get_clock().now().to_msg()
            msg.height, msg.width, msg.encoding, msg.step = 360, 640, 'rgb8', 1920
            msg.data = image.tobytes()
            publisher.publish(msg)
            sent.append(1)
            time.sleep(.35)

    thread = threading.Thread(target=publish_then_stop)
    thread.start()
    try:
        result = observe(observer_node, lambda: False, timeout=4)
        thread.join(timeout=5)
        print(f'published={len(sent)} received={len(received)} result={result}', flush=True)
        if len(sent) != 4 or len(received) < 3 or result.get('status') != 'unavailable' or result.get('reason') != 'inspection_unconfirmed':
            raise RuntimeError('camera disconnect was not handled as unconfirmed')
    finally:
        thread.join(timeout=5)
        observer_node.destroy_node()
        publisher_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
