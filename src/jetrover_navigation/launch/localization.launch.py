# 한글: 저장된 지도로 위치를 추정하는 launch(SLAM 대신). robot.launch.py가 먼저 떠 있어야 한다.
"""map_server + AMCL + lifecycle_manager, for localizing against a saved map
instead of running SLAM live. Needs `jetrover_bringup robot.launch.py`
(base + EKF + LiDAR) already running for /scan and odom -> base_footprint TF.

Default map is maps/lap2_20261005.yaml (re-mapped 2026-10-05 after the original
lap1_20260922 map kept blocking Nav2 near an actual chair the planner's
footprint+inflation couldn't clear in that tight spot -- see checklist 8).
Override with `map:=/path/to/other.yaml` for a new one.

auto_localize (default true, 2026-10-07): runs scan_match_init.py once at startup, which
matches the current /scan against the map and sends /initialpose if the match is confident
(more accurate than clicking 2D Pose Estimate over a remote RViz). The robot must stand still.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    # 한글: 기본 지도 경로(재매핑한 lap2 지도). 새 지도는 map:=경로 로 덮어쓴다.
    default_map = os.path.expanduser('~/jetrover_ws/maps/lap2_20261005.yaml')
    amcl_params = os.path.join(
        get_package_share_directory('jetrover_navigation'), 'config', 'amcl.yaml')

    map_arg = DeclareLaunchArgument('map', default_value=default_map,
                                     description='Path to a map .yaml saved by nav2_map_server')
    map_yaml = LaunchConfiguration('map')
    # 한글: Gazebo(jetrover_gazebo)에서는 use_sim_time:=true. 실기는 기본 false. / true only for Gazebo.
    sim_arg = DeclareLaunchArgument('use_sim_time', default_value='false')
    sim_time = {'use_sim_time': ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool)}

    # 한글: 지도 서버: 저장된 지도를 /map으로 발행.
    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{'yaml_filename': map_yaml}, sim_time],
    )

    # 한글: AMCL: 지도와 /scan으로 map→odom TF를 추정.
    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[amcl_params, sim_time],
    )

    # 한글: map_server/amcl 라이프사이클 노드를 자동으로 활성화한다.
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[sim_time, {
            'autostart': True,
            'node_names': ['map_server', 'amcl'],
        }],
    )

    # 한글: 시작 시 스캔-지도 매칭으로 초기 위치 자동 설정(확신 낮으면 안 보냄). auto_localize:=false로 끔.
    auto_arg = DeclareLaunchArgument(
        'auto_localize', default_value='true',
        description='Match /scan to the map once at startup and send /initialpose if confident')
    scan_match = TimerAction(
        period=3.0,  # let map_server/amcl come up first; the script also waits for them
        actions=[Node(
            package='jetrover_navigation',
            executable='scan_match_init.py',
            name='scan_match_init',
            output='screen',
            condition=IfCondition(LaunchConfiguration('auto_localize')),
            parameters=[sim_time],
        )],
    )

    return LaunchDescription(
        [map_arg, auto_arg, sim_arg, map_server, amcl, lifecycle_manager, scan_match])
