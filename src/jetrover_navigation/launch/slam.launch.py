# 한글: SLAM(slam_toolbox) 실행 launch.
import os

from ament_index_python.packages import get_package_share_directory, PackageNotFoundError
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    params = os.path.join(
        get_package_share_directory('jetrover_navigation'), 'config',
        'slam_toolbox_online_async.yaml')

    # 한글: slam_toolbox가 없으면 설치 방법만 안내한다.
    try:
        slam_share = get_package_share_directory('slam_toolbox')
    except PackageNotFoundError:
        return LaunchDescription([LogInfo(
            msg='slam_toolbox is not installed. Install it with: '
                'sudo apt install ros-jazzy-slam-toolbox')])

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(slam_share, 'launch', 'online_async_launch.py')),
            # 한글: 온라인 비동기 SLAM 설정 파일을 넘긴다(sim time 끔).
            launch_arguments={
                'slam_params_file': params,
                'use_sim_time': 'false',
            }.items()),
    ])
