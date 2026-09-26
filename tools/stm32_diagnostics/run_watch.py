#!/usr/bin/env python3
"""Watch the STM32 and the battery while the robot drives; exit with a message on trouble.

Usage: python3 run_watch.py [--min-volts 9.3] [--silent 2.0] [--snapshot-every 20] [--log FILE]
Run next to `robot.launch.py`. Exits (code 2) as soon as
  - no IMU frame arrived for --silent seconds (STM32 hang), or
  - the battery voltage is below --min-volts.
Also keeps tools/viz/out/snapshot.png fresh every --snapshot-every seconds (0 = off) and logs
battery / IMU rate / commanded speed once per second to --log.
"""
import argparse
import os
import subprocess
import sys
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import BatteryState, Imu

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = os.path.join(HERE, '..', 'viz', 'snapshot.py')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--min-volts', type=float, default=9.3)
    ap.add_argument('--silent', type=float, default=2.0)
    ap.add_argument('--snapshot-every', type=float, default=20.0)
    ap.add_argument('--log', default=os.path.expanduser('~/jetrover_ws/tools/stm32_diagnostics/watch.log'))
    args = ap.parse_args()

    rclpy.init()
    n = Node('run_watch')
    st = {'imu': 0, 'last_imu': time.monotonic(), 'v': float('nan'), 'vmin': 99.0, 'cmd': (0.0, 0.0, 0.0)}

    def on_imu(_):
        st['imu'] += 1
        st['last_imu'] = time.monotonic()

    def on_batt(m):
        st['v'] = m.voltage
        st['vmin'] = min(st['vmin'], m.voltage)

    def on_cmd(m):
        st['cmd'] = (m.linear.x, m.linear.y, m.angular.z)

    n.create_subscription(Imu, 'imu/data_raw', on_imu, qos_profile_sensor_data)
    n.create_subscription(BatteryState, 'battery_state', on_batt, 10)
    n.create_subscription(Twist, 'cmd_vel', on_cmd, 10)

    log = open(args.log, 'a', buffering=1)
    t0 = time.monotonic()
    nxt_log, nxt_snap = t0 + 1.0, t0 + 5.0
    reason = None
    while rclpy.ok():
        rclpy.spin_once(n, timeout_sec=0.05)
        now = time.monotonic()
        if now - st['last_imu'] > args.silent and now - t0 > 3.0:
            reason = (f'STM32 SILENT for {now - st["last_imu"]:.1f}s (voltage last {st["v"]:.2f} V, '
                      f'min {st["vmin"]:.2f} V, last cmd {st["cmd"]})')
            break
        if st['v'] == st['v'] and st['v'] < args.min_volts:
            reason = f'BATTERY LOW: {st["v"]:.2f} V (below {args.min_volts} V)'
            break
        if now >= nxt_log:
            log.write(f'{time.strftime("%H:%M:%S")} battery={st["v"]:.3f}V imu_per_s={st["imu"]} '
                      f'cmd=({st["cmd"][0]:+.2f},{st["cmd"][1]:+.2f},{st["cmd"][2]:+.2f})\n')
            st['imu'] = 0
            nxt_log += 1.0
        if args.snapshot_every > 0 and now >= nxt_snap:
            subprocess.Popen([sys.executable, SNAPSHOT, '--frame', 'map', '--seconds', '1.5'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            nxt_snap += args.snapshot_every
    log.write(f'{time.strftime("%H:%M:%S")} ALERT: {reason}\n')
    print('ALERT:', reason, flush=True)
    rclpy.shutdown()
    sys.exit(2)


if __name__ == '__main__':
    main()
