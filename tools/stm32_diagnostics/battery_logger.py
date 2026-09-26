#!/usr/bin/env python3
"""Log /battery_state and the IMU rate once per second to a file (run alongside base_node).

Usage: python3 battery_logger.py OUTFILE [seconds]
Each line: wall time, battery volts, IMU frames in the last second. If the STM32 hangs, the last
line before the IMU count drops to 0 shows the voltage at that moment.
"""
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import BatteryState, Imu


def main():
    out = open(sys.argv[1], 'a', buffering=1)
    duration = float(sys.argv[2]) if len(sys.argv) > 2 else 3600.0
    rclpy.init()
    n = Node('battery_logger')
    st = {'v': float('nan'), 'imu': 0}
    n.create_subscription(BatteryState, 'battery_state', lambda m: st.__setitem__('v', m.voltage), 10)
    n.create_subscription(Imu, 'imu/data_raw', lambda m: st.__setitem__('imu', st['imu'] + 1),
                          qos_profile_sensor_data)
    end = time.monotonic() + duration
    nxt = time.monotonic() + 1.0
    while time.monotonic() < end and rclpy.ok():
        rclpy.spin_once(n, timeout_sec=0.05)
        if time.monotonic() >= nxt:
            out.write(f'{time.strftime("%H:%M:%S")} battery={st["v"]:.3f}V imu_per_s={st["imu"]}\n')
            st['imu'] = 0
            nxt += 1.0


if __name__ == '__main__':
    main()
