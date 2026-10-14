#!/usr/bin/env python3
# 한글: (host, 시뮬레이션 실행 중) room_lap2_objects.sdf 팔 시험 자리(0.45, 0.75, 90°)에서 큐브 하나를 집어 들어 올린다.
#       IK(arm_ik.py)로 큐브 위 15/6 cm·큐브 높이 자세를 구해 50 Hz 보간 명령 → 열고 내려가 닫고(r_joint 0.3) 들어 올림.
#       판정: 들어 올린 뒤 큐브 z > 0.06 m(gz model). arm_hold.py는 미리 멈춰야 한다(sim_pick_check.sh가 함).
"""Pick-and-lift check for one cube in room_lap2_objects.sdf (robot spawned at the arm-test spot).

Usage: python3 tools/sim/sim_pick_check.py <sim.urdf> red|green|blue [--open 1.2] [--close 0.3]
Prints the cube pose before/after, r_joint command vs state when closed (contact = state lags command), RESULT line.
"""
import argparse
import os
import subprocess
import sys
import time

import numpy as np
import rclpy
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arm_ik import load_chain, solve  # noqa: E402

# 팔 시험 스폰(0.45, 0.75, 90°)에서 본 큐브 위치(base_footprint) / cube positions seen from the arm-test spawn
CUBES = {'red': ('object_1', 0.25, 0.08), 'green': ('object_2', 0.25, 0.0), 'blue': ('object_3', 0.25, -0.08)}
HOME = [0.0042, -0.6618, 1.6629, 1.45, 0.0168]


def model_pose(name):
    out = subprocess.run(['gz', 'model', '-m', name, '-p'], capture_output=True, text=True, timeout=10).stdout
    lines = out.splitlines()
    idx = [k for k, line in enumerate(lines) if 'XYZ' in line]
    return [float(v) for v in lines[idx[0] + 1].strip(' []').split()] if idx else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('urdf')
    ap.add_argument('cube', choices=sorted(CUBES))
    ap.add_argument('--open', type=float, default=1.2, help='r_joint open (gap about 6.4 cm)')
    ap.add_argument('--close', type=float, default=0.3, help='r_joint close target (3 cm gap is about 0.35)')
    args = ap.parse_args()
    name, bx, by = CUBES[args.cube]
    chain = load_chain(args.urdf)
    q = np.array(HOME)
    poses = {}
    for key, z in (('above', 0.15), ('pre', 0.06), ('grasp', 0.025)):
        q, err, tilt = solve(chain, np.array([bx, by, z]), q)
        poses[key] = q.tolist()
        print(f'IK {key} z {z}: {np.round(q, 3).tolist()} err {err * 1000:.1f} mm tilt {tilt:.1f} deg')

    rclpy.init()
    n = rclpy.create_node('sim_pick_check')
    js = {}
    n.create_subscription(JointState, '/joint_states', lambda m: js.update(dict(zip(m.name, m.position))), 10)
    pub = n.create_publisher(Float64MultiArray, '/arm_position_controller/commands', 10)
    cur = [HOME + [-0.0209]]

    def go(target, sec):
        a, b, t0 = np.array(cur[0]), np.array(target), time.monotonic()
        while True:
            s = min(1.0, (time.monotonic() - t0) / sec)
            pub.publish(Float64MultiArray(data=(a + (b - a) * s).tolist()))
            rclpy.spin_once(n, timeout_sec=0.02)
            if s >= 1.0:
                break
        cur[0] = list(b)

    def hold(sec):
        t0 = time.monotonic()
        while time.monotonic() - t0 < sec:
            pub.publish(Float64MultiArray(data=list(cur[0])))
            rclpy.spin_once(n, timeout_sec=0.02)

    hold(1.0)
    print('cube before', model_pose(name))
    go(HOME + [args.open], 1.5)
    go(poses['above'] + [args.open], 3.0)
    go(poses['pre'] + [args.open], 2.0)
    go(poses['grasp'] + [args.open], 2.0)
    hold(1.0)
    go(poses['grasp'] + [args.close], 3.0)
    hold(1.5)
    state = js.get('r_joint', float('nan'))
    print('closed: r_joint cmd %.2f state %.3f (contact if state > cmd)' % (args.close, state))
    go(poses['above'] + [args.close], 3.0)
    hold(3.0)
    c = model_pose(name)
    ok = c is not None and c[2] > 0.06
    print('cube after lift', c)
    print('RESULT:', args.cube, 'LIFTED' if ok else 'NOT LIFTED', 'z %.3f' % (c[2] if c else float('nan')))
    rclpy.shutdown()
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
