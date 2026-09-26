import os

from ament_index_python.packages import get_package_share_directory, PackageNotFoundError
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    share = get_package_share_directory('jetrover_base')
    base_config = os.path.join(share, 'config', 'base.yaml')
    ekf_config = os.path.join(share, 'config', 'ekf.yaml')
    description_launch = os.path.join(
        get_package_share_directory('jetrover_description'), 'launch', 'description.launch.py')

    try:
        get_package_share_directory('robot_localization')
        have_ekf = True
    except PackageNotFoundError:
        have_ekf = False

    actions = [
        DeclareLaunchArgument(
            'ekf', default_value='true',
            description='Run robot_localization (publishes /odom and odom->base_footprint)'),
        DeclareLaunchArgument(
            'cmd_vel_timeout', default_value='0.5',
            description='Seconds without /cmd_vel before the wheels are stopped '
                        '(use 1.0 for keyboard teleop, see troubleshooting/003)'),
        DeclareLaunchArgument(
            'max_linear', default_value='0.2',
            description='Speed limit in m/s applied to /cmd_vel linear x and y'),
        DeclareLaunchArgument(
            'max_angular', default_value='1.0',
            description='Speed limit in rad/s applied to /cmd_vel angular z'),
        Node(
            package='jetrover_base',
            executable='base_node',
            name='base_node',
            output='screen',
            parameters=[base_config, {
                'cmd_vel_timeout': ParameterValue(
                    LaunchConfiguration('cmd_vel_timeout'), value_type=float),
                'max_linear': ParameterValue(
                    LaunchConfiguration('max_linear'), value_type=float),
                'max_angular': ParameterValue(
                    LaunchConfiguration('max_angular'), value_type=float)}],
        ),
        # URDF -> static TFs (base_footprint -> base_link -> imu_link, lidar_link, ...).
        # base_node already rotates the IMU axes into base_link's, so imu_link has no rotation.
        IncludeLaunchDescription(PythonLaunchDescriptionSource(description_launch)),
    ]

    if have_ekf:
        actions.append(Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[ekf_config],
            remappings=[('odometry/filtered', 'odom')],
            condition=IfCondition(LaunchConfiguration('ekf')),
        ))
    else:
        actions.append(LogInfo(
            msg='robot_localization is not installed: /odom and odom->base_footprint are NOT '
                'published. Install it with: sudo apt install ros-jazzy-robot-localization'))

    return LaunchDescription(actions)
