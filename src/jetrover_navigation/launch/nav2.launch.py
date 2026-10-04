"""Full Nav2 stack: our own localization (map_server+amcl, localization.launch.py)
+ nav2_bringup's navigation_launch.py (planner/controller/bt_navigator/behavior_server/
velocity_smoother + lifecycle_manager_navigation) with jetrover's own params
(config/nav2_params.yaml). Needs `jetrover_bringup robot.launch.py` (base+EKF+LiDAR)
already running for /scan and odom -> base_footprint TF, same as localization.launch.py.

checklist 8번 / prd/slam-nav2.md 8.7.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    nav_share = get_package_share_directory('jetrover_navigation')
    bringup_share = get_package_share_directory('nav2_bringup')

    default_map = os.path.expanduser('~/jetrover_ws/maps/lap1_20260922.yaml')
    map_arg = DeclareLaunchArgument('map', default_value=default_map)

    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav_share, 'launch', 'localization.launch.py')),
        launch_arguments={'map': LaunchConfiguration('map')}.items(),
    )

    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_share, 'launch', 'navigation_launch.py')),
        launch_arguments={
            'params_file': os.path.join(nav_share, 'config', 'nav2_params.yaml'),
            'use_sim_time': 'false',
            'autostart': 'true',
        }.items(),
    )

    return LaunchDescription([map_arg, localization, navigation])
