# 한글: RViz 실행 launch.
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    # 한글: RViz 설정(jetrover.rviz). Jetson이 아니라 원격 호스트에서 띄우는 것이 일반적이다.
    config = os.path.join(get_package_share_directory('jetrover_bringup'), 'rviz', 'jetrover.rviz')

    return LaunchDescription([
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', config],
            output='screen',
        ),
    ])
