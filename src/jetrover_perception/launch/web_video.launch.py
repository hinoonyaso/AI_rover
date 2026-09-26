# Serves image topics as MJPEG over HTTP so they can be viewed from a plain browser
# (useful over VS Code Remote-SSH, where there is no local display for rqt_image_view/RViz).
# After this is running, forward the port (default 8080) in VS Code's "Ports" panel and open
# http://localhost:8080 in a browser: it lists every image topic with a clickable stream link,
# e.g. http://localhost:8080/stream?topic=/depth_cam/color/image_raw
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('port', default_value='8080'),
        Node(
            package='web_video_server',
            executable='web_video_server',
            name='web_video_server',
            output='screen',
            parameters=[{'port': LaunchConfiguration('port')}],
        ),
    ])
