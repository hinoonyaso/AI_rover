#!/usr/bin/env python3
# 한글: Gazebo 로봇의 운동 응답을 몸 기준 좌표로 잰다(전진/옆이동/대각/회전). 명령을 일정하게 내고 정답 위치로 실제 속도와
#       부수 이동(회전할 때 중심 이동 등)을 계산한다. Nav2의 /cmd_vel_nav 경로(속도 평활기·충돌 감시기 포함)로 보낸다.
#       실기 자체 펌웨어는 0.02~0.06 m/s를 비율 0.99~1.01로 추종(troubleshooting/…, E4/E5).
"""Command -> actual body-frame velocity of the simulated robot (ground truth), ROS_DOMAIN_ID=31, Nav2 running.

  python3 tools/sim/plant_response.py [--secs 6] [--only fwd left ...]
For each command (vx, vy, wz) the robot is teleported to the same start, the command is held for --secs seconds and the
ground-truth motion between t = 2 s and the end is converted to the body frame: forward, left (positive = left of the
robot's front), yaw rate. A good plant: the commanded component ratio ~ 1.0 and the other components ~ 0.
"""
import argparse
import math
import os
import sys
import time

from geometry_msgs.msg import Twist
import numpy as np
import rclpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import avoid_trials as T  # noqa: E402

CASES = {
    'fwd': (0.10, 0.0, 0.0), 'back': (-0.10, 0.0, 0.0),
    'left': (0.0, 0.10, 0.0), 'right': (0.0, -0.10, 0.0),
    'diag_fl': (0.07, 0.07, 0.0), 'diag_fr': (0.07, -0.07, 0.0),
    'spin_l': (0.0, 0.0, 0.30), 'spin_r': (0.0, 0.0, -0.30),
    'left_slow': (0.0, 0.04, 0.0), 'fwd_slow': (0.04, 0.0, 0.0), 'spin_slow': (0.0, 0.0, 0.10),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--secs', type=float, default=6.0)
    ap.add_argument('--only', nargs='+', default=list(CASES))
    args = ap.parse_args()
    rclpy.init()
    node, gt = T.Runner(), T.GroundTruth()
    pub = node.create_publisher(Twist, '/cmd_vel_nav', 10)
    try:
        node.spin(3.0)
        print(f'{"case":10s} {"cmd (vx vy wz)":>20s} | {"forward":>8s} {"left":>8s} {"yaw rate":>9s} | ratios fwd left yaw', flush=True)
        for name in args.only:
            vx, vy, wz = CASES[name]
            T.setup_leg(node, gt, 'S2', (1.02, 0.37, 83.0), (1.21, 1.00))
            gt.rows.clear()
            gt.recording = True
            t0 = time.time()
            while time.time() - t0 < args.secs:
                m = Twist()
                m.linear.x, m.linear.y, m.angular.z = vx, vy, wz
                pub.publish(m)
                node.spin(0.05)
            gt.recording = False
            node.spin(2.0)
            r = np.array(gt.rows)
            if len(r) < 20:
                print(f'{name:10s} no ground truth ({len(r)} rows)', flush=True)
                continue
            tt = r[:, 0] - r[0, 0]
            r = r[(tt >= 2.0) & (tt <= args.secs)]
            if len(r) < 10:
                print(f'{name:10s} too few rows in the window ({len(r)})', flush=True)
                continue
            dt = r[-1, 0] - r[0, 0]
            yaw = r[0, 3]
            dx, dy = r[-1, 1] - r[0, 1], r[-1, 2] - r[0, 2]
            fwd = (dx * math.cos(yaw) + dy * math.sin(yaw)) / dt
            left = (-dx * math.sin(yaw) + dy * math.cos(yaw)) / dt
            wzr = T.M.wrap(r[-1, 3] - r[0, 3]) / dt

            def ratio(a, c):
                return f'{a / c:5.2f}' if abs(c) > 1e-9 else '    -'
            print(f'{name:10s} ({vx:5.2f} {vy:5.2f} {wz:5.2f}) | {fwd:8.3f} {left:8.3f} {wzr:9.3f} | '
                  f'{ratio(fwd, vx)} {ratio(left, vy)} {ratio(wzr, wz)}', flush=True)
    finally:
        gt.stop()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
