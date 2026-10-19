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
from launch.actions import (AppendEnvironmentVariable, DeclareLaunchArgument,
                            IncludeLaunchDescription, OpaqueFunction, RegisterEventHandler)
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
    # 그리퍼 effort 2 N·m: 설명 기본값 1000이면 손가락이 사실상 무한한 힘으로 조여
    # 큐브가 튕겨 나갔다(2026-10-18). 실기 서보 토크와 같은 크기로 추정(측정 안 함).
    # Gripper effort 2 N·m: the description's 1000 squeezed with practically unlimited force
    # and shot the cube out of the gripper. Assumed similar to the real servo torque (unmeasured).
    robot_description = ParameterValue(
        Command(['xacro ', xacro_file, ' sim_mode:=true gripper_effort:=2 controllers_file:=',
                 controllers]),
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
    # 팔 컨트롤러: forward(기본, 기존 시험 도구·arm_hold) 또는 moveit(실기 브리지와 같은 이름의 궤적 컨트롤러)
    # Arm controllers: forward (default: existing tools + arm_hold) or moveit
    # (trajectory controllers named like the real bridge's action servers)
    moveit_mode = LaunchConfiguration('arm_mode').perform(context) == 'moveit'
    jsb, mecanum = spawner('joint_state_broadcaster'), spawner('mecanum_drive_controller')
    arm_spawners = ([spawner('arm_controller'), spawner('gripper_controller')] if moveit_mode
                    else [spawner('arm_position_controller')])

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
                               # 스캔한 방 바닥은 요철이 5~6 cm라 기준 depth(평평)와 60 mm 넘게 어긋난 오탐이 빈 방 24곳 중 20곳에서
                               # 평균 265점 나왔다. 100 mm로 101점, 140 mm로 42점(tools/sim/depth_fp_survey.py, 2026-10-19).
                               # 상자(높이 11 cm) 검출은 check_depth_obstacles.py로 확인. SIM_DEPTH_MARGIN_MM로 바꿀 수 있다. 실기는 60.
                               # The scanned room floor has 5-6 cm bumps: 60 mm gave 265 false points/msg in the empty room (20 of 24 poses),
                               # 100 mm gives 101, 140 mm 42. Real robot (flat floor) stays at 60 mm.
                               'background_margin_mm': int(os.environ.get('SIM_DEPTH_MARGIN_MM', '100')),
                               # 카메라에 보이는 면 뒤로 장애물을 연장하는 깊이: 실기 0.15 m는 상자 두께(0.22 m)보다 7 cm 짧아
                               # 코스트맵의 상자가 먼 쪽 7 cm 낮게 잡혀 로봇이 먼 모서리를 계획보다 7 cm 가깝게 지났다
                               # (S4 최소 중심-상자 거리 16.4 cm < 코스트맵 내접 반경 22 cm, 2026-10-19). 시뮬레이션은 0.25 m.
                               # Extrusion behind the seen face: the real 0.15 m is 7 cm shorter than the box (0.22 m), so the far
                               # 7 cm was missing in the costmap and the robot cut the far corner. Sim 0.25 m; real robot unchanged.
                               'extrude_depth_m': float(os.environ.get('SIM_DEPTH_EXTRUDE_M', '0.25')),
                               'background_depth_path': os.path.join(
                                   share, 'config', 'depth_background_ref_sim.npy')}, sim_time])

    # scanned-room models (models/room_lap2, Phase 3) / 스캔 방 모델 경로
    models = AppendEnvironmentVariable('GZ_SIM_RESOURCE_PATH', os.path.join(share, 'models'))
    # 로봇 메쉬(model://jetrover_description/meshes/...)를 찾도록 그 패키지 share의 상위 폴더.
    # 없으면 로봇 몸체가 안 그려지고 몸체 충돌 메쉬도 빠진다(2026-10-14 host 로그 70개).
    # Parent of jetrover_description's share dir so model://jetrover_description/... resolves
    # (the robot body was invisible and had no body collision).
    robot_meshes = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.dirname(get_package_share_directory('jetrover_description')))
    return [
        models, robot_meshes, gz, rsp, spawn, bridge, optical_tf, ekf, relay, depth_conv, sparse,
        RegisterEventHandler(OnProcessExit(target_action=spawn, on_exit=[jsb])),
        RegisterEventHandler(OnProcessExit(
            target_action=jsb,
            on_exit=[mecanum] + arm_spawners + ([] if moveit_mode else [arm_hold]))),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='lap2_room_box.sdf',
                              description='file in jetrover_gazebo/worlds or an absolute path'),
        DeclareLaunchArgument('x', default_value='1.02'),
        DeclareLaunchArgument('y', default_value='0.37'),
        DeclareLaunchArgument('yaw', default_value='1.45', description='rad, map frame'),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('arm_mode', default_value='forward',
                              description='forward (arm_position_controller + arm_hold) | moveit '
                                          '(arm_controller + gripper_controller for move_group)'),
        DeclareLaunchArgument('depth_obstacles', default_value='false',
                              description='run sparse_point_cloud '
                                          '(needs config/depth_background_ref_sim.npy)'),
        OpaqueFunction(function=setup),
    ])
