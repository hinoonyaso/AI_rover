"""Verify isolated compiled base-node wheel feedback, without motor commands.

한글: 모터 명령 없이 격리된 base_node의 휠 피드백 연동을 검증한다.
"""
import os
import pty
import select
import signal
import struct
import subprocess
import tempfile
import time
from pathlib import Path
import rclpy
from rclpy.executors import SingleThreadedExecutor
from ros_monitor import SensorMonitor


def frame():
    """Encode synthetic four-port feedback. / 가상 네 포트 피드백을 인코딩한다."""
    body = bytes([0x21, 32]) + struct.pack('<4f4i', 1.0, 2.0, -3.0, -4.0, 10, 20, 30, 40)
    crc = 0
    for value in body:
        crc ^= value
        for _ in range(8):
            crc = (crc >> 1) ^ (0x8c if crc & 1 else 0)
    return bytes([0xaa,0x55]) + body + bytes([crc])


def main():
    """Pass synthetic feedback through serial, ROS, and monitor without writes.

    한글: 시리얼·ROS·모니터 경로를 가상 피드백으로 검증하며 장치에 쓰지 않는다.
    """
    if os.environ.get('ROS_DOMAIN_ID') != '187':
        raise RuntimeError('requires isolated ROS domain 187')
    executable = '/tmp/jetrover-calibration-install/jetrover_base/lib/jetrover_base/base_node'
    if not Path(executable).is_file(): raise RuntimeError('isolated base build missing')
    with tempfile.TemporaryDirectory() as directory:
        os.environ['HOME'] = directory
        master, slave = pty.openpty()
        proc = subprocess.Popen([executable, '--ros-args', '-p', f'port:={os.ttyname(slave)}', '-p', 'sensor_only:=true'],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        rclpy.init(); monitor=SensorMonitor(); executor=SingleThreadedExecutor();executor.add_node(monitor)
        outgoing=bytearray()
        try:
            deadline=time.monotonic()+12
            while time.monotonic()<deadline and monitor.wheel_feedback is None:
                if proc.poll() is not None: raise RuntimeError('base node exited')
                os.write(master,frame());executor.spin_once(timeout_sec=.05)
                if select.select([master],[],[],0)[0]: outgoing.extend(os.read(master,4096))
            assert monitor.wheel_feedback is not None, 'wheel feedback not received'
            assert monitor.wheel_feedback['port_rps'] == [1.,2.,-3.,-4.]
            assert monitor.wheel_feedback['port_counter'] == [10,20,30,40]
            if outgoing: raise RuntimeError('unexpected serial writes')
            print('PASS isolated serial -> base node -> ROS -> monitor wheel feedback')
        finally:
            proc.send_signal(signal.SIGINT)
            try:proc.wait(timeout=8)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
            time.sleep(.2)
            if select.select([master],[],[],0)[0]: outgoing.extend(os.read(master,4096))
            executor.shutdown();monitor.destroy_node();rclpy.shutdown();os.close(master);os.close(slave)
        if outgoing: raise RuntimeError('unexpected serial writes including shutdown')

if __name__ == '__main__':main()
