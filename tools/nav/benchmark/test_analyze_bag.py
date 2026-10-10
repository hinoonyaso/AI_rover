#!/usr/bin/env python3
# 한글: 가짜 rosbag(synthetic bag)으로 analyze.py를 검증하는 통합 시험. ROS 환경(rosbag2_py, rclpy)이 필요하다.
"""Integration test: build a tiny synthetic rosbag with known geometry and check analyze.py's numbers.

Needs a sourced ROS 2 environment (rosbag2_py). Run: python3 tools/nav/benchmark/test_analyze_bag.py
No robot needed. Catches "the robot drove fine but the analysis script broke on the bag API" before a field day.

Scenario (all times in seconds from T0): /cmd_vel is zero at 0, vx=0.1 at 1..5, zero at 6 -> moving interval
[1, 5] = 4.0 s. /amcl_pose moves x 0 -> 2 m during [1, 5] at y = 0.02 (so CTE vs the straight y=0 plan is
2 cm); poses outside the interval are at y = 0.5 and must be ignored. /plan is the straight line y = 0.
"""
import json
import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import analyze  # noqa: E402
from geometry_msgs.msg import Pose, PoseStamped, PoseWithCovarianceStamped, Twist  # noqa: E402
from nav_msgs.msg import Path  # noqa: E402
from geometry_msgs.msg import TransformStamped  # noqa: E402
from rclpy.serialization import serialize_message  # noqa: E402
from tf2_msgs.msg import TFMessage  # noqa: E402
import rosbag2_py  # noqa: E402

T0 = 100.0


def ns(t):
    return int((T0 + t) * 1e9)


def amcl(x, y, yaw=0.0):
    m = PoseWithCovarianceStamped()
    m.pose.pose.position.x = x
    m.pose.pose.position.y = y
    m.pose.pose.orientation.z = math.sin(yaw / 2.0)
    m.pose.pose.orientation.w = math.cos(yaw / 2.0)
    return m


def twist(vx):
    m = Twist()
    m.linear.x = vx
    return m


def straight_plan():
    p = Path()
    for x in (0.0, 0.5, 1.0, 1.5, 2.0):
        ps = PoseStamped()
        ps.pose = Pose()
        ps.pose.position.x = x
        p.poses.append(ps)
    return p


def make_topic(name, type_name):
    try:
        return rosbag2_py.TopicMetadata(name=name, type=type_name, serialization_format='cdr')
    except TypeError:  # 한글: 구버전 API는 id 인자가 필요하다.
        return rosbag2_py.TopicMetadata(id=0, name=name, type=type_name, serialization_format='cdr')


def tf_msg(parent, child, x, y, yaw):
    tr = TransformStamped()
    tr.header.frame_id, tr.child_frame_id = parent, child
    tr.transform.translation.x, tr.transform.translation.y = x, y
    tr.transform.rotation.z, tr.transform.rotation.w = math.sin(yaw / 2.0), math.cos(yaw / 2.0)
    return TFMessage(transforms=[tr])


def write_bag(path, with_tf=False):
    writer = rosbag2_py.SequentialWriter()
    writer.open(rosbag2_py.StorageOptions(uri=path, storage_id='sqlite3'),
                rosbag2_py.ConverterOptions(input_serialization_format='cdr',
                                            output_serialization_format='cdr'))
    writer.create_topic(make_topic('/amcl_pose', 'geometry_msgs/msg/PoseWithCovarianceStamped'))
    writer.create_topic(make_topic('/plan', 'nav_msgs/msg/Path'))
    writer.create_topic(make_topic('/cmd_vel', 'geometry_msgs/msg/Twist'))

    for t, vx in ((0.0, 0.0), (1.0, 0.1), (2.0, 0.1), (3.0, 0.1), (4.0, 0.1), (5.0, 0.1), (6.0, 0.0)):
        writer.write('/cmd_vel', serialize_message(twist(vx)), ns(t))
    writer.write('/plan', serialize_message(straight_plan()), ns(1.0))
    for t in (0.0, 0.5):  # 이동 전: 제외돼야 한다
        writer.write('/amcl_pose', serialize_message(amcl(0.0, 0.5)), ns(t))
    for i in range(9):  # 이동 구간 t=1..5, x 0..2
        t = 1.0 + 0.5 * i
        writer.write('/amcl_pose', serialize_message(amcl(0.5 * (t - 1.0), 0.02)), ns(t))
    for t in (5.5, 6.0):  # 이동 후: 최종 pose는 (2.0, 0.02)
        writer.write('/amcl_pose', serialize_message(amcl(2.0, 0.02)), ns(t))
    if with_tf:  # 한글: 최종 자세 = map->odom (0.1, 0) * odom->base (1.95, 0.03, 0.1 rad) = (2.05, 0.03)
        writer.create_topic(make_topic('/tf', 'tf2_msgs/msg/TFMessage'))
        writer.write('/tf', serialize_message(tf_msg('odom', 'base_footprint', 1.0, 0.0, 0.0)), ns(3.0))
        writer.write('/tf', serialize_message(tf_msg('map', 'odom', 0.1, 0.0, 0.0)), ns(5.0))
        writer.write('/tf', serialize_message(tf_msg('odom', 'base_footprint', 1.95, 0.03, 0.1)),
                     ns(6.0))
    del writer  # flush + close


def write_meta(path, measured_final):
    meta = {'scenario': 'A', 'trial': 1, 'goal': {'x': 2.0, 'y': 0.0, 'yaw_deg': 0.0},
            'outcome': 'success', 'collision': False, 'recoveries': 1}
    if measured_final:
        meta['measured_final'] = {'x': 2.03, 'y': 0.04, 'yaw_deg': 5.0}
    with open(os.path.join(path, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f)


class AnalyzeBagTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def trial(self, name, measured_final, with_tf=False):
        path = os.path.join(self.root, name)
        write_bag(path, with_tf)
        write_meta(path, measured_final)
        return analyze.analyze_trial(path)

    def test_measured_final_is_ground_truth(self):
        r = self.trial('trial_A01', True)
        self.assertEqual(r['ground_truth'], 'measured')
        self.assertAlmostEqual(r['pos_err_cm'], 5.0, places=6)    # hypot(3, 4) cm
        self.assertAlmostEqual(r['yaw_err_deg'], 5.0, places=6)
        self.assertAlmostEqual(r['cte_rms_cm'], 2.0, places=3)    # 이동 전 y=0.5 포즈는 제외됨
        self.assertAlmostEqual(r['time_s'], 4.0, places=6)
        self.assertAlmostEqual(r['path_len_m'], 2.0, places=6)
        self.assertTrue(r['success'])
        self.assertFalse(r['collision'])
        self.assertEqual(r['recoveries'], 1)

    def test_falls_back_to_amcl_pose(self):
        r = self.trial('trial_A02', False)
        self.assertEqual(r['ground_truth'], 'amcl')
        self.assertAlmostEqual(r['pos_err_cm'], 2.0, places=6)    # 마지막 pose (2.0, 0.02) vs goal (2.0, 0)
        self.assertAlmostEqual(r['yaw_err_deg'], 0.0, places=6)

    def test_final_pose_from_tf_beats_amcl(self):
        r = self.trial('trial_A03', False, with_tf=True)
        self.assertEqual(r['ground_truth'], 'tf')
        self.assertAlmostEqual(r['pos_err_cm'], math.hypot(5.0, 3.0), places=4)
        self.assertAlmostEqual(r['yaw_err_deg'], math.degrees(0.1), places=4)

    def test_markdown_and_csv_outputs(self):
        rows = [self.trial('trial_A01', True), self.trial('trial_A02', False)]
        out = os.path.join(self.root, 'summary')
        analyze.write_markdown(out + '.md', 'synthetic', rows)
        with open(out + '.md', encoding='utf-8') as f:
            text = f.read()
        self.assertIn('| A | 2 | 100% | 0% |', text)
        self.assertIn('ALL', text)


if __name__ == '__main__':
    unittest.main()
