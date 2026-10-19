#!/usr/bin/env python3
# 한글: DWB 후보 궤적 평가(/evaluation)를 읽어, 어느 평가자(critic)가 어떤 후보를 죽였는지 요약한다(host).
#       회피 시험이 멈췄을 때 이동 후보가 왜 전부 무효인지 보려는 진단. 목표를 보내고 --at 초 뒤부터 --count 개 메시지를 읽는다.
"""Summarize DWB's candidate trajectory scoring at given times (host, ROS_DOMAIN_ID=31, Nav2 running).

  python3 tools/sim/dwb_eval_probe.py --scenario S4 --leg AB --at 8 20 --count 3
For each captured /evaluation message: the number of candidates, how many are valid (no negative critic score), which critic
killed how many, and the best candidates (total score, velocity, per-critic weighted scores). Translating candidates are
those with |v_xy| >= 0.04.
"""
import argparse
import math
import os
import sys

from dwb_msgs.msg import LocalPlanEvaluation
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
import rclpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import avoid_trials as T  # noqa: E402


def describe(msg, top=4):
    tw = msg.twists
    killers, valid = {}, []
    for t in tw:
        dead = [c.name for c in t.scores if c.raw_score < 0]
        for n in dead:
            killers[n] = killers.get(n, 0) + 1
        if not dead:
            valid.append(t)
    n_trans = sum(1 for t in tw if math.hypot(t.traj.velocity.x, t.traj.velocity.y) >= 0.04)
    v_trans = [t for t in valid if math.hypot(t.traj.velocity.x, t.traj.velocity.y) >= 0.04]
    print(f'  {len(tw)} candidates ({n_trans} translating >= 0.04 m/s); valid {len(valid)} (translating {len(v_trans)}); '
          f'killed by: {killers}', flush=True)
    best = sorted(valid, key=lambda t: t.total)[:top]
    for t in best:
        parts = ' '.join(f'{c.name[:6]}={c.raw_score * c.scale:.1f}' for c in t.scores)
        print(f'    total {t.total:7.1f} v=({t.traj.velocity.x:5.2f}, {t.traj.velocity.y:5.2f}, {t.traj.velocity.theta:5.2f}) {parts}',
              flush=True)
    if v_trans:
        bt = min(v_trans, key=lambda t: t.total)
        parts = ' '.join(f'{c.name[:6]}={c.raw_score * c.scale:.1f}' for c in bt.scores)
        print(f'    best TRANSLATING: total {bt.total:7.1f} v=({bt.traj.velocity.x:5.2f}, {bt.traj.velocity.y:5.2f}, '
              f'{bt.traj.velocity.theta:5.2f}) {parts}', flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--scenario', default='S4', choices=sorted(T.SCENARIOS))
    ap.add_argument('--leg', default='AB')
    ap.add_argument('--at', type=float, nargs='+', default=[8.0])
    ap.add_argument('--count', type=int, default=2)
    args = ap.parse_args()
    rclpy.init()
    node, gt = T.Runner(), T.GroundTruth()
    got = []
    node.create_subscription(LocalPlanEvaluation, '/evaluation', lambda m: got.append(m), 1)
    try:
        node.spin(3.0)
        start, goal_xy = T.SCENARIOS[args.scenario]['legs'][args.leg]
        T.setup_leg(node, gt, args.scenario, start, T.SCENARIOS[args.scenario]['box'])
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.pose.position.x, goal.pose.pose.position.y = goal_xy
        yaw = math.atan2(goal_xy[1] - start[1], goal_xy[0] - start[0])
        goal.pose.pose.orientation.z, goal.pose.pose.orientation.w = math.sin(yaw / 2), math.cos(yaw / 2)
        node.client.wait_for_server(timeout_sec=10.0)
        hf = node.client.send_goal_async(goal)
        rclpy.spin_until_future_complete(node, hf)
        t0 = node.now()
        for at in sorted(args.at):
            while node.now() - t0 < at:
                node.spin(0.1)
            got.clear()
            while len(got) < args.count and node.now() - t0 < at + 8.0:
                node.spin(0.1)
            g = gt.latest
            print(f't={at:.0f}s robot ({g[1]:.2f}, {g[2]:.2f}, {math.degrees(g[3]):.0f} deg), {len(got)} evaluation messages', flush=True)
            for m in got[:args.count]:
                describe(m)
        hf.result().cancel_goal_async()
        node.spin(1.0)
    finally:
        gt.stop()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
