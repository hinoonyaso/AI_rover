"""Test six-pose worker against isolated IMU and runtime parameter service.

한글: 격리 IMU와 런타임 파라미터 서비스로 여섯 자세 측정 워커를 시험한다.
"""
import json
import os
import subprocess
import time
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu


def main():
    """Publish stationary z-up samples from a fake base node. / 가상 노드에서 정지 Z축 표본을 발행한다."""
    if os.environ.get('ROS_DOMAIN_ID') != '183': raise RuntimeError('isolated ROS domain required')
    rclpy.init(); node=Node('base_node')
    node.declare_parameter('accel_offset_m_s2',[0.,0.,0.]);node.declare_parameter('accel_scale',[1.,1.,1.])
    pub=node.create_publisher(Imu,'/imu/data_raw',qos_profile_sensor_data)
    worker=Path(__file__).resolve().parents[1]/'imu_calibration/dashboard_accel_pose.py'
    proc=subprocess.Popen(['/usr/bin/python3',str(worker),'z_plus'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        deadline=time.monotonic()+14
        while proc.poll() is None and time.monotonic()<deadline:
            msg=Imu();msg.header.frame_id='imu_link';msg.header.stamp=node.get_clock().now().to_msg();msg.linear_acceleration.z=9.80665
            pub.publish(msg);rclpy.spin_once(node,timeout_sec=.015)
        out,err=proc.communicate(timeout=3)
        if proc.returncode:raise RuntimeError(out+' '+err)
        result=json.loads(out)['result']
        assert result['current_offset_m_s2']==[0.,0.,0.] and result['current_scale']==[1.,1.,1.]
        assert result['samples']>=50
        print('PASS fake ROS parameter service and stationary accelerometer pose')
    finally:
        if proc.poll() is None:proc.kill();proc.wait()
        node.destroy_node();rclpy.shutdown()

if __name__=='__main__':main()
