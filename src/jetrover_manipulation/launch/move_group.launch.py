# 한글: MoveIt2 move_group launch. 기본은 plan_only(계획/시각화만, 로봇 팔을 움직이지 않는다).
# MoveIt2 move_group launch. Default `mode:=plan_only` plans and visualises only (never moves the arm).
#   plan_only : joint_state_publisher가 홈 자세 가짜 /joint_states를 내고 실행은 꺼짐. 로봇 없이도 가능.
#   real      : base_node(/joint_states, 실제 서보 위치)가 이미 떠 있어야 한다. 실행 브리지는 다음 단계(미구현).
import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _load_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def _setup(context, *args, **kwargs):
    mode = LaunchConfiguration('mode').perform(context)
    use_rviz = LaunchConfiguration('rviz').perform(context) == 'true'
    if mode not in ('plan_only', 'real'):
        raise RuntimeError(f"mode must be 'plan_only' or 'real', got {mode!r}")

    share = get_package_share_directory('jetrover_manipulation')
    desc_share = get_package_share_directory('jetrover_description')
    cfg = os.path.join(share, 'config')

    # 한글: xacro를 실행해 URDF 문자열을 만든다(robot_state_publisher와 같은 파일).
    import xacro
    robot_description = {
        'robot_description': xacro.process_file(
            os.path.join(desc_share, 'urdf', 'jetrover.xacro')).toxml()}
    with open(os.path.join(cfg, 'jetrover.srdf'), 'r', encoding='utf-8') as f:
        robot_description_semantic = {'robot_description_semantic': f.read()}
    kinematics = {'robot_description_kinematics': _load_yaml(os.path.join(cfg, 'kinematics.yaml'))}
    joint_limits = {'robot_description_planning': _load_yaml(os.path.join(cfg, 'joint_limits.yaml'))}
    ompl = {
        'planning_pipelines': ['ompl'],
        'default_planning_pipeline': 'ompl',
        'ompl': _load_yaml(os.path.join(cfg, 'ompl_planning.yaml')),
    }
    controllers = _load_yaml(os.path.join(cfg, 'moveit_controllers.yaml'))
    execution = {
        # 한글: plan_only에서는 실행 자체를 막아 팔이 절대 움직이지 않게 한다.
        'allow_trajectory_execution': mode == 'real',
        'moveit_manage_controllers': False,
        'trajectory_execution.allowed_execution_duration_scaling': 1.5,
        'trajectory_execution.allowed_goal_duration_margin': 1.0,
        'trajectory_execution.allowed_start_tolerance': 0.05,
    }
    scene_monitor = {
        'publish_planning_scene': True,
        'publish_geometry_updates': True,
        'publish_state_updates': True,
        'publish_transforms_updates': True,
    }
    common = [robot_description, robot_description_semantic, kinematics]

    nodes = [Node(
        package='moveit_ros_move_group', executable='move_group', output='screen',
        parameters=common + [joint_limits, ompl, controllers, execution, scene_monitor,
                             {'use_sim_time': False}],
    )]

    # 한글: base_node가 이미 /joint_states를 내고 있으면 가짜를 켜면 두 발행자가 섞여 상태가 흔들린다(2026-10-06 겪음).
    # 로봇/base_node 없이 시험할 때만 fake_joint_states:=true. / Two publishers on /joint_states mix; use only without base_node.
    if mode == 'plan_only' and LaunchConfiguration('fake_joint_states').perform(context) == 'true':
        nodes += [
            Node(package='robot_state_publisher', executable='robot_state_publisher',
                 parameters=[robot_description]),
            Node(package='joint_state_publisher', executable='joint_state_publisher',
                 parameters=[robot_description, {
                     'zeros': {'joint1': 0.0042, 'joint2': -0.6618, 'joint3': 1.6629,
                               'joint4': 1.6043, 'joint5': 0.0168, 'r_joint': -0.0209}}]),
        ]

    if use_rviz:
        rviz_cfg = os.path.join(cfg, 'moveit.rviz')
        args = ['-d', rviz_cfg] if os.path.exists(rviz_cfg) else []
        nodes.append(Node(package='rviz2', executable='rviz2', name='rviz2_moveit',
                          output='screen', arguments=args,
                          parameters=common + [joint_limits, ompl]))
    return nodes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('mode', default_value='plan_only',
                              description="plan_only | real (see file header)"),
        DeclareLaunchArgument('fake_joint_states', default_value='false',
                              description='plan_only without a robot: publish fake home /joint_states + TF'),
        DeclareLaunchArgument('rviz', default_value='false',
                              description='Start RViz here (usually run on the host instead)'),
        OpaqueFunction(function=_setup),
    ])
