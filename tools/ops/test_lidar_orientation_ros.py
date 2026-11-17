"""Isolated ROS scan and TF orientation integration.

한글: 격리 ROS 스캔과 TF 방향 연동 시험이다.
"""
import json
import os
import subprocess
import time
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TransformStamped
from tf2_ros import StaticTransformBroadcaster


def main():
    """Publish fake static TF and scans; no physical device is used.

    한글: 실제 장치 없이 가상 정적 TF와 스캔을 발행한다.
    """
    if os.environ.get('ROS_DOMAIN_ID') != '186': raise RuntimeError('isolated ROS domain required')
    rclpy.init(); node=Node('fake_scan_publisher')
    broadcaster=StaticTransformBroadcaster(node)
    tf=TransformStamped();tf.header.stamp=node.get_clock().now().to_msg();tf.header.frame_id='base_link';tf.child_frame_id='test_laser';tf.transform.rotation.w=1.
    broadcaster.sendTransform(tf)
    publisher=node.create_publisher(LaserScan,'/scan',qos_profile_sensor_data)
    proc=subprocess.Popen(['/usr/bin/python3',os.path.join(os.path.dirname(__file__),'calibration/lidar_orientation.py'),'0','1.5'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        end=time.monotonic()+10
        while proc.poll() is None and time.monotonic()<end:
            scan=LaserScan();scan.header.frame_id='test_laser';scan.header.stamp=node.get_clock().now().to_msg();scan.angle_min=-.02;scan.angle_increment=.01;scan.range_min=.05;scan.range_max=5.;scan.ranges=[.5]*5
            publisher.publish(scan);rclpy.spin_once(node,timeout_sec=.03)
        out,err=proc.communicate(timeout=3)
        if proc.returncode:raise RuntimeError(out+' '+err)
        result=json.loads(out)['result']
        assert abs(result['difference_deg']) < .1 and result['scan_frame']=='test_laser', result
        print('PASS isolated ROS scan, timestamped TF, and bearing')
    finally:
        if proc.poll() is None:proc.kill();proc.wait()
        node.destroy_node();rclpy.shutdown()

if __name__ == '__main__':main()
