# 한글: STM32 베이스 드라이버 + URDF TF + EKF 실행 launch.
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

    # 한글: robot_localization이 설치돼 있는지 확인한다. 없으면 EKF를 건너뛰고 안내만 출력한다(그 경우 /odom과 TF가 안 나온다).
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
        # 한글: 팔 구동/시작 시 홈 자세 이동(기본 꺼짐). 사람이 팔 옆에서 지켜볼 때만 true. / Arm motion, OFF by default.
        DeclareLaunchArgument(
            'arm_command_enabled', default_value='false',
            description='Allow arm motion (arm/command, home move); only while watched'),
        DeclareLaunchArgument(
            'arm_move_home_on_start', default_value='false',
            description='Step the arm to base.yaml arm_home_pose_rad at startup '
                        '(needs arm_command_enabled)'),
        Node(
            # 한글: STM32 시리얼 드라이버 노드. base.yaml을 읽고, cmd_vel_timeout/속도 제한은 launch 인자로 덮어쓴다.
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
                    LaunchConfiguration('max_angular'), value_type=float),
                'arm_command_enabled': ParameterValue(
                    LaunchConfiguration('arm_command_enabled'), value_type=bool),
                'arm_move_home_on_start': ParameterValue(
                    LaunchConfiguration('arm_move_home_on_start'), value_type=bool)}],
        ),
        # 한글: URDF에서 정적 TF를 만든다. base_node가 IMU 축을 이미 base_link 축으로 돌려 발행하므로 imu_link에는 회전이 없다.
        # URDF -> static TFs (base_footprint -> base_link -> imu_link, lidar_link, ...).
        # base_node already rotates the IMU axes into base_link's, so imu_link has no rotation.
        IncludeLaunchDescription(PythonLaunchDescriptionSource(description_launch)),
    ]

    if have_ekf:
        # 한글: EKF: wheel_twist(vx, vy)와 IMU 자이로 yaw rate를 융합해 /odom과 odom→base_footprint TF를 낸다.
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
