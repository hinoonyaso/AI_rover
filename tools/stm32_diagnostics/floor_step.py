#!/usr/bin/env python3
# 한글: 실제 base_node를 통한 바닥에서의 짧고 감독된 1회 이동(최대 0.2m/s, 6초, 0.8m). IMU가 0.5초 넘게 끊기면 즉시 중단하고 정지한다. 끝나면 정지 명령을 반복 발행한다.
"""One short, supervised move on the floor through the real base_node.

Usage: python3 floor_step.py VX VY WZ SECONDS      (m/s, m/s, rad/s, s; max 0.2 m/s, 6 s, 0.8 m)
Needs `ros2 launch jetrover_base base.launch.py` running. Publishes /cmd_vel at 20 Hz for SECONDS,
then zero repeatedly, and reports the EKF displacement and whether the STM32 kept streaming.
Aborts (and stops) if IMU data stops for more than 0.5 s while moving.
"""
import math
import sys
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import BatteryState, Imu

MAX_SPEED = 0.2      # m/s, same as base_node's own limit
MAX_SECONDS = 6.0
MAX_DISTANCE = 0.8   # m per move, including the 0.5 s watchdog tail


def yaw_of(m):
    q = m.pose.pose.orientation
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def main():
    vx, vy, wz, secs = (float(a) for a in sys.argv[1:5])
    if max(abs(vx), abs(vy)) > MAX_SPEED or secs > MAX_SECONDS or abs(wz) > 0.5:
        sys.exit(f'refused: limits are {MAX_SPEED} m/s, 0.5 rad/s, {MAX_SECONDS} s')
    if math.hypot(vx, vy) * (secs + 0.5) > MAX_DISTANCE:
        sys.exit(f'refused: this move would cover more than {MAX_DISTANCE} m')

    rclpy.init()
    n = Node('floor_step')
    pub = n.create_publisher(Twist, 'cmd_vel', 1)
    odom = [None]
    imu = {'n': 0, 'last': time.monotonic()}
    volts = []

    def on_imu(_):
        imu['n'] += 1
        imu['last'] = time.monotonic()

    n.create_subscription(Odometry, 'odom', lambda m: odom.__setitem__(0, m), 10)
    n.create_subscription(Imu, 'imu/data_raw', on_imu, qos_profile_sensor_data)
    n.create_subscription(BatteryState, 'battery_state', lambda m: volts.append(m.voltage), 10)

    def spin(t):
        end = time.monotonic() + t
        while time.monotonic() < end:
            rclpy.spin_once(n, timeout_sec=0.01)

    def stop():
        for _ in range(10):
            pub.publish(Twist())
            spin(0.03)

    spin(1.5)
    if odom[0] is None or time.monotonic() - imu['last'] > 0.5:
        sys.exit('no /odom or no IMU: is the launch running and the STM32 alive?')
    x0, y0, w0 = odom[0].pose.pose.position.x, odom[0].pose.pose.position.y, yaw_of(odom[0])
    n0 = imu['n']
    aborted = False
    try:
        end = time.monotonic() + secs
        while time.monotonic() < end:
            t = Twist()
            t.linear.x, t.linear.y, t.angular.z = float(vx), float(vy), float(wz)
            pub.publish(t)
            spin(0.05)
            if time.monotonic() - imu['last'] > 0.5:
                aborted = True
                print('!!! IMU silent while moving: aborting', flush=True)
                break
    finally:
        stop()
    spin(1.5)
    silent = time.monotonic() - imu['last']
    m = odom[0]
    dx, dy = m.pose.pose.position.x - x0, m.pose.pose.position.y - y0
    dyaw = math.degrees(yaw_of(m) - w0)
    dyaw = (dyaw + 180) % 360 - 180
    body_x = dx * math.cos(w0) + dy * math.sin(w0)
    body_y = -dx * math.sin(w0) + dy * math.cos(w0)
    print(f'cmd vx={vx:+.2f} vy={vy:+.2f} wz={wz:+.2f} for {secs:.1f}s')
    print(f'EKF displacement (body frame): forward {body_x:+.3f} m, left {body_y:+.3f} m, yaw {dyaw:+.1f} deg')
    print(f'battery: {volts[-1]:.2f} V (min {min(volts):.2f} over the test)' if volts else 'battery: no battery_state yet')
    print(f'IMU frames during test: {imu["n"] - n0}, silent for {silent:.2f}s now -> '
          f'{"STM32 OK" if silent < 0.5 and not aborted else "STM32 NOT RESPONDING"}')
    rclpy.shutdown()
    sys.exit(1 if aborted or silent >= 0.5 else 0)


if __name__ == '__main__':
    main()
