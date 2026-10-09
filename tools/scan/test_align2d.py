# 한글: 2D ICP 단위시험(합성 방 벽). python3 tools/scan/test_align2d.py
"""Synthetic test for align2d.icp2d (no ROS)."""
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from align2d import icp2d, transform  # noqa: E402


def room(step=0.05):
    xs = np.arange(0, 3.0, step)
    ys = np.arange(0, 2.5, step)
    walls = [np.stack([xs, np.zeros_like(xs)], 1), np.stack([xs, np.full_like(xs, 2.5)], 1),
             np.stack([np.zeros_like(ys), ys], 1), np.stack([np.full_like(ys, 3.0), ys], 1)]
    box = np.stack([np.full(6, 1.2), np.linspace(1.0, 1.25, 6)], 1)  # furniture edge (asymmetry)
    return np.concatenate(walls + [box])


class Align2dTest(unittest.TestCase):
    def test_recovers_known_offset(self):
        dst = room()
        true = (0.12, -0.08, math.radians(4.0))
        # src = dst moved by the inverse of `true`, so icp must find `true`
        c, s = math.cos(true[2]), math.sin(true[2])
        r = np.array([[c, -s], [s, c]])
        src = (dst - np.array(true[:2])) @ r  # inverse transform
        rng = np.random.default_rng(0)
        src = src + rng.normal(0, 0.005, src.shape)
        (x, y, yaw), res = icp2d(src, dst)
        self.assertAlmostEqual(x, true[0], delta=0.01)
        self.assertAlmostEqual(y, true[1], delta=0.01)
        self.assertAlmostEqual(math.degrees(yaw), 4.0, delta=0.3)
        self.assertLess(np.median(res), 0.02)

    def test_transform_roundtrip(self):
        p = np.array([[1.0, 0.0], [0.0, 2.0]])
        q = transform(p, 1.0, 2.0, math.pi / 2)
        np.testing.assert_allclose(q, [[1.0, 3.0], [-1.0, 2.0]], atol=1e-9)


if __name__ == '__main__':
    unittest.main()
