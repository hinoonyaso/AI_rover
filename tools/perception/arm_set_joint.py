#!/usr/bin/env python3
# 한글: 팔 관절 하나를 지정 각도로 옮긴다(base_node arm/command, 한 번에 0.35 rad 이하, 2초 이동). 팔이 실제로 움직인다 — 사람 입회.
"""Move one arm joint to a target angle via base_node arm/command (THE ARM MOVES).

Usage: python3 tools/perception/arm_set_joint.py joint4 1.45
Needs base_node with arm_command_enabled:=true. Moves in steps of <= 0.25 rad from the actual reading.
Prints the joint readings before and after.
"""
import sys
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


def main():
    name, target = sys.argv[1], float(sys.argv[2])
    rclpy.init()
    node = Node('arm_set_joint')
    js = {}
    node.create_subscription(JointState, '/joint_states',
                             lambda m: js.update(zip(m.name, m.position)), 10)
    pub = node.create_publisher(JointState, 'arm/command', 10)
    t0 = time.time()
    while name not in js and time.time() - t0 < 5:
        rclpy.spin_once(node, timeout_sec=0.1)
    if name not in js:
        sys.exit(f'no reading for {name}')
    # wait until base_node is matched, otherwise the first command is silently lost (2026-10-09)
    # 한글: base_node와 연결되기 전에 보내면 명령이 사라진다 → 연결 확인 후 전송
    while pub.get_subscription_count() == 0 and time.time() - t0 < 10:
        rclpy.spin_once(node, timeout_sec=0.1)
    if pub.get_subscription_count() == 0:
        sys.exit('base_node is not subscribed to arm/command (arm_command_enabled:=true?)')
    print('before:', {k: round(v, 3) for k, v in sorted(js.items()) if k.startswith('joint')})
    # Step from the ACTUAL reading each time (2026-10-09: stepping from the previous command made
    # the next step exceed arm_max_step_rad 0.35 while the servo was still moving -> rejected).
    # 한글: 매 단계 실제 관절값에서 0.25 rad 이하로. 직전 명령값 기준이면 서보가 덜 와서 0.35 제한에 걸렸다.
    for _ in range(20):
        cur = js[name]
        if abs(target - cur) <= 0.02:
            break
        nxt = cur + max(-0.25, min(0.25, target - cur))
        msg = JointState(name=[name], position=[nxt])
        msg.header.stamp = node.get_clock().now().to_msg()
        pub.publish(msg)
        t1 = time.time()
        while time.time() - t1 < 3.0:  # 2 s move + settle + joint_states refresh / 이동 2초 + 안정
            rclpy.spin_once(node, timeout_sec=0.1)
    t1 = time.time()
    while time.time() - t1 < 2.0:  # let the 5 Hz round-robin refresh all joints
        rclpy.spin_once(node, timeout_sec=0.1)
    print('after: ', {k: round(v, 3) for k, v in sorted(js.items()) if k.startswith('joint')})
    if abs(js[name] - target) > 0.05:
        print(f'WARNING: {name} is {js[name]:.3f}, target {target:.3f} -- command rejected or not reached')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
