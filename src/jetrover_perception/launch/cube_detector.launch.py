"""Run cube detection with an explicit depth source.

한글: 깊이 출처를 명시해 큐브 인식을 실행한다.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import json
from pathlib import Path


def setup(context):
    """Choose one depth input without automatic fallback.

    한글: 자동 대체 없이 하나의 깊이 입력을 선택한다.
    """
    source=LaunchConfiguration('depth_source').perform(context)
    if source == 'configured':
        path=Path.home()/'.local/share/jetinspect-ops/calibration/depth-source.json'
        if path.exists():
            if path.is_symlink() or path.stat().st_size>65536:raise ValueError('invalid depth source configuration')
            source=json.loads(path.read_text()).get('source')
        else:source='default'
    if source not in ('default','corrected'):raise ValueError('depth_source must be default or corrected')
    remappings=[] if source=='default' else [('depth_cam/depth/image_raw','/depth_cam/depth_corrected/image_raw')]
    return [Node(package='jetrover_perception',executable='cube_detector.py',name='cube_detector',output='screen',remappings=remappings)]


def generate_launch_description():
    """Declare detector source selection. / 감지기 입력 선택을 선언한다."""
    return LaunchDescription([DeclareLaunchArgument('depth_source',default_value='configured'),OpaqueFunction(function=setup)])
