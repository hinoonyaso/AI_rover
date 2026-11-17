"""Verify isolated ROS odometry reception and continuous displacement.

한글: 격리 ROS 오도메트리 수신 및 연속 이동 계산을 검증한다.
"""
import os
import sys
import tempfile
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'backend'))
import rclpy
from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor
from nav_msgs.msg import Odometry
from ros_monitor import SensorMonitor
from odom_observation import odom_displacement


def main():
    """Publish synthetic odometry without robot actuators. / 실제 구동 없이 가상 오도메트리를 발행한다."""
    if os.environ.get('ROS_DOMAIN_ID') != '185': raise RuntimeError('isolated domain required')
    with tempfile.TemporaryDirectory() as directory:
        os.environ['HOME']=directory;rclpy.init();sender=Node('fake_odom');monitor=SensorMonitor()
        executor=SingleThreadedExecutor();executor.add_node(sender);executor.add_node(monitor)
        publisher=sender.create_publisher(Odometry,'/odom_raw',10)
        start=None; result=None; deadline=time.monotonic()+8; pos=0.
        try:
            while time.monotonic()<deadline:
                msg=Odometry();msg.header.frame_id='odom';msg.child_frame_id='base_link';msg.header.stamp=sender.get_clock().now().to_msg()
                msg.pose.pose.orientation.w=1.;msg.pose.pose.position.x=pos;publisher.publish(msg)
                executor.spin_once(timeout_sec=.05)
                current=monitor.odom['raw'].value
                if current and start is None:start=current
                if start and current and current['stamp']>start['stamp'] and current['x_m']>start['x_m']:
                    result=odom_displacement(start,current,'forward');break
                pos+=.01
            assert result is not None and result>0, result
            print('PASS isolated ROS odometry -> monitor -> displacement')
        finally:
            executor.shutdown();monitor.destroy_node();sender.destroy_node();rclpy.shutdown()

if __name__ == '__main__':main()
