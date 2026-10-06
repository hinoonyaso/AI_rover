# 한글: MoveIt 실행 브리지(FollowJointTrajectory -> base_node arm/command_timed).
# base_node는 arm_command_enabled:=true 로 떠 있어야 하고, move_group은 mode:=real 이어야 한다.
# Execution bridge. Needs base_node with arm_command_enabled:=true and move_group in mode:=real.
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('dry_run', default_value='true',
                              description='true: 검사/로그만, 명령 발행 안 함 (기본, 안전)'),
        Node(package='jetrover_manipulation', executable='trajectory_bridge.py', output='screen',
             parameters=[{'dry_run': LaunchConfiguration('dry_run')}]),
    ])
