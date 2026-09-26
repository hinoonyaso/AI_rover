#!/usr/bin/env python3
"""End-to-end test of base_node -> wheel_twist/imu -> robot_localization EKF -> /odom.

No robot needed: base_node talks to a virtual serial port fed with fake IMU frames.
Needs robot_localization and installed jetrover_base/jetrover_description (source install/setup.bash).
The fake gyro is driven by the test, so yaw changes come from it, like the real gyro.
"""
import math
import os
import pty
import select
import signal
import struct
import subprocess
import tempfile
import threading
import time
import tty

import rclpy
from ament_index_python.packages import get_package_prefix, get_package_share_directory
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node


def crc(b):
    c = 0
    for x in b:
        c ^= x
        for _ in range(8):
            c = (c >> 1) ^ 0x8C if c & 1 else c >> 1
    return c


def frame(func, data):
    f = bytes([0xAA, 0x55, func, len(data)]) + bytes(data)
    return f + bytes([crc(f[2:])])


master, slave = pty.openpty()
tty.setraw(master)
path = os.ttyname(slave)
stop = threading.Event()
gz_deg = [0.0]  # fake sensor gz in deg/s (ROS wz = -gz)


def feeder():
    while not stop.is_set():
        imu = struct.pack('<6f', 0.0, 0.0, -0.96, 0.0, 0.0, gz_deg[0])
        os.write(master, frame(7, imu))
        if select.select([master], [], [], 0)[0]:
            os.read(master, 4096)
        time.sleep(0.01)


threading.Thread(target=feeder, daemon=True).start()

share = get_package_share_directory('jetrover_base')


def exe(pkg, name):
    """Run the executable directly: SIGINT sent to a `ros2 run` wrapper does not reach the node."""
    return os.path.join(get_package_prefix(pkg), 'lib', pkg, name)


urdf_path = os.path.join(get_package_share_directory('jetrover_description'), 'urdf',
                         'jetrover.urdf')
with open(urdf_path) as f:
    urdf = f.read()
# A multi-line URDF cannot be passed with `-p`; use a parameters file.
rsp_params = tempfile.NamedTemporaryFile('w', suffix='.yaml', delete=False)
rsp_params.write('robot_state_publisher:\n  ros__parameters:\n    robot_description: |\n')
rsp_params.write(''.join('      ' + line + '\n' for line in urdf.splitlines()))
rsp_params.close()

procs = [
    subprocess.Popen([exe('jetrover_base', 'base_node'), '--ros-args', '-p', f'port:={path}']),
    subprocess.Popen([exe('robot_state_publisher', 'robot_state_publisher'), '--ros-args',
                      '--params-file', rsp_params.name]),
    subprocess.Popen([exe('robot_localization', 'ekf_node'), '--ros-args',
                      '--params-file', os.path.join(share, 'config', 'ekf.yaml'),
                      '-r', '__node:=ekf_filter_node', '-r', 'odometry/filtered:=odom']),
]

rclpy.init()
n = Node('ekf_pipeline_test')
pub = n.create_publisher(Twist, 'cmd_vel', 1)
odom = [None]
n.create_subscription(Odometry, 'odom', lambda m: odom.__setitem__(0, m), 10)


def spin(t):
    end = time.monotonic() + t
    while time.monotonic() < end:
        rclpy.spin_once(n, timeout_sec=0.01)


def drive(vx, secs):
    end = time.monotonic() + secs
    while time.monotonic() < end:
        t = Twist()
        t.linear.x = float(vx)
        pub.publish(t)
        spin(0.05)


def pose():
    m = odom[0]
    q = m.pose.pose.orientation
    yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
    return m.pose.pose.position.x, m.pose.pose.position.y, yaw


exit_code = 1
try:
    spin(4.0)
    if odom[0] is None:
        raise SystemExit('no /odom from the EKF: is robot_localization running?')
    p0 = pose()
    print(f'idle            x={p0[0]:+.3f} y={p0[1]:+.3f} yaw={p0[2]:+.3f}')
    drive(0.1, 2.0)
    spin(1.5)
    p1 = pose()
    print(f'fwd 0.1 x 2s    dx={p1[0]-p0[0]:+.3f} dy={p1[1]-p0[1]:+.3f} dyaw={p1[2]-p0[2]:+.3f}'
          '   (expect dx~+0.2..0.25, dy~0, dyaw~0)')
    gz_deg[0] = -0.2 * 180 / math.pi  # ROS wz = +0.2 rad/s
    spin(3.0)
    gz_deg[0] = 0.0
    spin(1.0)
    p2 = pose()
    print(f'gyro +0.2x3s    dyaw={p2[2]-p1[2]:+.3f} rad   (expect ~+0.6), no position change: '
          f'{math.hypot(p2[0]-p1[0], p2[1]-p1[1]):.3f} m')
    drive(0.1, 2.0)
    spin(1.5)
    p3 = pose()
    print(f'fwd after turn  dx={p3[0]-p2[0]:+.3f} dy={p3[1]-p2[1]:+.3f}   '
          f'(expect ~+0.20 / +0.14 = 0.25 m along yaw {p2[2]:+.2f})')
    checks = {
        'forward dx ~ 0.25': abs((p1[0] - p0[0]) - 0.25) < 0.03,
        'forward dy ~ 0': abs(p1[1] - p0[1]) < 0.02,
        'gyro yaw ~ +0.6': abs((p2[2] - p1[2]) - 0.6) < 0.05,
        'turned forward dy ~ +0.14': abs((p3[1] - p2[1]) - 0.14) < 0.03,
    }
    failed = [name for name, ok in checks.items() if not ok]
    print('RESULT:', 'PASS' if not failed else 'FAIL: ' + ', '.join(failed))
    exit_code = 1 if failed else 0
finally:
    stop.set()
    for p in procs:
        p.send_signal(signal.SIGINT)
    for p in procs:
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
    os.unlink(rsp_params.name)
    rclpy.shutdown()
    raise SystemExit(exit_code)
