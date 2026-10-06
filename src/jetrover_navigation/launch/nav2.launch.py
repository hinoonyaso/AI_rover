# 한글: Nav2 전체 스택 launch. robot.launch.py(베이스+EKF+LiDAR)가 먼저 실행 중이어야 한다.
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

    default_map = os.path.expanduser('~/jetrover_ws/maps/lap2_20261005.yaml')
    map_arg = DeclareLaunchArgument('map', default_value=default_map)
    # 한글: 진단용 로그 레벨(기본 info). 예: log_level:=debug / Diagnostic log level (default info).
    log_level_arg = DeclareLaunchArgument('log_level', default_value='info')

    # 한글: 우리 localization(map_server + amcl)을 포함.
    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav_share, 'launch', 'localization.launch.py')),
        launch_arguments={'map': LaunchConfiguration('map')}.items(),
    )

    # 한글: nav2_bringup의 navigation_launch.py(플래너/컨트롤러/BT/행동 서버/속도 스무더)를 jetrover 파라미터로 포함.
    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_share, 'launch', 'navigation_launch.py')),
        launch_arguments={
            'params_file': os.path.join(nav_share, 'config', 'nav2_params.yaml'),
            'use_sim_time': 'false',
            'autostart': 'true',
            'log_level': LaunchConfiguration('log_level'),
        }.items(),
    )

    return LaunchDescription([map_arg, log_level_arg, localization, navigation])
