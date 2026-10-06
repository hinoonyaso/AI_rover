# 한글: 브리지의 순수 계산 함수 시험(ROS 불필요). / Tests for the bridge's pure helpers (no ROS needed).
import importlib.util
import math
import os
import sys
import types
import unittest

# rclpy 등이 없는 환경에서도 로직만 시험하도록 필요한 모듈을 가짜로 채운다.
for name in ('rclpy', 'rclpy.action', 'rclpy.callback_groups', 'rclpy.executors', 'rclpy.node',
             'control_msgs', 'control_msgs.action', 'sensor_msgs', 'sensor_msgs.msg',
             'trajectory_msgs', 'trajectory_msgs.msg'):
    if name not in sys.modules:
        sys.modules[name] = types.ModuleType(name)
sys.modules['control_msgs.action'].FollowJointTrajectory = type(
    'F', (), {'Result': type('R', (), {})})
for n in ('ActionServer', 'CancelResponse', 'GoalResponse'):
    setattr(sys.modules['rclpy.action'], n, object)
sys.modules['rclpy.callback_groups'].ReentrantCallbackGroup = object
sys.modules['rclpy.executors'].MultiThreadedExecutor = object
sys.modules['rclpy.node'].Node = object
sys.modules['sensor_msgs.msg'].JointState = object
sys.modules['trajectory_msgs.msg'].JointTrajectory = object
sys.modules['trajectory_msgs.msg'].JointTrajectoryPoint = object

path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'trajectory_bridge.py')
spec = importlib.util.spec_from_file_location('trajectory_bridge', path)
tb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tb)


class BridgeLogic(unittest.TestCase):
    def test_interpolate_midpoint_and_clamp(self):
        t = [0.0, 1.0]
        p = [[0.0, 1.0], [1.0, 0.0]]
        self.assertEqual(tb.interpolate(t, p, 0.5), [0.5, 0.5])
        self.assertEqual(tb.interpolate(t, p, -1.0), [0.0, 1.0])
        self.assertEqual(tb.interpolate(t, p, 9.0), [1.0, 0.0])

    def test_resample_ends_exactly_at_last_point(self):
        s = tb.resample([0.0, 1.0], [[0.0], [0.5]], 0.2)
        self.assertEqual([round(x[0], 3) for x in s], [0.2, 0.4, 0.6, 0.8, 1.0])
        self.assertEqual(s[-1][1], [0.5])

    def test_resample_short_trajectory_single_sample(self):
        s = tb.resample([0.0, 0.1], [[0.0], [0.05]], 0.2)
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0][1], [0.05])

    def test_validate_accepts_gentle_plan(self):
        s = tb.resample([0.0, 2.0], [[0.0], [0.4]], 0.2)
        self.assertEqual(tb.validate_plan([0.0], s, [(-1.6, 1.6)], 0.2), '')

    def test_validate_rejects_big_step(self):
        s = tb.resample([0.0, 0.2], [[0.0], [0.5]], 0.2)
        self.assertIn('step', tb.validate_plan([0.0], s, [(-1.6, 1.6)], 0.2))

    def test_validate_rejects_start_jump(self):
        # 시작 자세가 첫 점과 멀면 첫 스텝이 커서 거부돼야 한다.
        self.assertIn('step', tb.validate_plan([0.0], [(0.2, [0.5])], [(-1.6, 1.6)], 0.2))

    def test_validate_rejects_out_of_limits_and_nan(self):
        self.assertIn('outside', tb.validate_plan([1.5], [(0.2, [1.7])], [(-1.676, 1.676)], 0.3))
        self.assertIn('non-finite', tb.validate_plan([0.0], [(0.2, [math.nan])], [(-1.6, 1.6)], 0.3))


if __name__ == '__main__':
    unittest.main()
