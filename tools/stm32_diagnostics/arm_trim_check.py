#!/usr/bin/env python3
# 한글: 팔 피드백 보정(arm_feedback_trim_*) 실기 확인. base_node가 arm_command_enabled:=true로 떠 있어야 한다.
#       관절을 현재 위치 기준 ±delta rad로 번갈아 움직이고, 멈춘 뒤 /joint_states에서 최종 펄스를 계산해 목표와 비교한다. 팔이 움직인다.
"""Measure the final pulse error of arm/command moves (gravity sag + dead band), with or without read-back trim.

Usage: python3 tools/stm32_diagnostics/arm_trim_check.py --joints joint2,joint3,joint4 [--delta 0.04] [--n 4]
"""
import argparse
import math
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

NAMES = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'r_joint']
RAD_PER_TICK = math.radians(240.0) / 1000.0
SIGN, CENTER = -1.0, 500.0


def pulse(rad):
    return CENTER + rad / (RAD_PER_TICK * SIGN)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--joints', default='joint3')
    ap.add_argument('--delta', type=float, default=0.04)
    ap.add_argument('--n', type=int, default=4)
    ap.add_argument('--wait', type=float, default=4.0)
    args = ap.parse_args()
    rclpy.init()
    node = Node('arm_trim_check')
    last = {}
    node.create_subscription(JointState, '/joint_states',
                             lambda m: last.update(dict(zip(m.name, m.position))), 10)
    pub = node.create_publisher(JointState, '/arm/command', 1)

    def spin(sec):
        t0 = time.time()
        while time.time() - t0 < sec:
            rclpy.spin_once(node, timeout_sec=0.05)

    spin(2.0)
    for name in args.joints.split(','):
        if name not in last:
            raise SystemExit(f'no /joint_states for {name}')
        base = last[name]
        errs = []
        for k in range(args.n):
            target = base + (args.delta if k % 2 == 0 else -args.delta)
            msg = JointState()
            msg.name, msg.position = [name], [target]
            pub.publish(msg)
            spin(args.wait)
            err = pulse(last[name]) - pulse(target)
            errs.append(round(err, 1))
            print(f'  {name} move {k + 1}: target {pulse(target):.1f} final {pulse(last[name]):.1f} err {err:+.1f}',
                  flush=True)
        msg = JointState()
        msg.name, msg.position = [name], [base]
        pub.publish(msg)
        spin(args.wait)
        print(f'{name}: errors {errs}  max|e| {max(map(abs, errs)):.1f}')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
