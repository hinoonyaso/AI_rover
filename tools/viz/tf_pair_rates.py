#!/usr/bin/env python3
# 한글: /tf를 프레임 쌍(부모->자식)별로 N초 세어 Hz와 마지막 수신 후 경과 시간을 보여준다. 어떤 발행자가 멈췄는지 찾는 용도
#       (troubleshooting/033: 팔을 움직인 뒤 robot_state_publisher 관절 TF와 카메라 color TF가 끊김). 읽기만 한다.
"""Count /tf messages per (parent, child) pair for a few seconds (read-only).

Usage: python3 tools/viz/tf_pair_rates.py [--seconds 4] [--expect link3 link4 ...]
Prints Hz per pair and the joint_states stamp vs now (robot_state_publisher skips joint_states
stamped earlier than its last publish). --expect: child frames that must appear; exit 1 if missing.
"""
import argparse
import collections
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from sensor_msgs.msg import JointState
from tf2_msgs.msg import TFMessage


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--seconds', type=float, default=4.0)
    ap.add_argument('--expect', nargs='*', default=['link1', 'link4', 'depth_cam_color_frame'],
                    help='child frames that must be on /tf (dynamic)')
    args = ap.parse_args()
    rclpy.init()
    node = Node('tf_pair_rates')
    count, last = collections.Counter(), {}
    js = {}

    def on_tf(msg):
        now = time.time()
        for tr in msg.transforms:
            key = (tr.header.frame_id, tr.child_frame_id)
            count[key] += 1
            last[key] = now
    node.create_subscription(TFMessage, '/tf', on_tf, QoSProfile(depth=100))
    static = set()
    node.create_subscription(
        TFMessage, '/tf_static',
        lambda m: static.update((t.header.frame_id, t.child_frame_id) for t in m.transforms),
        QoSProfile(depth=100, durability=DurabilityPolicy.TRANSIENT_LOCAL))
    node.create_subscription(JointState, '/joint_states', lambda m: js.update(
        stamp=m.header.stamp.sec + m.header.stamp.nanosec * 1e-9,
        now=node.get_clock().now().nanoseconds * 1e-9), 10)
    t0 = time.time()
    while time.time() - t0 < args.seconds:
        rclpy.spin_once(node, timeout_sec=0.05)
    end = time.time()
    print(f'/tf pairs over {args.seconds:g} s (Hz, s since last):')
    for (p, c), n in sorted(count.items()):
        print(f'  {p:28s} -> {c:30s} {n / args.seconds:6.1f} Hz  {end - last[(p, c)]:5.2f} s')
    print(f'/tf_static pairs: {len(static)}')
    if js:
        print(f'joint_states stamp - now: {js["stamp"] - js["now"]:+.3f} s')
    else:
        print('no /joint_states')
    children = {c for _, c in count} | {c for _, c in static}
    missing = [c for c in args.expect if c not in children]
    if missing:
        print('MISSING on /tf: ' + ' '.join(missing))
    node.destroy_node()
    rclpy.shutdown()
    sys.exit(1 if missing else 0)


if __name__ == '__main__':
    main()
