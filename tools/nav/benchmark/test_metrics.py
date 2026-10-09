import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import metrics as m  # noqa: E402


class MetricsTest(unittest.TestCase):
    def test_angle_diff_wraps(self):
        self.assertAlmostEqual(m.angle_diff(math.radians(350), math.radians(10)), math.radians(-20))
        self.assertAlmostEqual(m.angle_diff(math.radians(-170), math.radians(170)), math.radians(20))

    def test_yaw_from_quat(self):
        self.assertAlmostEqual(m.yaw_from_quat(math.sin(0.4), math.cos(0.4)), 0.8)

    def test_compose2d(self):
        x, y, yaw = m.compose2d((1.0, 2.0, math.pi / 2), (0.5, 0.0, math.pi))
        self.assertAlmostEqual(x, 1.0)
        self.assertAlmostEqual(y, 2.5)
        self.assertAlmostEqual(yaw, -math.pi / 2)  # 3pi/2 wrapped / 감싸기

    def test_cte_straight_line(self):
        plan = [(0, 0), (2, 0)]
        errs = m.cross_track_errors(plan, [(0.5, 0.1), (1.0, -0.2), (3.0, 0.0)])
        self.assertAlmostEqual(errs[0], 0.1)
        self.assertAlmostEqual(errs[1], 0.2)
        self.assertAlmostEqual(errs[2], 1.0)  # 선분 끝점 너머는 끝점까지 거리

    def test_cte_degenerate_plan(self):
        self.assertEqual(m.cross_track_errors([(0, 0)], [(1, 1)]), [])
        self.assertTrue(math.isnan(m.rms([])))

    def test_rms(self):
        self.assertAlmostEqual(m.rms([3.0, 4.0]), math.sqrt(12.5))

    def test_path_length_and_goal_errors(self):
        self.assertAlmostEqual(m.path_length([(0, 0), (3, 4), (3, 5)]), 6.0)
        pos, yaw = m.goal_errors((1.03, 2.04), math.radians(95), (1.0, 2.0), math.radians(90))
        self.assertAlmostEqual(pos, 0.05)
        self.assertAlmostEqual(math.degrees(yaw), 5.0)

    def test_moving_interval(self):
        self.assertEqual(m.moving_interval([0, 1, 2, 3, 4], [0, 0.1, 0.2, 0, 0]), (1, 2))
        self.assertIsNone(m.moving_interval([0, 1], [0, 0.005]))

    def test_summarize(self):
        s = m.summarize([
            {'success': True, 'collision': False, 'pos_err_cm': 4.0, 'time_s': 10},
            {'success': False, 'collision': True, 'pos_err_cm': 8.0, 'time_s': 20},
        ])
        self.assertEqual(s['success_rate'], 0.5)
        self.assertEqual(s['collision_rate'], 0.5)
        self.assertEqual(s['pos_err_cm']['mean'], 6.0)
        self.assertIsNone(s['yaw_err_deg'])


if __name__ == '__main__':
    unittest.main()
