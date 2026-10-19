# 한글: Nav2 전체 스택 launch. robot.launch.py(베이스+EKF+LiDAR)가 먼저 실행 중이어야 한다.
"""Full Nav2 stack: our own localization (map_server+amcl, localization.launch.py)
+ nav2_bringup's navigation_launch.py (planner/controller/bt_navigator/behavior_server/
velocity_smoother + lifecycle_manager_navigation) with jetrover's own params
(config/nav2_params.yaml). Needs `jetrover_bringup robot.launch.py` (base+EKF+LiDAR)
already running for /scan and odom -> base_footprint TF, same as localization.launch.py.

checklist 8번 / prd/slam-nav2.md 8.7.
"""
import os
import re
import tempfile

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    nav_share = get_package_share_directory('jetrover_navigation')
    bringup_share = get_package_share_directory('nav2_bringup')

    default_map = os.path.expanduser('~/jetrover_ws/maps/lap2_20261005.yaml')
    map_arg = DeclareLaunchArgument('map', default_value=default_map)
    # 한글: 진단용 로그 레벨(기본 info). 예: log_level:=debug / Diagnostic log level (default info).
    log_level_arg = DeclareLaunchArgument('log_level', default_value='info')
    # 한글: A/B 시험용으로 다른 파라미터 파일을 줄 수 있다(기본은 패키지의 nav2_params.yaml).
    # Alternate params file for A/B tests (default: this package's nav2_params.yaml).
    params_arg = DeclareLaunchArgument(
        'params_file', default_value=os.path.join(nav_share, 'config', 'nav2_params.yaml'))

    # 한글: 우리 localization(map_server + amcl)을 포함.
    # 한글: auto_localize(기본 true)는 localization.launch.py로 그대로 넘긴다.
    auto_arg = DeclareLaunchArgument('auto_localize', default_value='true')
    # 한글: Gazebo에서는 use_sim_time:=true(navigation_launch가 모든 Nav2 노드 파라미터를 덮어씀).
    sim_arg = DeclareLaunchArgument('use_sim_time', default_value='false')
    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav_share, 'launch', 'localization.launch.py')),
        launch_arguments={'map': LaunchConfiguration('map'),
                          'auto_localize': LaunchConfiguration('auto_localize'),
                          'use_sim_time': LaunchConfiguration('use_sim_time')}.items(),
    )

    # 한글: nav2_bringup의 navigation_launch.py(플래너/컨트롤러/BT/행동 서버/속도 스무더)를 jetrover 파라미터로 포함.
    # use_sim_time:=true일 때는 파라미터 파일의 `use_sim_time: false`를 true로 바꾼 임시 파일을 쓴다.
    # 노드마다 false가 명시돼 있어서 launch 인자(use_sim_time)가 덮어쓰지 못했다: 컨트롤러·플래너·BT·코스트맵이 벽시계를 쓰고
    # AMCL만 시뮬레이션 시계를 써서 "Transform data too old" → 목표가 0.8초 만에 aborted(2026-10-18, Gazebo).
    # 실기(기본 false)는 파일을 그대로 쓴다.
    # With use_sim_time:=true use a temporary copy of the params file with `use_sim_time: true`. Every node section
    # states `false` explicitly, which beat the launch argument: controller/planner/BT/costmaps ran on wall time and
    # only AMCL on sim time -> "Transform data too old", goals aborted after 0.8 s. The robot (default false) is untouched.
    def include_navigation(context):
        params = LaunchConfiguration('params_file').perform(context)
        sim = LaunchConfiguration('use_sim_time').perform(context).lower() == 'true'
        if sim:
            text = re.sub(r'(use_sim_time:\s*)(?:false|False)', r'\1true', open(params).read())
            # 시뮬레이션 전용: 깊이 레이어 최소 장애물 높이 −0.1 → 0.09 m. 스캔한 방 메쉬는 바닥 요철 5~6 cm와 벽 밑이 말려 올라간
            # 경사면(최대 26 cm)이 있어 빈 방에서도 깊이 오탐이 생기고, 마킹은 시야의 광선이 지나가야만 지워져 코스트맵 통로를
            # 영구히 막았다(tools/sim/depth_fp_survey.py, 2026-10-19). 9 cm 이하는 무시하고 상자(11 cm) 윗면은 그대로 잡힌다.
            # Sim only: depth layer min_obstacle_height -0.1 -> 0.09. The scanned mesh has floor bumps and wall-foot ramps; their
            # stale marks blocked corridors for good. The box top (0.11 m) is still seen. The real robot is untouched.
            text = re.sub(r'(min_obstacle_height:\s*)-0\.1\b', r'\g<1>0.09', text)
            with tempfile.NamedTemporaryFile('w', suffix='_sim.yaml', delete=False) as f:
                f.write(text)
                params = f.name
        return [IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(bringup_share, 'launch', 'navigation_launch.py')),
            launch_arguments={
                'params_file': params,
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'autostart': 'true',
                'log_level': LaunchConfiguration('log_level'),
            }.items())]

    return LaunchDescription(
        [map_arg, log_level_arg, params_arg, auto_arg, sim_arg, localization, OpaqueFunction(function=include_navigation)])
