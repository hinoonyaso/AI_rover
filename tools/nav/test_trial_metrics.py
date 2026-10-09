#!/usr/bin/env python3
# 한글: trial_metrics.diag_frac 단위시험(ROS 불필요, CI).
"""Unit tests for tools/nav/trial_metrics.py."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trial_metrics import diag_frac  # noqa: E402


class DiagFracTest(unittest.TestCase):

    def test_forward_and_45_deg_pass(self):
        self.assertEqual(diag_frac([(0.12, 0.0), (0.08, 0.08), (0.08, -0.08)]), 0.0)

    def test_strafe_counts(self):
        self.assertAlmostEqual(diag_frac([(0.12, 0.0), (0.0, 0.12)]), 0.5)

    def test_boundary(self):
        a = math.radians(50.0)
        just_over = (0.1 * math.cos(a + 0.01), 0.1 * math.sin(a + 0.01))
        just_under = (0.1 * math.cos(a - 0.01), 0.1 * math.sin(a - 0.01))
        self.assertEqual(diag_frac([just_over]), 1.0)
        self.assertEqual(diag_frac([just_under]), 0.0)

    def test_slow_and_turning_skipped(self):
        self.assertEqual(diag_frac([(0.0, 0.0), (0.0, 0.02), (0.1, 0.0)]), 0.0)
        self.assertTrue(math.isnan(diag_frac([(0.0, 0.0)])))

    def test_reverse_is_over(self):
        self.assertEqual(diag_frac([(-0.1, 0.0)]), 1.0)


if __name__ == '__main__':
    unittest.main()
