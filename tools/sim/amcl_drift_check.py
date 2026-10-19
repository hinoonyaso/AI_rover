#!/usr/bin/env python3
# 한글: Gazebo에서 AMCL 추정이 정답(Gazebo)과 얼마나 어긋나는지 잰다. 시작 자세를 정답으로 주고, 로봇을 가만히 두거나
#       제자리 회전·직진을 시켜 시간에 따라 오차를 출력한다. 주행 시험 실패가 위치 추정 탓인지 가르는 진단. 읽기+소폭 이동.
"""AMCL error vs Gazebo ground truth over time (host, ROS_DOMAIN_ID=31, Nav2 with auto_localize:=false running).

  python3 tools/sim/amcl_drift_check.py [--start X Y YAW_DEG] [--stand 40] [--spin] [--drive]
Phases: stand still, optionally rotate in place (wz 0.3 rad/s for 8 s), optionally drive forward 0.4 m (vx 0.08).
Prints every 4 s: ground truth pose, AMCL pose, position and yaw error.
"""
import argparse
import math
import os
import sys
import time

from geometry_msgs.msg import Twist
import rclpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import avoid_trials as T  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--start', type=float, nargs=3, default=[1.02, 0.37, 83.0])
    ap.add_argument('--stand', type=float, default=40.0)
    ap.add_argument('--spin', action='store_true')
    ap.add_argument('--drive', action='store_true')
    args = ap.parse_args()
    rclpy.init()
    node, gt = T.Runner(), T.GroundTruth()
    pub = node.create_publisher(Twist, '/cmd_vel_nav', 10)
    try:
        node.spin(3.0)
        err0 = T.setup_leg(node, gt, 'S2', tuple(args.start), T.SCENARIOS['S2']['box'])
        print(f'start {args.start}, AMCL error after init {err0 * 100:.1f} cm', flush=True)

        def report(label):
            g, a = gt.latest, node.amcl_pose()
            if g and a:
                dyaw = math.degrees(T.M.wrap(a[2] - g[3]))
                print(f'{label:8s} GT ({g[1]:.3f}, {g[2]:.3f}, {math.degrees(g[3]):6.1f})  AMCL ({a[0]:.3f}, {a[1]:.3f}, '
                      f'{math.degrees(a[2]):6.1f})  err {math.hypot(a[0] - g[1], a[1] - g[2]) * 100:5.1f} cm  yaw {dyaw:+5.1f}',
                      flush=True)

        def phase(label, secs, twist=None):
            t0 = time.time()
            nxt = 0.0
            while time.time() - t0 < secs:
                if twist is not None:
                    m = Twist()
                    m.linear.x, m.angular.z = twist
                    pub.publish(m)
                node.spin(0.1)
                if time.time() - t0 >= nxt:
                    report(label)
                    nxt += 4.0
        phase('stand', args.stand)
        if args.spin:
            phase('spin', 8.0, (0.0, 0.3))
            phase('rest', 8.0)
        if args.drive:
            phase('drive', 5.0, (0.08, 0.0))
            phase('rest', 8.0)
    finally:
        gt.stop()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
