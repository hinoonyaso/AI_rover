# 한글: host(노트북/PC)용 RViz. move_group은 Jetson에서 돌고, 여기서는 MotionPlanning 패널만 띄운다.
# 같은 ROS_DOMAIN_ID/네트워크여야 하고, 이 패키지와 jetrover_description이 host에도 빌드/설치돼 있어야 한다.
# RViz for the host machine: move_group runs on the Jetson; this only starts the MotionPlanning panel.
import os

import xacro
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def _y(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def generate_launch_description():
    share = get_package_share_directory('jetrover_manipulation')
    cfg = os.path.join(share, 'config')
    desc = get_package_share_directory('jetrover_description')
    robot_description = {'robot_description': xacro.process_file(
        os.path.join(desc, 'urdf', 'jetrover.xacro')).toxml()}
    with open(os.path.join(cfg, 'jetrover.srdf'), 'r', encoding='utf-8') as f:
        srdf = {'robot_description_semantic': f.read()}
    return LaunchDescription([Node(
        package='rviz2', executable='rviz2', name='rviz2_moveit', output='screen',
        arguments=['-d', os.path.join(cfg, 'moveit.rviz')],
        parameters=[robot_description, srdf,
                    {'robot_description_kinematics': _y(os.path.join(cfg, 'kinematics.yaml'))},
                    {'robot_description_planning': _y(os.path.join(cfg, 'joint_limits.yaml'))}])])
