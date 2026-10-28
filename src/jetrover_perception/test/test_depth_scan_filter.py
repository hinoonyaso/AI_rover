# 한글: depth_scan_filter.py의 거리 판정 순수 함수 시험(ROS 없이).
# Unit tests for keep_mask of depth_scan_filter.py (no ROS).
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
from depth_scan_filter import keep_mask  # noqa: E402, I100


def test_points_near_a_scan_return_are_dropped():
    # leg seen by the LiDAR at (0.70, 0.10); a low box at (0.65, -0.30) is not seen by it
    scan = np.array([[0.70, 0.10], [0.72, 0.12], [2.0, 0.0]])
    pts = np.array([[0.71, 0.09], [0.66, 0.05], [0.65, -0.30], [0.60, -0.25]])
    keep = keep_mask(pts, scan, 0.10)
    assert keep.tolist() == [False, False, True, True]


def test_no_scan_or_no_points_keeps_everything():
    pts = np.array([[0.5, 0.0], [0.6, 0.1]])
    assert keep_mask(pts, np.zeros((0, 2)), 0.1).tolist() == [True, True]
    assert keep_mask(np.zeros((0, 2)), np.array([[0.5, 0.0]]), 0.1).tolist() == []


def test_many_points_chunked():
    rng = np.random.default_rng(0)
    pts = rng.uniform(-1, 1, size=(5000, 2))
    scan = np.array([[0.0, 0.0]])
    keep = keep_mask(pts, scan, 0.2)
    assert np.array_equal(keep, np.hypot(pts[:, 0], pts[:, 1]) > 0.2)


def test_low_points_near_scan_are_kept():
    # 2026-10-28 사고(troubleshooting/056): 다리(LiDAR 점) 바로 앞 발 점(z 0.06)은 지우면 안 된다
    # foot points under/next to a leg (LiDAR return) must survive; leg points above keep_below_z are still dropped
    scan = np.array([[0.30, 0.20]])
    pts = np.array([[0.30, 0.15], [0.30, 0.15], [0.30, 0.15], [0.60, 0.0]])
    z = np.array([0.06, 0.12, 0.30, 0.30])
    keep = keep_mask(pts, scan, 0.10, z, 0.13)
    assert keep.tolist() == [True, True, False, True]
