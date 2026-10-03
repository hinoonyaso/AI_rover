import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    share = get_package_share_directory('jetrover_description')
    xacro_file = os.path.join(share, 'urdf', 'jetrover.xacro')
    robot_description = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)

    # /joint_states for the arm's revolute joints now comes from jetrover_base's
    # base_node (it polls the real bus servo positions, FUNC 0x05, and converts
    # ticks -> radians -- see base_node.cpp). This launch only needs
    # robot_state_publisher; it must be run alongside base_node (base.launch.py /
    # robot.launch.py already do this) for the arm to render with a real pose
    # instead of sitting at the URDF's zero position.
    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_description}],
        ),
    ])
