#!/usr/bin/env python3
# 한글: T6 L2 실기 시험 — 실제 서보로 arm/grasp Action을 반복 호출한다. 그리퍼가 닫힌다. base_node가 arm_command_enabled:=true로 떠 있어야 한다.
#       회차마다: (사용자가 큐브를 열린 그리퍼 사이에 놓는다) → goal → 결과 → HOLDING 유지 관찰(--dwell-s) → arm/release → 사용자가 큐브를 뺀다.
#       --swing: HOLDING 중 관절 1을 ±40 펄스(약 10°) 두 번 흔들고 그리퍼 위치가 유지되는지 본다.
"""L2 test of the contact grasp on the real robot. THE GRIPPER CLOSES (and joint 1 swings with --swing).

Usage: python3 tools/stm32_diagnostics/grasp_l2_run.py --trials 5 [--first-delay 30] [--gap 20] [--dwell-s 8] [--swing]
Per trial: wait for the cube (the first trial waits --first-delay s, later ones --gap s after the previous release),
send the arm/grasp goal, wait for the result, watch the gripper while HOLDING for --dwell-s s (a person may tug the
cube gently), optionally swing joint 1, call arm/release, wait for Idle. Prints one line per trial and a summary;
raw data goes to Log/grasp_l2_<time>.json. Never sends a gripper position command itself.
"""
import argparse
import json
import math
import os
import sys
import time

import rclpy
from rclpy.action import ActionClient
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from jetrover_interfaces.action import Grasp
from jetrover_interfaces.srv import Release

RPT = math.radians(240.0) / 1000.0     # rad per servo pulse


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--trials', type=int, default=5)
    ap.add_argument('--first-delay', type=float, default=30.0)
    ap.add_argument('--gap', type=float, default=20.0)
    ap.add_argument('--dwell-s', type=float, default=8.0)
    ap.add_argument('--swing', action='store_true')
    ap.add_argument('--max-temp', type=float, default=75.0, help='stop the series above this gripper temperature')
    args = ap.parse_args()

    rclpy.init()
    n = rclpy.create_node('grasp_l2')
    js, state, temps = {}, {'name': None}, []
    n.create_subscription(JointState, 'joint_states', lambda m: js.update(dict(zip(m.name, m.position))), 10)
    n.create_subscription(String, 'arm/grasp_state', lambda m: state.update(name=m.data), 10)
    cmd_pub = n.create_publisher(JointState, 'arm/command', 10)
    act = ActionClient(n, Grasp, 'arm/grasp')
    rel = n.create_client(Release, 'arm/release')

    def spin(sec):
        t0 = time.monotonic()
        while time.monotonic() - t0 < sec:
            rclpy.spin_once(n, timeout_sec=0.02)

    def wait(pred, limit):
        t0 = time.monotonic()
        while time.monotonic() - t0 < limit:
            rclpy.spin_once(n, timeout_sec=0.02)
            if pred():
                return True
        return False

    if not act.wait_for_server(timeout_sec=10) or not rel.wait_for_service(timeout_sec=10):
        sys.exit('arm/grasp or arm/release not available: base_node must run with arm_command_enabled:=true')
    spin(2.0)
    if state['name'] != 'Idle':
        sys.exit(f'grasp state is {state["name"]}, expected Idle')

    rows = []
    for k in range(1, args.trials + 1):
        wait_s = args.first_delay if k == 1 else args.gap
        print(f'trial {k}/{args.trials}: put the cube between the open jaws; closing starts in {wait_s:g} s', flush=True)
        spin(wait_s)
        g = Grasp.Goal()
        g.profile = 'cube3cm'
        fut = act.send_goal_async(g, feedback_callback=lambda fb: temps.append(fb.feedback.temperature_c))
        wait(fut.done, 5)
        gh = fut.result()
        if gh is None or not gh.accepted:
            print('  goal refused', flush=True)
            rows.append({'trial': k, 'accepted': False})
            continue
        t0 = time.monotonic()
        rf = gh.get_result_async()
        wait(rf.done, 90)
        took = time.monotonic() - t0
        res = rf.result().result if rf.done() else None
        row = {'trial': k, 'accepted': True, 'seconds': round(took, 1),
               'success': bool(res and res.success), 'reason': res.reason if res else 'no result',
               'contact': res.contact_position if res else None, 'final': res.final_position if res else None,
               'temp_c': max([t for t in temps if t > 0], default=None)}
        if row['success']:
            r0 = js.get('r_joint')
            lo = hi = r0
            t_end = time.monotonic() + args.dwell_s
            while time.monotonic() < t_end:
                rclpy.spin_once(n, timeout_sec=0.05)
                v = js.get('r_joint')
                if v is not None and lo is not None:
                    lo, hi = min(lo, v), max(hi, v)
            row['hold_spread_pulses'] = round((hi - lo) / RPT, 1) if lo is not None else None
            if args.swing and 'joint1' in js:
                j0 = js['joint1']
                r_before = js.get('r_joint')
                for d in (+40, -40, +40, -40, 0):
                    m = JointState()
                    m.name = ['joint1']
                    m.position = [j0 + d * RPT * (1 if d else 0)]
                    cmd_pub.publish(m)
                    spin(1.0)
                row['swing_gripper_change_pulses'] = (round((js.get('r_joint') - r_before) / RPT, 1)
                                                      if r_before is not None and js.get('r_joint') is not None else None)
            rr = rel.call_async(Release.Request())
            wait(rr.done, 5)
            row['release_ok'] = bool(rr.done() and rr.result().success)
            row['idle_after_release'] = wait(lambda: state['name'] == 'Idle', 15)
        else:
            row['idle_after_failure'] = wait(lambda: state['name'] == 'Idle', 15)
        rows.append(row)
        print('  ' + json.dumps(row, ensure_ascii=False), flush=True)
        if row.get('temp_c') and row['temp_c'] >= args.max_temp:
            print(f'  gripper at {row["temp_c"]:.0f} C: stopping the series', flush=True)
            break
    os.makedirs('Log', exist_ok=True)
    path = 'Log/grasp_l2_%s.json' % time.strftime('%Y%m%d_%H%M%S')
    json.dump(rows, open(path, 'w'), indent=1)
    ok = sum(1 for r in rows if r.get('success'))
    print(f'SUMMARY: {ok}/{len(rows)} grasps succeeded; raw: {path}')
    rclpy.shutdown()


if __name__ == '__main__':
    main()
