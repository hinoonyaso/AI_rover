"""Shared helper: average /imu/data_raw over a time window."""
import statistics as st
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu

COLS = ("ax", "ay", "az", "gx", "gy", "gz")


def collect(seconds, node_name="imu_calibration"):
    """Return {name: (mean, std)} for accel (m/s^2) and gyro (rad/s), plus the sample count."""
    rows = []
    if not rclpy.ok():
        rclpy.init()
    node = Node(node_name)
    node.create_subscription(
        Imu, "imu/data_raw",
        lambda m: rows.append((
            m.linear_acceleration.x, m.linear_acceleration.y, m.linear_acceleration.z,
            m.angular_velocity.x, m.angular_velocity.y, m.angular_velocity.z)),
        qos_profile_sensor_data)

    end = time.monotonic() + seconds
    while time.monotonic() < end and rclpy.ok():
        rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_node()

    if len(rows) < 10:
        raise SystemExit("no IMU data on imu/data_raw: is base_node running?")

    stats = {n: (st.mean(c), st.pstdev(c)) for n, c in zip(COLS, zip(*rows))}
    return stats, len(rows)
