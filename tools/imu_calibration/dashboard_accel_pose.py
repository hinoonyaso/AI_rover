#!/usr/bin/python3
"""Collect one stationary IMU pose without changing device configuration.

한글: 장치 설정 변경 없이 IMU 정지 자세 한 개를 수집한다.
"""
import json
import sys
import time
import rclpy
from rclpy.node import Node
from rcl_interfaces.srv import GetParameters
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu
from calibration_math import accel_pose_summary, gyro_candidate


def main():
    """Observe one pose and reject movement or uncertain source.

    한글: 자세 하나를 관찰하고 움직임이나 불확실한 발행자를 거부한다.
    """
    if len(sys.argv) != 2:
        raise SystemExit('pose required')
    rclpy.init()
    node = Node('jetinspect_accel_measure')
    try:
        client = node.create_client(GetParameters, '/base_node/get_parameters')
        if not client.wait_for_service(timeout_sec=5):
            raise ValueError('base_node_unavailable')
        def read_calibration():
            request = GetParameters.Request()
            request.names = ['accel_offset_m_s2', 'accel_scale']
            future = client.call_async(request)
            rclpy.spin_until_future_complete(node, future, timeout_sec=5)
            if not future.done() or future.result() is None:
                raise ValueError('accel_settings_unavailable')
            values = future.result().values
            if len(values) != 2 or any(v.type != 8 or len(v.double_array_value) != 3 for v in values):
                raise ValueError('accel_settings_unavailable')
            return [list(v.double_array_value) for v in values]
        before = read_calibration()
        def publisher():
            publishers = node.get_publishers_info_by_topic('/imu/data_raw')
            if len(publishers) != 1 or publishers[0].node_name != 'base_node' or publishers[0].node_namespace != '/':
                raise ValueError('imu_source_unconfirmed')
            return bytes(publishers[0].endpoint_gid).hex()
        until = time.monotonic() + 5
        while time.monotonic() < until:
            rclpy.spin_once(node, timeout_sec=.1)
            try:
                source_id = publisher()
                break
            except ValueError:
                continue
        else:
            raise ValueError('imu_source_unconfirmed')
        acceleration, rotation, timestamps, receive_times, frames = [], [], [], [], set()
        def receive(msg):
            stamp = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
            if stamp <= 0 or (timestamps and stamp <= timestamps[-1]): return
            timestamps.append(stamp)
            receive_times.append(time.monotonic())
            acceleration.append([msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z])
            rotation.append([msg.angular_velocity.x, msg.angular_velocity.y, msg.angular_velocity.z])
            frames.add(msg.header.frame_id)
        node.create_subscription(Imu, '/imu/data_raw', receive, qos_profile_sensor_data)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=.1)
        if publisher() != source_id: raise ValueError('source_changed')
        after = read_calibration()
        if before != after: raise ValueError('accel_settings_changed')
        if len(receive_times) < 2 or receive_times[-1] - receive_times[0] < 4: raise ValueError('insufficient_samples')
        if len(frames) != 1 or not next(iter(frames), ''): raise ValueError('frame_unconfirmed')
        gyro = gyro_candidate(rotation, [0]*3, [0]*3, min_samples=50)
        if any(abs(v) > .08 for v in gyro['residual_mean']): raise ValueError('not_stationary')
        result = accel_pose_summary(acceleration, sys.argv[1])
        result.update({'frame_id': next(iter(frames)), 'source_id': source_id, 'duration_s': 5,
                       'current_offset_m_s2':before[0], 'current_scale':before[1]})
        print(json.dumps({'result': result}, allow_nan=False), flush=True)
    except (ValueError, RuntimeError) as error:
        print(json.dumps({'error': str(error)}), flush=True)
        sys.exit(1)
    finally:
        node.destroy_node(); rclpy.shutdown()


if __name__ == '__main__': main()
