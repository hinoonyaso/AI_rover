# Orbbec DaBai DCW (RGB-D) bringup, same driver/parameters Hiwonder uses
# (src/peripherals/launch/include/dabai_dcw.launch.py in their JetRover repo), but WITHOUT
# their color->rgb topic remap: their own rtabmap_slam.launch.py subscribes to the un-remapped
# ".../color/image_raw" and ".../color/camera_info", so we keep the driver's natural names.
import os

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

    # Sparse PointCloud2 built from a strided (downsampled) depth image, instead
    # of the camera driver's own heavy enable_point_cloud (troubleshooting/019).
    # 한글: 드라이버의 무거운 포인트클라우드 대신, 간격을 둔 depth 영상으로 가벼운 PointCloud2를 만든다.
    sparse_point_cloud = Node(
        package='jetrover_perception',
        executable='sparse_point_cloud.py',
        name='sparse_point_cloud',
        namespace=camera_name,
        output='screen',
        parameters=[{'home_pose_rad': _arm_home_pose()}],
    )

    return [container, depth_colorizer, sparse_point_cloud]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('camera_name', default_value='depth_cam'),
        DeclareLaunchArgument(
            'colorizer', default_value='true',
            description='Run depth_colorizer (viewing only); false during Nav2 tests to save CPU'),
        OpaqueFunction(function=launch_setup),
    ])
