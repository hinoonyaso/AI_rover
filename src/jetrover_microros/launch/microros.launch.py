# 한글: micro-ROS 펌웨어(COMM_MODE=MICROROS) 전체 실행 launch.
"""micro-ROS firmware (COMM_MODE=MICROROS) bring-up: agent + bridge + URDF TFs + EKF.

Use INSTEAD of base.launch.py (both would open the same serial port). The firmware must be the
MICROROS build; the stock/RRC build speaks a different protocol on this port.
"""
import os

from ament_index_python.packages import get_package_share_directory, PackageNotFoundError
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory('jetrover_microros')
    base_share = get_package_share_directory('jetrover_base')
    description_launch = os.path.join(
        get_package_share_directory('jetrover_description'), 'launch', 'description.launch.py')

    def have(pkg):
        try:
            get_package_share_directory(pkg)
            return True
        except PackageNotFoundError:
            return False

# 한글: agent + 브리지 + URDF TF + EKF. 같은 시리얼 포트를 쓰는 base.launch.py와 동시에 실행하면 안 된다.
    actions = [
        DeclareLaunchArgument(
            'dev', default_value='/dev/serial/by-id/usb-1a86_USB_Single_Serial_596F003889-if00',
            description='Serial device of the STM32 host link (USB serial port 2)'),
        DeclareLaunchArgument('baud', default_value='1000000'),
        DeclareLaunchArgument('ekf', default_value='true'),
        Node(
            package='jetrover_microros', executable='rrc_bridge', name='rrc_bridge', output='screen',
            parameters=[os.path.join(share, 'config', 'bridge.yaml')]),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(description_launch)),
    ]

# 한글: agent가 소스 빌드 안 되어 있으면 안내만 출력하고 계속 진행한다(브리지/URDF는 확인 가능).
    if have('micro_ros_agent'):
        actions.append(Node(
            package='micro_ros_agent', executable='micro_ros_agent', name='micro_ros_agent',
            output='screen',
            arguments=['serial', '--dev', LaunchConfiguration('dev'), '-b', LaunchConfiguration('baud')]))
    else:
        actions.append(LogInfo(
            msg='micro_ros_agent is not installed: build it with '
                'firmware/rrc_m4/micro_ros/build_agent.sh (see micro_ros/README.md)'))

    if have('robot_localization'):
        actions.append(Node(
            package='robot_localization', executable='ekf_node', name='ekf_filter_node', output='screen',
            parameters=[os.path.join(base_share, 'config', 'ekf.yaml')],
            remappings=[('odometry/filtered', 'odom')],
            condition=IfCondition(LaunchConfiguration('ekf'))))

    return LaunchDescription(actions)
