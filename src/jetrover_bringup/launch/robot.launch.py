# 한글: 로봇 전체 기본 실행(베이스 + LiDAR).
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # 한글: 다른 패키지의 launch 파일을 인자와 함께 포함하는 헬퍼.
    def include(package, name, **args):
        path = os.path.join(get_package_share_directory(package), 'launch', name)
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(path), launch_arguments=args.items())

    # 한글: 베이스(+URDF+EKF) 다음에 LiDAR를 함께 띄운다. 키보드 텔레옵은 cmd_vel_timeout을 1.0으로 올린다.
    # base_node + URDF/TF + EKF, then the LiDAR.
    return LaunchDescription([
        DeclareLaunchArgument(
            'cmd_vel_timeout', default_value='0.5',
            description='Seconds without /cmd_vel before the wheels stop '
                        '(1.0 for keyboard teleop)'),
        DeclareLaunchArgument(
            'max_linear', default_value='0.2', description='Speed limit in m/s (x and y)'),
        DeclareLaunchArgument(
            'max_angular', default_value='1.0', description='Speed limit in rad/s'),
        include('jetrover_base', 'base.launch.py',
                cmd_vel_timeout=LaunchConfiguration('cmd_vel_timeout'),
                max_linear=LaunchConfiguration('max_linear'),
                max_angular=LaunchConfiguration('max_angular')),
        include('jetrover_bringup', 'lidar.launch.py'),
    ])
