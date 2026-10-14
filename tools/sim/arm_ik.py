#!/usr/bin/env python3
# 한글: 시뮬레이션 URDF로 팔 수치 IK(위치 + 그리퍼가 아래를 향하고 손가락 벌림 축이 몸 y축). 큐브 집기 자세 계산용.
#       결과는 joint1~5(rad). 실기 서보 오프셋·백래시는 반영 안 됨 — 시뮬레이션 전용.
"""Numeric arm IK on the simulation URDF (position + gripper pointing down, opening axis along base y).

Usage:
  xacro src/jetrover_gazebo/urdf/jetrover_sim.urdf.xacro sim_mode:=true controllers_file:=x > /tmp/sim.urdf
  python3 tools/sim/arm_ik.py /tmp/sim.urdf X Y [Z ...]     # target of end_effector_link in base_footprint (m)
Prints joint1..joint5 per Z. Example (green cube 0.25 m ahead): arm_ik.py /tmp/sim.urdf 0.25 0 0.12 0.06 0.025
"""
import sys
import xml.etree.ElementTree as ET

import numpy as np
from scipy.optimize import minimize


def rpy(r, p, y):
    cr, sr, cp, sp, cy, sy = np.cos(r), np.sin(r), np.cos(p), np.sin(p), np.cos(y), np.sin(y)
    return np.array([[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
                     [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
                     [-sp, cp * sr, cp * cr]])


def axang(a, t):
    a = a / np.linalg.norm(a)
    k = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(t) * k + (1 - np.cos(t)) * k @ k


def load_chain(urdf, tip='end_effector_link'):
    joints = {j.find('child').get('link'): j for j in ET.parse(urdf).getroot().findall('joint')}
    chain, link = [], tip
    while link in joints:
        chain.append(joints[link])
        link = joints[link].find('parent').get('link')
    return chain[::-1]


def fk(chain, q):
    t, i = np.eye(4), 0
    for j in chain:
        o = j.find('origin')
        m = np.eye(4)
        m[:3, :3] = rpy(*map(float, (o.get('rpy') or '0 0 0').split()))
        m[:3, 3] = list(map(float, (o.get('xyz') or '0 0 0').split()))
        t = t @ m
        if j.get('type') == 'revolute':
            r = np.eye(4)
            r[:3, :3] = axang(np.array(list(map(float, j.find('axis').get('xyz').split()))), q[i])
            t = t @ r
            i += 1
    return t


def solve(chain, target, q0, lim=2.09):
    # 위치 오차 + link5 z축이 아래(−z) + 그리퍼 y축이 몸 y축 / position, approach down, opening along base y
    def cost(q):
        t = fk(chain, q)
        yaw_axis = np.array([-np.sin(np.arctan2(target[1], target[0])), np.cos(np.arctan2(target[1], target[0]))])
        return (100 * np.sum((t[:3, 3] - target) ** 2) + 0.05 * (1 + t[2, 2]) ** 2
                + 0.05 * (1 - abs(t[:2, 1] @ yaw_axis)) ** 2)
    best = None
    for k in range(20):
        start = q0 if k == 0 else np.random.default_rng(k).uniform(-1.5, 1.5, 5)
        r = minimize(cost, start, method='L-BFGS-B', bounds=[(-lim, lim)] * 5)
        if best is None or r.fun < best.fun:
            best = r
    t = fk(chain, best.x)
    return best.x, np.linalg.norm(t[:3, 3] - target), np.degrees(np.arccos(np.clip(-t[2, 2], -1, 1)))


def main():
    urdf, x, y = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    zs = [float(z) for z in sys.argv[4:]] or [0.12, 0.06, 0.025]
    chain = load_chain(urdf)
    q = np.array([0.0, -0.66, 1.66, 1.45, 0.0])
    for z in zs:
        q, err, tilt = solve(chain, np.array([x, y, z]), q)
        print(f'z {z:.3f}: joints {np.round(q, 3).tolist()}  pos err {err * 1000:.1f} mm  tilt {tilt:.1f} deg')


if __name__ == '__main__':
    main()
