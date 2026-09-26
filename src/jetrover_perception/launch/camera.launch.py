# Orbbec DaBai DCW (RGB-D) bringup, same driver/parameters Hiwonder uses
# (src/peripherals/launch/include/dabai_dcw.launch.py in their JetRover repo), but WITHOUT
# their color->rgb topic remap: their own rtabmap_slam.launch.py subscribes to the un-remapped
# ".../color/image_raw" and ".../color/camera_info", so we keep the driver's natural names.
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


def launch_setup(context):
    camera_name = LaunchConfiguration('camera_name').perform(context)
    params_file = os.path.join(
        get_package_share_directory('jetrover_perception'), 'config', 'dabai_dcw.yaml')

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
    return [container]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('camera_name', default_value='depth_cam'),
        OpaqueFunction(function=launch_setup),
    ])
