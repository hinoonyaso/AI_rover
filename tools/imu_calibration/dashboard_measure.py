#!/usr/bin/python3
"""Measure a stationary gyro candidate using the running base node.

한글: 실행 중인 베이스 노드와 정지 IMU에서 보정 후보를 측정한다.
"""
import json
import sys
import time

import rclpy
from rcl_interfaces.srv import GetParameters
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu
from calibration_math import gyro_candidate


def main():
    """Read existing bias twice and observe IMU without writes.

    한글: 쓰기 없이 현재 bias를 두 번 읽고 IMU를 관측한다.
    """
    rclpy.init()
    node = Node('jetinspect_gyro_measure')
    try:
        client = node.create_client(GetParameters, '/base_node/get_parameters')
        if not client.wait_for_service(timeout_sec=5):
            raise ValueError('base_node_unavailable')
        def read_bias():
            request = GetParameters.Request()
            request.names = ['gyro_bias']
            future = client.call_async(request)
            rclpy.spin_until_future_complete(node, future, timeout_sec=5)
            if not future.done() or future.result() is None:
                raise ValueError('bias_unavailable')
            values = future.result().values
            if len(values) != 1 or values[0].type != 8:
                raise ValueError('bias_unavailable')
            return list(values[0].double_array_value)
        before = read_bias()
        publishers = node.get_publishers_info_by_topic('/imu/data_raw')
        if len(publishers) != 1 or publishers[0].node_name != 'base_node' or publishers[0].node_namespace != '/':
            raise ValueError('imu_source_unconfirmed')
        samples = []
        frames = set()
        stamps = []
        received = []
        def receive(msg):
            stamp = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
            if stamp <= 0 or (stamps and stamp <= stamps[-1]):
                return
            stamps.append(stamp)
            received.append(time.monotonic())
            samples.append([msg.angular_velocity.x, msg.angular_velocity.y, msg.angular_velocity.z])
            frames.add(msg.header.frame_id)
        node.create_subscription(Imu, '/imu/data_raw', receive, qos_profile_sensor_data)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        after = read_bias()
        publishers = node.get_publishers_info_by_topic('/imu/data_raw')
        if len(publishers) != 1 or publishers[0].node_name != 'base_node' or publishers[0].node_namespace != '/':
            raise ValueError('imu_source_unconfirmed')
        if len(received) < 2 or received[-1] - received[0] < 8:
            raise ValueError('insufficient_samples')
        if len(frames) != 1 or not next(iter(frames), ''):
            raise ValueError('frame_unconfirmed')
        result = gyro_candidate(samples, before, after, min_samples=50)
        result.update({'frame_id': next(iter(frames)), 'duration_s': 10, 'source': '/imu/data_raw'})
        print(json.dumps({'result': result}, allow_nan=False), flush=True)
    except (ValueError, RuntimeError) as error:
        print(json.dumps({'error': str(error)}), flush=True)
        sys.exit(1)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__': main()
