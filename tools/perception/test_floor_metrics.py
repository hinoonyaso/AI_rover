# 한글: floor_metrics를 합성 바닥 depth 영상으로 검증(카메라 높이 0.30 m, 35도 숙임). ROS 불필요.
"""Synthetic-floor unit test for floor_metrics (no ROS).

Run: python3 tools/perception/test_floor_metrics.py
"""
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from floor_metrics import floor_metrics  # noqa: E402

FX = FY = 362.5  # DaBai DCW 640x360 factory K (checklist 11)
CX, CY = 318.5, 177.4
W, H = 640, 360


def synth(pitch_deg, height, x_cam=0.10, box=None):
    th = math.radians(pitch_deg)
    t = np.array([x_cam, 0.0, height])
    r0 = np.array([[0, 0, 1], [-1, 0, 0], [0, -1, 0]], float)  # optical -> base (level)
    ry = np.array([[math.cos(th), 0, math.sin(th)], [0, 1, 0], [-math.sin(th), 0, math.cos(th)]])
    rot = ry @ r0
    vs, us = np.indices((H, W))
    rays = np.stack([(us - CX) / FX, (vs - CY) / FY, np.ones((H, W))], -1)
    dirb = rays @ rot.T
    s = np.where(dirb[..., 2] < 0, -t[2] / dirb[..., 2], 0.0)
    if box is not None:  # vertical face at x = box[0] up to height box[1]
        sb = (box[0] - t[0]) / np.where(dirb[..., 0] > 0, dirb[..., 0], np.inf)
        zb = t[2] + sb * dirb[..., 2]
        hit = (sb > 0) & (zb >= 0) & (zb <= box[1]) & ((s == 0) | (sb < s))
        s = np.where(hit, sb, s)
    s[s > 3.0] = 0
    return (s * 1000).astype(np.uint16), rot, t


class FloorMetricsTest(unittest.TestCase):
    def test_flat_floor_geometry(self):
        d, rot, t = synth(35, 0.30)
        m = floor_metrics(d, FX, FY, CX, CY, rot, t)
        self.assertAlmostEqual(m['cam_pitch'], 35.0, places=3)
        bottom = 0.10 + 0.30 / math.tan(math.radians(35) + math.atan((H - CY) / FY))
        self.assertGreater(m['near'], bottom - 0.01)  # 5th percentile is just beyond the edge
        self.assertLess(m['near'], bottom + 0.05)
        self.assertAlmostEqual(m['lane_cover'], 15 / 16, places=6)  # only 0.20-0.25 bin unseen
        self.assertEqual(m['low_frac'], 0.0)

    def test_steeper_pitch_sees_less_far(self):
        a = floor_metrics(*(lambda d, r, t: (d, FX, FY, CX, CY, r, t))(*synth(35, 0.30)))
        b = floor_metrics(*(lambda d, r, t: (d, FX, FY, CX, CY, r, t))(*synth(55, 0.30)))
        self.assertLess(b['far'], a['far'])
        self.assertLess(b['near'], a['near'])

    def test_box_shows_as_low_points(self):
        d, rot, t = synth(35, 0.30, box=(0.6, 0.10))
        m = floor_metrics(d, FX, FY, CX, CY, rot, t)
        self.assertGreater(m['low_frac'], 0.0)


if __name__ == '__main__':
    unittest.main()
