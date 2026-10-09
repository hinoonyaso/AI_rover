#!/usr/bin/env python3
# 한글: bags/<tag>/trial_*/ (rosbag2 + meta.json)에서 Nav2 baseline 지표를 계산해 CSV/Markdown으로 저장한다.
"""Compute Nav2 baseline metrics from recorded trials.

Usage: python3 analyze.py bags/baseline_openloop [--out docs/benchmarks/navigation/baseline_openloop]
Needs a ROS 2 environment (rosbag2_py, rclpy) -- the metric math itself is in metrics.py (unit-tested).

Per trial dir: a rosbag2 recording of /amcl_pose, /plan, /cmd_vel and meta.json (see record_trial.sh):
  {"scenario": "A", "trial": 1, "goal": {"x":..,"y":..,"yaw_deg":..},
   "outcome": "success|fail|abort", "collision": false, "recoveries": 0,
   "measured_final": {"x":..,"y":..,"yaw_deg":..}   # optional tape/protractor ground truth
  }
Success/collision/recoveries are operator-judged (cannot be inferred from the bag).
Goal error uses `measured_final` when present: AMCL's own pose is not independent ground truth.
Otherwise the final pose = last map->odom * last odom->base_footprint from /tf (ground_truth 'tf'), and
only without /tf the last /amcl_pose ('amcl'). 2026-10-10: on real bags the last /amcl_pose lagged the
stop pose by 3-8 cm (AMCL publishes only after update_min_d/a of motion), so it biased the goal error.
"""
import argparse
import csv
import glob
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics as m  # noqa: E402

TOPICS = {'/amcl_pose': 'geometry_msgs/msg/PoseWithCovarianceStamped',
          '/plan': 'nav_msgs/msg/Path',
          '/cmd_vel': 'geometry_msgs/msg/Twist',
          '/tf': 'tf2_msgs/msg/TFMessage'}


def read_bag(path):
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message

    reader = rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=path, storage_id=''),
                rosbag2_py.ConverterOptions(input_serialization_format='',
                                            output_serialization_format=''))
    types = {t.name: t.type for t in reader.get_all_topics_and_types()}
    data = {k: [] for k in TOPICS}
    while reader.has_next():
        topic, raw, stamp_ns = reader.read_next()
        if topic in data and topic in types:
            data[topic].append((stamp_ns * 1e-9, deserialize_message(raw, get_message(types[topic]))))
    return data


def final_pose_from_tf(tf_msgs, base='base_footprint'):
    """Last map->odom * last odom->base from /tf messages, or None. 한글: /tf로 최종 자세."""
    last = {}
    for _, msg in tf_msgs:
        for tr in msg.transforms:
            q = tr.transform.rotation
            last[(tr.header.frame_id, tr.child_frame_id)] = (
                tr.transform.translation.x, tr.transform.translation.y, m.yaw_from_quat(q.z, q.w))
    mo, ob = last.get(('map', 'odom')), last.get(('odom', base))
    if mo is None or ob is None:
        return None
    x, y, yaw = m.compose2d(mo, ob)
    return (x, y), yaw


def analyze_trial(path):
    with open(os.path.join(path, 'meta.json'), encoding='utf-8') as f:
        meta = json.load(f)
    data = read_bag(path)
    goal = meta['goal']
    goal_xy, goal_yaw = (goal['x'], goal['y']), math.radians(goal['yaw_deg'])

    # 한글: 이동 구간(cmd_vel이 0이 아닌 첫~마지막 시각)만 잘라서 쓴다.
    cmd = data['/cmd_vel']
    speeds = [math.hypot(msg.linear.x, msg.linear.y) + abs(msg.angular.z) for _, msg in cmd]
    interval = m.moving_interval([t for t, _ in cmd], speeds)
    t0, t1 = interval if interval else (None, None)

    poses = [(t, (msg.pose.pose.position.x, msg.pose.pose.position.y),
              m.yaw_from_quat(msg.pose.pose.orientation.z, msg.pose.pose.orientation.w))
             for t, msg in data['/amcl_pose']]
    moving = [p for p in poses if t0 is not None and t0 <= p[0] <= t1]
    track = [p[1] for p in moving]

    # 한글: 계획 경로는 이동 시작 직후 처음 받은 /plan을 기준선으로 쓴다(재계획 전 원래 의도).
    plan = next((msg for t, msg in data['/plan'] if t0 is None or t >= t0), None)
    plan_xy = [(ps.pose.position.x, ps.pose.position.y) for ps in plan.poses] if plan else []
    cte = m.cross_track_errors(plan_xy, track)

    final = meta.get('measured_final')
    from_tf = final_pose_from_tf(data['/tf'])
    source = 'measured' if final else ('tf' if from_tf else 'amcl')
    if final:
        f_xy, f_yaw = (final['x'], final['y']), math.radians(final['yaw_deg'])
    elif from_tf:
        f_xy, f_yaw = from_tf
    elif poses:
        f_xy, f_yaw = poses[-1][1], poses[-1][2]
    else:
        f_xy = f_yaw = None
    pos_err = yaw_err = None
    if f_xy is not None:
        pe, ye = m.goal_errors(f_xy, f_yaw, goal_xy, goal_yaw)
        pos_err, yaw_err = pe * 100.0, math.degrees(ye)

    return {
        'scenario': meta['scenario'], 'trial': meta['trial'],
        'success': meta['outcome'] == 'success', 'collision': bool(meta.get('collision')),
        'pos_err_cm': pos_err, 'yaw_err_deg': yaw_err,
        'cte_rms_cm': m.rms(cte) * 100.0 if cte else None,
        'time_s': (t1 - t0) if interval else None,
        'path_len_m': m.path_length(track) if len(track) > 1 else None,
        'recoveries': meta.get('recoveries'),
        'ground_truth': source,
    }


def fmt(stat, digits=1):
    return '-' if not stat else '%.*f ± %.*f (max %.*f)' % (
        digits, stat['mean'], digits, stat['std'], digits, stat['max'])


def write_markdown(path, tag, rows):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('# Nav2 baseline: %s\n\n| 시나리오 | n | Success | Collision | Goal pos [cm] | Goal yaw [deg] '
                '| CTE RMS [cm] | Time [s] | Recovery |\n|---|---|---|---|---|---|---|---|---|\n' % tag)
        for sc in sorted({r['scenario'] for r in rows}) + ['ALL']:
            sel = rows if sc == 'ALL' else [r for r in rows if r['scenario'] == sc]
            s = m.summarize(sel)
            f.write('| %s | %d | %.0f%% | %.0f%% | %s | %s | %s | %s | %s |\n' % (
                sc, s['n'], 100 * s['success_rate'], 100 * s['collision_rate'],
                fmt(s['pos_err_cm']), fmt(s['yaw_err_deg']), fmt(s['cte_rms_cm']),
                fmt(s['time_s']), fmt(s['recoveries'])))
        f.write('\n값은 mean ± std (max). Goal 오차는 `measured_final`(줄자 실측)이 있으면 그것을, '
                '없으면 bag의 /tf(map→odom→base_footprint), 그것도 없으면 마지막 AMCL pose를 쓴다 '
                '(`ground_truth` 열 참고, CSV).\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bag_root')
    ap.add_argument('--out', default=None, help='output prefix (writes .csv and .md)')
    args = ap.parse_args()
    rows = [analyze_trial(d) for d in sorted(glob.glob(os.path.join(args.bag_root, 'trial_*')))]
    if not rows:
        sys.exit('no trial_* directories under %s' % args.bag_root)
    out = args.out or os.path.join('docs/benchmarks/navigation', os.path.basename(args.bag_root.rstrip('/')))
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    with open(out + '.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    write_markdown(out + '.md', os.path.basename(out), rows)
    print('wrote %s.csv and %s.md (%d trials)' % (out, out, len(rows)))


if __name__ == '__main__':
    main()
