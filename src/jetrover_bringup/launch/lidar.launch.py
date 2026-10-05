# 한글: RPLIDAR 실행 launch.
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    # 한글: LiDAR(RPLIDAR A1M8) 파라미터 파일. 포트는 by-path로 지정돼 있다(ttyUSB 번호는 재부팅마다 바뀜).
    config = os.path.join(get_package_share_directory('jetrover_bringup'), 'config', 'lidar.yaml')

    return LaunchDescription([
        Node(
            package='rplidar_ros',
            executable='rplidar_composition',
            name='rplidar_composition',
            output='screen',
            parameters=[config],
        ),
    ])
