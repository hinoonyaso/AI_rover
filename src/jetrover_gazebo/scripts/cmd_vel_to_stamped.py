#!/usr/bin/env python3
# 한글: Nav2/키보드의 /cmd_vel(Twist)을 mecanum_drive_controller가 받는 TwistStamped로 바꿔 전달한다(시뮬레이션 전용).
"""Relay /cmd_vel (Twist, as Nav2 sends) to the mecanum controller reference (TwistStamped)."""
from geometry_msgs.msg import Twist, TwistStamped
import rclpy
from rclpy.node import Node


class Relay(Node):
    def __init__(self):
        super().__init__('cmd_vel_to_stamped')
        self.declare_parameter('frame_id', 'base_footprint')
        self.frame = self.get_parameter('frame_id').value
        self.pub = self.create_publisher(TwistStamped, '/mecanum_drive_controller/reference', 10)
        self.create_subscription(Twist, '/cmd_vel', self.cb, 10)

    def cb(self, msg):
        out = TwistStamped()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = self.frame
        out.twist = msg
        self.pub.publish(out)


def main():
    rclpy.init()
    rclpy.spin(Relay())


if __name__ == '__main__':
    main()
