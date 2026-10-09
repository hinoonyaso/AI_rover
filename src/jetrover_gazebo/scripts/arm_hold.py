#!/usr/bin/env python3
# 한글: 시뮬레이션에서 팔을 base.yaml 홈 자세로 고정한다(위치 컨트롤러에 주기적으로 명령).
#       카메라 TF가 팔 끝에 달려 있어 필요.
"""Hold the simulated arm at base.yaml arm_home_pose_rad (arm_position_controller, 2 Hz)."""
import os

from ament_index_python.packages import get_package_share_directory
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
import yaml


def home_pose():
    path = os.path.join(get_package_share_directory('jetrover_base'), 'config', 'base.yaml')
    p = yaml.safe_load(open(path))['base_node']['ros__parameters']
    names, home = list(p['arm_joint_names']), list(p['arm_home_pose_rad'])
    order = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'r_joint']
    return [float(home[names.index(j)]) for j in order]


class ArmHold(Node):
    def __init__(self):
        super().__init__('arm_hold')
        self.home = home_pose()
        self.pub = self.create_publisher(
            Float64MultiArray, '/arm_position_controller/commands', 10)
        self.create_timer(0.5, self.tick)
        self.get_logger().info(f'holding arm at {self.home}')

    def tick(self):
        self.pub.publish(Float64MultiArray(data=self.home))


def main():
    rclpy.init()
    rclpy.spin(ArmHold())


if __name__ == '__main__':
    main()
