"""Test IMU acceleration parameters via pseudo-serial and isolated ROS.

한글: 가상 시리얼과 격리 ROS로 가속도 적용 파라미터를 시험한다.
"""
import os
import pty
import select
import signal
import subprocess
import time
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu
from test_sensor_only_ros import frame


def main():
    """Check calibrated IMU values without actuator writes. / 구동 쓰기 없이 보정된 IMU를 확인한다."""
    if os.environ.get('ROS_DOMAIN_ID') != '184':raise RuntimeError('isolated ROS domain required')
    master,slave=pty.openpty()
    exe='/tmp/jetrover-calibration-install/jetrover_base/lib/jetrover_base/base_node'
    proc=subprocess.Popen([exe,'--ros-args','-p',f'port:={os.ttyname(slave)}','-p','sensor_only:=true',
                           '-p','accel_offset_m_s2:=[0.0,0.0,1.0]','-p','accel_scale:=[1.0,1.0,2.0]'],
                          stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
    rclpy.init();node=Node('test_accel_apply');received=[];outgoing=bytearray()
    node.create_subscription(Imu,'/imu/data_raw',lambda m:received.append(m),qos_profile_sensor_data)
    try:
        end=time.monotonic()+12
        while time.monotonic()<end and len(received)<5:
            if proc.poll() is not None:raise RuntimeError('base node exited')
            os.write(master,frame());rclpy.spin_once(node,timeout_sec=.05)
            if select.select([master],[],[],0)[0]:outgoing.extend(os.read(master,4096))
        if not received:raise RuntimeError('no IMU output')
        actual=received[-1].linear_acceleration.z
        assert abs(actual-2*(9.80665-1))<.01,actual
        assert abs(received[-1].linear_acceleration_covariance[8]-.016)<1e-6
    finally:
        proc.send_signal(signal.SIGINT)
        try:proc.wait(timeout=8)
        except subprocess.TimeoutExpired:proc.kill();proc.wait()
        time.sleep(.2)
        if select.select([master],[],[],0)[0]:outgoing.extend(os.read(master,4096))
        node.destroy_node();rclpy.shutdown();os.close(master);os.close(slave)
    if outgoing:raise RuntimeError('unexpected serial writes')
    print('PASS pseudo-serial -> calibrated IMU -> ROS; no actuator writes')

if __name__=='__main__':main()
