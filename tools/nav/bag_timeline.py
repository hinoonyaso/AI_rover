#!/usr/bin/env python3
# 한글: 주행 시험 bag(straight_trial.py --bag)을 시간순으로 요약한다 — collision_monitor 동작, 전역 경로 변화(우회 폭),
#       AMCL 위치/방향, 2초 단위 cmd_vel_nav 평균과 vy 부호 전환 횟수. 시간 초과/정체 회차의 원인 찾기용(읽기 전용).
"""Summarize a Nav2 trial bag on a timeline (read-only).

Usage: python3 tools/nav/bag_timeline.py bags/wobble/<run> [--bin 2.0]
Prints:
  collision_monitor_state changes (action 0 none, 1 stop, 2 slowdown)
  every /plan: start -> end, length, max lateral deviation from the start-end line (detour width)
  /amcl_pose (x, y, yaw)
  per bin: mean vx/vy/wz of /cmd_vel_nav, vy sign flips (dithering), zero /cmd_vel count
A long run of near-zero cmd_vel_nav with many vy flips while the plan is unchanged = the controller
sees no good sample (blocked in the local costmap), not a planner problem.
"""
import argparse
import collections
import math

from rclpy.serialization import deserialize_message
import rosbag2_py
from rosidl_runtime_py.utilities import get_message

WANT = {'/cmd_vel_nav', '/cmd_vel', '/collision_monitor_state', '/plan', '/amcl_pose'}


def yaw_deg(q):
    return math.degrees(math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z)))


def read(path):
    r = rosbag2_py.SequentialReader()
    r.open(rosbag2_py.StorageOptions(uri=path, storage_id='mcap'),
           rosbag2_py.ConverterOptions('', ''))
    types = {t.name: t.type for t in r.get_all_topics_and_types()}
    data, t0 = {k: [] for k in WANT}, None
    while r.has_next():
        topic, raw, t = r.read_next()
        if topic not in WANT:
            continue
        t0 = t0 or t
        data[topic].append(((t - t0) / 1e9, deserialize_message(raw, get_message(types[topic]))))
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('bag')
    ap.add_argument('--bin', type=float, default=2.0, help='seconds per cmd_vel row')
    args = ap.parse_args()
    data = read(args.bag)

    print('collision_monitor_state (0 none, 1 stop, 2 slowdown):')
    for t, m in data['/collision_monitor_state']:
        print(f'  {t:6.1f} s action={m.action_type} {m.polygon_name}')

    print('plans: start -> end, length, max lateral deviation from the start-end line')
    for t, m in data['/plan']:
        ps = [p.pose.position for p in m.poses]
        if not ps:
            print(f'  {t:6.1f} s empty')
            continue
        a, b = ps[0], ps[-1]
        chord = math.hypot(b.x - a.x, b.y - a.y) or 1.0
        dev = max(abs((p.x - a.x) * (b.y - a.y) - (p.y - a.y) * (b.x - a.x)) / chord for p in ps)
        length = sum(math.hypot(q.x - p.x, q.y - p.y) for p, q in zip(ps, ps[1:]))
        print(f'  {t:6.1f} s ({a.x:+.2f},{a.y:+.2f}) -> ({b.x:+.2f},{b.y:+.2f}) '
              f'len {length:.2f} m, detour {dev:.2f} m')

    print('amcl_pose:')
    for t, m in data['/amcl_pose']:
        p = m.pose.pose
        print(f'  {t:6.1f} s ({p.position.x:+.2f},{p.position.y:+.2f}) '
              f'yaw {yaw_deg(p.orientation):+6.1f}')

    print(f'cmd_vel_nav per {args.bin:g} s: mean vx vy wz, vy sign flips, '
          'zero /cmd_vel (after monitor)')
    nav, out = collections.defaultdict(list), collections.defaultdict(list)
    for t, m in data['/cmd_vel_nav']:
        nav[int(t // args.bin)].append((m.linear.x, m.linear.y, m.angular.z))
    for t, m in data['/cmd_vel']:
        out[int(t // args.bin)].append(abs(m.linear.x) + abs(m.linear.y) + abs(m.angular.z) < 1e-4)
    for k in sorted(set(nav) | set(out)):
        v = nav.get(k, [])
        n = len(v) or 1
        flips = sum(1 for p, q in zip(v, v[1:]) if p[1] * q[1] < 0)
        print(f'  {k * args.bin:5.0f}-{(k + 1) * args.bin:3.0f} s n={len(v):3d} '
              f'vx {sum(x for x, _, _ in v) / n:+.3f} vy {sum(y for _, y, _ in v) / n:+.3f} '
              f'wz {sum(z for _, _, z in v) / n:+.3f} flips {flips:2d} '
              f'zero {sum(out.get(k, []))}/{len(out.get(k, []))}')


if __name__ == '__main__':
    main()
