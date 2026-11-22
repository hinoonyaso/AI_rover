# Orbbec DaBai DCW (RGB-D) bringup, same driver/parameters Hiwonder uses
# (src/peripherals/launch/include/dabai_dcw.launch.py in their JetRover repo), but WITHOUT
# their color->rgb topic remap: their own rtabmap_slam.launch.py subscribes to the un-remapped
# ".../color/image_raw" and ".../color/camera_info", so we keep the driver's natural names.
import os
import importlib.util
import hashlib

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode
import yaml


# 한글: base.yaml의 팔 홈 자세(관절1~5)를 읽어 depth self-filter의 홈 자세 확인에 넘긴다(값을 두 곳에 복사하지 않음).
def _arm_home_pose():
    """Return joint1..5 of base_node's arm_home_pose_rad (single source: base.yaml)."""
    try:
        path = os.path.join(get_package_share_directory('jetrover_base'), 'config', 'base.yaml')
        with open(path) as f:
            params = yaml.safe_load(f)['base_node']['ros__parameters']
        names = list(params['arm_joint_names'])
        home = list(params['arm_home_pose_rad'])
        joints = [f'joint{i}' for i in range(1, 6)]
        return [float(home[names.index(j)]) for j in joints]
    except Exception as e:  # noqa: BLE001 -- gate is then disabled, node warns about it
        print(f'[camera.launch] could not read arm home pose from base.yaml: {e}')
        return [0.0]


def launch_setup(context):
    camera_name = LaunchConfiguration('camera_name').perform(context)
    params_file = os.path.join(
        get_package_share_directory('jetrover_perception'), 'config', 'dabai_dcw.yaml')

    # 한글: 카메라 드라이버를 composable node로 실행한다. 파라미터는 config/dabai_dcw.yaml.
    container = ComposableNodeContainer(
        name='camera_container',
        namespace=camera_name,
        package='rclcpp_components',
        executable='component_container',
        composable_node_descriptions=[
            ComposableNode(
                package='orbbec_camera',
                plugin='orbbec_camera::OBCameraNodeDriver',
                name=camera_name,
                namespace=camera_name,
                parameters=[params_file, {'camera_name': camera_name}],
            ),
        ],
        output='screen',
    )

    # Republishes depth/image_raw (16UC1, unviewable as-is) as a colorized bgr8
    # image on depth/image_colorized, so it can be streamed/viewed normally
    # (web_video_server, rqt_image_view). See troubleshooting/019.
    # 한글: 16UC1 depth를 컬러 영상으로 바꿔 웹/rqt에서 볼 수 있게 한다(troubleshooting/019).
    depth_colorizer = Node(
        package='jetrover_perception',
        executable='depth_colorizer.py',
        name='depth_colorizer',
        namespace=camera_name,
        output='screen',
        # 한글: Nav2 시험 중에는 colorizer:=false (CPU 과부하로 컨트롤러가 3 Hz까지 떨어짐, troubleshooting/028/031).
        condition=IfCondition(LaunchConfiguration('colorizer')),
    )

    depth_source = LaunchConfiguration('depth_source').perform(context)
    if depth_source not in ('default', 'corrected'):
        raise ValueError('depth_source must be default or corrected')
    cloud_remappings = []
    cloud_extra = {}
    if depth_source == 'corrected':
        # The old self-filter reference is invalid after changing the reprojection.
        # 한글: 재투영이 바뀌면 기존 자기 차폐 기준 영상은 유효하지 않다.
        guard_file = os.path.join(get_package_share_directory('jetrover_perception'), 'launch', 'depth_source_guard.py')
        spec = importlib.util.spec_from_file_location('depth_source_guard', guard_file)
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        reference = LaunchConfiguration('corrected_background_path').perform(context)
        calibration = os.path.expanduser('~/.local/share/jetinspect-ops/calibration/rgbd-extrinsic-active.json')
        cloud_extra['background_depth_path'] = guard.validate_corrected_background(reference, calibration)
        cloud_extra['background_calibration_path'] = calibration
        with open(calibration, 'rb') as active_file:
            cloud_extra['background_calibration_sha256'] = hashlib.sha256(active_file.read()).hexdigest()
        cloud_remappings = [('depth/image_raw', 'depth_corrected/image_raw'),
                            ('depth/camera_info', 'depth_corrected/camera_info')]

    # Sparse PointCloud2 built from a strided (downsampled) depth image, instead
    # of the camera driver's own heavy enable_point_cloud (troubleshooting/019).
    # 한글: 드라이버의 무거운 포인트클라우드 대신, 간격을 둔 depth 영상으로 가벼운 PointCloud2를 만든다.
    sparse_point_cloud = Node(
        package='jetrover_perception',
        executable='sparse_point_cloud.py',
        name='sparse_point_cloud',
        namespace=camera_name,
        output='screen',
        remappings=cloud_remappings,
        # depth_publish_clearing / depth_extrude_m (2026-10-25): 실기 시험(8.15/8.16 6번) 통과 후
        # 기본값을 켬 / 0.25 m로(이전 끔 / 0.15 m). 공식 nav2_params.yaml의 depth_clear 관측원이
        # depth/points_clear를 쓴다(troubleshooting/053).
        # Defaults switched on after the real tests (was off / 0.15 m); depth_clear needs them.
        parameters=[{
            'floor_aware': LaunchConfiguration('depth_floor_aware').perform(context) == 'true',
            'home_pose_rad': _arm_home_pose(),
            'expected_depth_frame': camera_name + '_color_optical_frame',
            **cloud_extra,
            'publish_clearing':
                LaunchConfiguration('depth_publish_clearing').perform(context) == 'true',
            'extrude_depth_m': float(LaunchConfiguration('depth_extrude_m').perform(context)),
        }],
    )

    # depth 장애물 점에서 LiDAR가 보는 점을 뺀 낮은 물체만 depth/points_low로
    # (2026-10-25 시험, troubleshooting/055). 기본 끔. nav2_params_real_low.yaml과 함께 쓴다.
    # Low-only depth cloud for the Nav2 depth layer (off by default).
    depth_scan_filter = Node(
        package='jetrover_perception',
        executable='depth_scan_filter.py',
        name='depth_scan_filter',
        namespace=camera_name,
        output='screen',
        condition=IfCondition(LaunchConfiguration('depth_lidar_filter')),
        remappings=[('points_in', 'depth/points_sparse'),
                    ('points_out', 'depth/points_low'), ('scan', '/scan')],
    )

    return [container, depth_colorizer, sparse_point_cloud, depth_scan_filter]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('camera_name', default_value='depth_cam'),
        DeclareLaunchArgument('depth_source', default_value='default', description='default or corrected depth for obstacle cloud'),
        DeclareLaunchArgument('corrected_background_path', default_value='', description='verified corrected depth background npy'),
        DeclareLaunchArgument(
            'colorizer', default_value='true',
            description='Run depth_colorizer (viewing only); false during Nav2 tests to save CPU'),
        DeclareLaunchArgument(
            'depth_publish_clearing', default_value='true',
            description='sparse_point_cloud: also publish free-floor points on '
                        'depth/points_clear (clearing-only source)'),
        DeclareLaunchArgument('depth_floor_aware', default_value='false',
                              description='Enable experimental floor-aware obstacle detection'),
        DeclareLaunchArgument(
            'depth_lidar_filter', default_value='false',
            description='run depth_scan_filter: depth/points_low without points the LiDAR sees'),
        DeclareLaunchArgument(
            'depth_extrude_m', default_value='0.25',
            description='sparse_point_cloud: extend obstacle points behind the seen face '
                        '(sim tests used 0.25)'),
        OpaqueFunction(function=launch_setup),
    ])
