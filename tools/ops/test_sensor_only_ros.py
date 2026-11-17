"""Verify the compiled sensor-only node with an isolated pseudo-terminal.

한글: 격리 의사 터미널로 컴파일된 센서 전용 노드를 검증한다.
"""
import os
import pty
import select
import signal
import struct
import subprocess
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu


def frame():
    """Build a synthetic IMU frame. / 가상 IMU 프레임을 만든다."""
    body = bytes([7, 24]) + struct.pack('<6f', 0, 0, -1, 0, 0, 0)
    crc = 0
    for value in body:
        crc ^= value
        for _ in range(8):
            crc = (crc >> 1) ^ (0x8c if crc & 1 else 0)
    return bytes([0xaa, 0x55]) + body + bytes([crc])


def main():
    """Verify data reception and absence of actuator writes. / 센서 수신 및 구동 프레임 부재를 확인한다."""
    if os.environ.get('ROS_DOMAIN_ID') != '98' or os.environ.get('GZ_IP') != '127.0.0.1':
        raise RuntimeError('requires isolated test domain 98')
    master, slave = pty.openpty()
    name = os.ttyname(slave)
    executable = os.environ.get('JETINSPECT_TEST_BASE_NODE', os.path.expanduser('~/jetrover_ws/install/jetrover_base/lib/jetrover_base/base_node'))
    proc = subprocess.Popen([executable, '--ros-args', '-p', f'port:={name}', '-p', 'sensor_only:=true',
                             '-p', 'clear_estop_on_start:=true', '-p', 'motor_stop_frame_on_stop:=true',
                             '-p', 'arm_command_enabled:=true', '-p', 'publish_arm_joint_states:=true'],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    rclpy.init()
    node = Node('sensor_only_test')
    samples = []
    node.create_subscription(Imu, '/imu/data_raw', lambda msg: samples.append(msg), qos_profile_sensor_data)
    pub = node.create_publisher(Twist, '/cmd_vel', 10)
    outgoing = bytearray()
    try:
        until = time.monotonic() + 12
        while time.monotonic() < until:
            if proc.poll() is not None:
                raise RuntimeError('base node exited')
            os.write(master, frame())
            twist = Twist(); twist.linear.x = 0.2; pub.publish(twist)
            rclpy.spin_once(node, timeout_sec=0.05)
            if select.select([master], [], [], 0)[0]: outgoing.extend(os.read(master, 4096))
            if len(samples) >= 20 and time.monotonic() > until - 7: break
        if len(samples) < 20: raise RuntimeError('no IMU samples from pseudo-terminal')
        if pub.get_subscription_count() != 0: raise RuntimeError('sensor-only node subscribes to motor commands')
        if outgoing: raise RuntimeError(f'unexpected serial write: {outgoing.hex()}')
    finally:
        proc.send_signal(signal.SIGINT)
        try: proc.wait(timeout=8)
        except subprocess.TimeoutExpired: proc.kill(); proc.wait()
        time.sleep(.2)
        if select.select([master], [], [], 0)[0]: outgoing.extend(os.read(master, 4096))
        node.destroy_node(); rclpy.shutdown(); os.close(master); os.close(slave)
    if outgoing: raise RuntimeError(f'unexpected serial write on shutdown: {outgoing.hex()}')
    print(f'PASS IMU samples={len(samples)}, motor subscriber=0, serial writes=0 including shutdown')


if __name__ == '__main__': main()
