# 한글: JetRover Gazebo 시뮬레이션 실행(host). Gazebo + 로봇 소환 + 컨트롤러 + 브리지 + EKF + 보조 노드.
#       Nav2는 따로: ros2 launch jetrover_navigation nav2.launch.py use_sim_time:=true
"""
JetRover in Gazebo Harmonic (prd/gazebo-sim.md). Run on the host PC.

  ros2 launch jetrover_gazebo sim.launch.py [world:=lap2_room_box.sdf] [x:=1.02 y:=0.37 yaw:=1.45]
                                            [gui:=true] [depth_obstacles:=false]
Then Nav2 with simulated time:
  ros2 launch jetrover_navigation nav2.launch.py use_sim_time:=true \
      params_file:=$HOME/<ws>/tools/nav/ab_params/nav2_params_mppi.yaml
Spawn pose is in the map frame (world = map coordinates); default = start point A of the
2026-10-09 trials.
depth_obstacles needs a simulated depth background reference first (see README).
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction,
                            RegisterEventHandler)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
import yaml


def home_pose_joints1_5():
    path = os.path.join(get_package_share_directory('jetrover_base'), 'config', 'base.yaml')
    p = yaml.safe_load(open(path))['base_node']['ros__parameters']
    names, home = list(p['arm_joint_names']), list(p['arm_home_pose_rad'])
    return [float(home[names.index(f'joint{i}')]) for i in range(1, 6)]


def setup(context):
    share = get_package_share_directory('jetrover_gazebo')
    world = LaunchConfiguration('world').perform(context)
    if not os.path.isabs(world):
        world = os.path.join(share, 'worlds', world)
    gui = LaunchConfiguration('gui').perform(context) == 'true'
    controllers = os.path.join(share, 'config', 'sim_controllers.yaml')
    xacro_file = os.path.join(share, 'urdf', 'jetrover_sim.urdf.xacro')
    robot_description = ParameterValue(
        Command(['xacro ', xacro_file, ' sim_mode:=true controllers_file:=', controllers]),
        value_type=str)
    sim_time = {'use_sim_time': True}

    gz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': f'-r -v 2 {"" if gui else "-s "}{world}'}.items())
    rsp = Node(package='robot_state_publisher', executable='robot_state_publisher',
               output='screen',
               parameters=[{'robot_description': robot_description}, sim_time])
    spawn = Node(package='ros_gz_sim', executable='create', output='screen',
                 arguments=['-topic', 'robot_description', '-name', 'jetrover',
                            '-x', LaunchConfiguration('x'), '-y', LaunchConfiguration('y'),
                            '-z', '0.01', '-Y', LaunchConfiguration('yaw')])
    bridge = Node(package='ros_gz_bridge', executable='parameter_bridge', output='screen',
                  parameters=[{'config_file': os.path.join(share, 'config', 'sim_bridge.yaml')},
                              sim_time])

    def spawner(name):
        return Node(package='controller_manager', executable='spawner', arguments=[name],
                    output='screen')
    jsb, mecanum, arm = (spawner('joint_state_broadcaster'), spawner('mecanum_drive_controller'),
                         spawner('arm_position_controller'))

    # camera optical frame (the real driver publishes this chain; Gazebo labels images with it)
    # 한글: 실기는 카메라 드라이버가 내는 optical 프레임 TF. 시뮬에서는 정적 TF로.
    optical_tf = Node(package='tf2_ros', executable='static_transform_publisher', output='screen',
                      arguments=['--frame-id', 'depth_cam_link',
                                 '--child-frame-id', 'depth_cam_color_optical_frame',
                                 '--roll', '-1.5707963', '--pitch', '0', '--yaw', '-1.5707963'],
                      parameters=[sim_time])
    ekf = Node(package='robot_localization', executable='ekf_node', name='ekf_filter_node',
               output='screen',
               parameters=[os.path.join(share, 'config', 'sim_ekf.yaml'), sim_time],
               remappings=[('odometry/filtered', 'odom')])
    relay = Node(package='jetrover_gazebo', executable='cmd_vel_to_stamped.py', output='screen',
                 parameters=[sim_time])
    depth_conv = Node(package='jetrover_gazebo', executable='depth_float_to_mm.py',
                      output='screen', parameters=[sim_time])
    arm_hold = Node(package='jetrover_gazebo', executable='arm_hold.py', output='screen',
                    parameters=[sim_time])
    sparse = Node(package='jetrover_perception', executable='sparse_point_cloud.py',
                  name='sparse_point_cloud', namespace='depth_cam', output='screen',
                  condition=IfCondition(LaunchConfiguration('depth_obstacles')),
                  parameters=[{'home_pose_rad': home_pose_joints1_5(),
                               'background_depth_path': os.path.join(
                                   share, 'config', 'depth_background_ref_sim.npy')}, sim_time])

    return [
        gz, rsp, spawn, bridge, optical_tf, ekf, relay, depth_conv, sparse,
        RegisterEventHandler(OnProcessExit(target_action=spawn, on_exit=[jsb])),
        RegisterEventHandler(OnProcessExit(target_action=jsb, on_exit=[mecanum, arm, arm_hold])),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='lap2_room_box.sdf',
                              description='file in jetrover_gazebo/worlds or an absolute path'),
        DeclareLaunchArgument('x', default_value='1.02'),
        DeclareLaunchArgument('y', default_value='0.37'),
        DeclareLaunchArgument('yaw', default_value='1.45', description='rad, map frame'),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('depth_obstacles', default_value='false',
                              description='run sparse_point_cloud '
                                          '(needs config/depth_background_ref_sim.npy)'),
        OpaqueFunction(function=setup),
    ])
