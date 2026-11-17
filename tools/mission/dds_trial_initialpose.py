"""Initialize a verified Gazebo pose in the dedicated transport-test domain.

한글: 전송 비교 전용 도메인에서 확인된 Gazebo의 초기 위치만 설정한다.
"""
import math
import os
import time

from gazebo_nav_trial import verify_gazebo_pose


def main():
    """Set AMCL initial pose after verifying simulated hardware. / 가상 하드웨어 확인 후 AMCL 초기 위치를 설정한다."""
    if (os.environ.get('ROS_DOMAIN_ID') != '98' or os.environ.get('GZ_IP') != '127.0.0.1' or
            os.environ.get('RMW_IMPLEMENTATION') != 'rmw_fastrtps_cpp' or
            os.environ.get('ROS_AUTOMATIC_DISCOVERY_RANGE') not in ('LOCALHOST', 'SUBNET') or
            any(os.environ.get(k) for k in ('ROS_STATIC_PEERS', 'ROS_DISCOVERY_SERVER', 'CYCLONEDDS_URI'))):
        raise RuntimeError('isolated transport test configuration required')
    import rclpy
    from controller_manager_msgs.srv import ListHardwareComponents
    from geometry_msgs.msg import PoseWithCovarianceStamped
    from rclpy.node import Node
    from rclpy.parameter import Parameter
    from tf2_ros import Buffer, TransformException, TransformListener

    verify_gazebo_pose()
    rclpy.init()
    node = Node('isolated_transport_initialpose', parameter_overrides=[Parameter('use_sim_time', value=True)])
    try:
        client = node.create_client(ListHardwareComponents, '/controller_manager/list_hardware_components')
        if not client.wait_for_service(timeout_sec=12):
            raise RuntimeError('simulation controller unavailable')
        future = client.call_async(ListHardwareComponents.Request())
        deadline = time.monotonic() + 12
        while not future.done() and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=.1)
        if (not future.done() or future.result() is None or len(future.result().component) != 1 or
                future.result().component[0].name != 'GazeboSimSystem' or
                future.result().component[0].state.label != 'active' or 'base_node' in node.get_node_names()):
            raise RuntimeError('simulated hardware not verified')
        pub = node.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
        buffer = Buffer()
        listener = TransformListener(buffer, node)
        pose = PoseWithCovarianceStamped()
        pose.header.frame_id = 'map'
        pose.pose.pose.position.x, pose.pose.pose.position.y = 1.02, .37
        pose.pose.pose.orientation.z, pose.pose.pose.orientation.w = math.sin(1.45 / 2), math.cos(1.45 / 2)
        pose.pose.covariance[0] = pose.pose.covariance[7] = .01
        pose.pose.covariance[35] = .02
        deadline = time.monotonic() + 40
        next_send = 0.0
        while time.monotonic() < deadline:
            if pub.get_subscription_count() and time.monotonic() >= next_send:
                pose.header.stamp = node.get_clock().now().to_msg()
                pub.publish(pose)
                next_send = time.monotonic() + 1
            rclpy.spin_once(node, timeout_sec=.2)
            try:
                p = buffer.lookup_transform('map', 'base_footprint', rclpy.time.Time()).transform.translation
                if math.hypot(p.x - 1.02, p.y - .37) < .2:
                    print('simulated localization verified; no navigation goal sent', flush=True)
                    return
            except TransformException:
                pass
        raise RuntimeError('simulation localization not confirmed')
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
