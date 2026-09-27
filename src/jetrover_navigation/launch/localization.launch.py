"""map_server + AMCL + lifecycle_manager, for localizing against a saved map
instead of running SLAM live. Needs `jetrover_bringup robot.launch.py`
(base + EKF + LiDAR) already running for /scan and odom -> base_footprint TF.

Default map is the one saved in maps/lap1_20260922.yaml (single lap, small
room, 2026-09-22). Override with `map:=/path/to/other.yaml` for a new one.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    default_map = os.path.expanduser('~/jetrover_ws/maps/lap1_20260922.yaml')
    amcl_params = os.path.join(
        get_package_share_directory('jetrover_navigation'), 'config', 'amcl.yaml')

    map_arg = DeclareLaunchArgument('map', default_value=default_map,
                                     description='Path to a map .yaml saved by nav2_map_server')
    map_yaml = LaunchConfiguration('map')

    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{'yaml_filename': map_yaml, 'use_sim_time': False}],
    )

    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[amcl_params],
    )

    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[{
            'use_sim_time': False,
            'autostart': True,
            'node_names': ['map_server', 'amcl'],
        }],
    )

    return LaunchDescription([map_arg, map_server, amcl, lifecycle_manager])
