# 한글: 브리지의 순수 계산 함수 시험(ROS 불필요). / Tests for the bridge's pure helpers (no ROS needed).
import importlib.util
import math
import os
import sys
import threading
import types
import unittest

# rclpy 등이 없는 환경에서도 로직만 시험하도록 필요한 모듈을 가짜로 채운다.
for name in ('diagnostic_msgs', 'diagnostic_msgs.msg', 'rclpy', 'rclpy.action', 'rclpy.callback_groups',
             'rclpy.executors', 'rclpy.node',
             'control_msgs', 'control_msgs.action', 'sensor_msgs', 'sensor_msgs.msg',
             'trajectory_msgs', 'trajectory_msgs.msg'):
    if name not in sys.modules:
        sys.modules[name] = types.ModuleType(name)
sys.modules['control_msgs.action'].FollowJointTrajectory = type(
    'F', (), {'Result': type('R', (), {'SUCCESSFUL': 0, 'INVALID_GOAL': -1, 'PATH_TOLERANCE_VIOLATED': -4,
                                       'GOAL_TOLERANCE_VIOLATED': -5})})
sys.modules['diagnostic_msgs.msg'].DiagnosticArray = object
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


JOINTS = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5']
SERVO = {'joint1': 1, 'joint2': 2, 'joint3': 3, 'joint4': 4, 'joint5': 5, 'r_joint': 10}


def ages(now, **kw):
    """{servo: (age_s_at_report, reported_at)}; every servo fresh unless overridden by name (joint3=2.0 ...)."""
    out = {sid: (0.2, now - 0.5) for sid in SERVO.values()}
    for name, age in kw.items():
        out[SERVO[name]] = (age, now - 0.5)
    return out


class JointFreshness(unittest.TestCase):
    def check(self, a, now=100.0, joints=JOINTS, limit=1.5):
        return tb.joint_age_error(joints, SERVO, a, now, limit, 3.0)

    def test_all_fresh_is_ok(self):
        self.assertEqual(self.check(ages(100.0)), '')

    def test_one_silent_servo_is_rejected_even_if_the_others_are_fresh(self):
        err = self.check(ages(100.0, joint3=2.5))
        self.assertIn('joint3', err)
        self.assertIn('old', err)

    def test_other_joints_are_not_blamed_for_a_servo_the_trajectory_does_not_use(self):
        self.assertEqual(self.check(ages(100.0, r_joint=9.0), joints=JOINTS), '')
        self.assertIn('r_joint', self.check(ages(100.0, r_joint=9.0), joints=['r_joint']))

    def test_age_keeps_growing_between_stats_messages(self):
        a = {sid: (1.0, 99.0) for sid in SERVO.values()}         # reported 1 s ago with age 1.0 -> 2.0 s old now? no: 100-99
        self.assertIn('old', self.check(a, now=100.0))           # 1.0 + 1.0 = 2.0 s > 1.5
        self.assertEqual(self.check(a, now=99.2), '')            # 1.0 + 0.2 = 1.2 s

    def test_never_answered_stale_stats_and_missing_servo(self):
        self.assertIn('never answered', self.check(ages(100.0, joint2=-1.0)))
        self.assertIn('stale', self.check(ages(100.0), now=110.0))
        self.assertIn('no arm/servo_stats', self.check({}))
        partial = ages(100.0)
        del partial[4]
        self.assertIn('no servo stats for joint joint4', self.check(partial))

    def test_the_longest_gap_seen_at_20hz_is_tolerated(self):
        self.assertEqual(self.check(ages(100.0, joint1=0.9, joint5=0.9)), '')   # T1: max 0.9 s with 6 % silent servos


class BusyGateRace(unittest.TestCase):
    def test_only_one_of_many_simultaneous_goals_is_accepted(self):
        for _ in range(50):
            gate = tb.BusyGate()
            n, barrier, wins = 20, threading.Barrier(20), []

            def goal():
                barrier.wait()
                if gate.acquire():
                    wins.append(1)
            threads = [threading.Thread(target=goal) for _ in range(n)]
            [t.start() for t in threads]
            [t.join() for t in threads]
            self.assertEqual(len(wins), 1)

    def test_release_allows_the_next_goal_and_stale_tokens_are_taken_over(self):
        now = [0.0]
        gate = tb.BusyGate(max_hold_s=10.0, clock=lambda: now[0])
        self.assertTrue(gate.acquire())
        self.assertFalse(gate.acquire())
        gate.release()
        self.assertTrue(gate.acquire())
        now[0] = 5.0
        self.assertFalse(gate.acquire())
        now[0] = 11.0                     # leaked token (execute never ran)
        self.assertTrue(gate.acquire())
        self.assertEqual(gate.takeovers, 1)

    def test_exception_in_execute_releases_the_gate(self):
        b = object.__new__(tb.TrajectoryBridge)
        b._gate = tb.BusyGate()
        self.assertTrue(b._gate.acquire())

        class Gh:
            @property
            def request(self):
                raise RuntimeError('boom')
        with self.assertRaises(RuntimeError):
            b._execute(Gh(), ['joint1'])
        self.assertFalse(b._gate.busy)


class HoldPolicy(unittest.TestCase):
    def make(self):
        b = object.__new__(tb.TrajectoryBridge)
        b.gripper_set = {'r_joint'}
        b.sent = []
        b.period = 0.2
        b._current = lambda joints: ([0.1] * len(joints), '')
        b._send = lambda joints, vec, dur: b.sent.append((list(joints), list(vec)))
        b.get_logger = lambda: types.SimpleNamespace(warn=lambda *_: None, info=lambda *_: None)
        return b

    class Gh:
        is_cancel_requested = False

        def abort(self):
            pass

        def canceled(self):
            pass

        def succeed(self):
            pass

    def test_gripper_is_never_held(self):
        b = self.make()
        b._finish(self.Gh(), -4, 'canceled', ['r_joint'], hold=True)
        self.assertEqual(b.sent, [])

    def test_arm_joints_are_still_held(self):
        b = self.make()
        b._finish(self.Gh(), -4, 'lag', JOINTS, hold=True)
        self.assertEqual(b.sent, [(JOINTS, [0.1] * 5)])

    def test_mixed_list_holds_only_the_arm_joints(self):
        b = self.make()
        b._finish(self.Gh(), -4, 'lag', ['joint1', 'r_joint'], hold=True)
        self.assertEqual(b.sent, [(['joint1'], [0.1])])

    def test_no_hold_when_not_asked(self):
        b = self.make()
        b._finish(self.Gh(), -5, 'did not reach', JOINTS, hold=False)
        self.assertEqual(b.sent, [])


if __name__ == '__main__':
    unittest.main()
