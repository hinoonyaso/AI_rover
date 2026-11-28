# 한글: sparse_point_cloud.py의 바닥 평면 기준 높이(floor_aware) 순수 함수 시험(ROS 없이 합성 카메라).
# Unit tests for floor_plane_points of sparse_point_cloud.py with a synthetic ray-cast camera (no ROS).
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
pytest.importorskip('rclpy')
from sparse_point_cloud import fit_floor_plane, floor_plane_points  # noqa: E402, I100

W, H = 96, 54
INTR = (110.0, 110.0, W / 2, H / 2)          # fx, fy, cx, cy
CAM = np.array([0.12, 0.0, 0.33])             # camera position in base_footprint


def camera_rotation(pitch_down_rad):
    """Optical frame (x right, y down, z forward) -> base_footprint, camera pitched down."""
    s, c = np.sin(pitch_down_rad), np.cos(pitch_down_rad)
    return np.column_stack(((0.0, -1.0, 0.0), (-s, 0.0, -c), (c, 0.0, -s)))


def render(rotation, box=None):
    """Depth image (mm, optical z) of the floor z=0 plus an optional box (xmin,xmax,ymin,ymax,zmax)."""
    vs, us = np.indices((H, W)).astype(float)
    d = np.stack(((us - INTR[2]) / INTR[0], (vs - INTR[3]) / INTR[1], np.ones_like(us)), axis=-1)
    r = d @ rotation.T
    with np.errstate(divide='ignore', invalid='ignore'):
        s = np.where(r[..., 2] < 0, -CAM[2] / r[..., 2], np.inf)
        if box is not None:
            lo = np.array([box[0], box[2], 0.0]) - CAM
            hi = np.array([box[1], box[3], box[4]]) - CAM
            t1, t2 = lo / r, hi / r
            near = np.max(np.minimum(t1, t2), axis=-1)
            far = np.min(np.maximum(t1, t2), axis=-1)
            hit = (near <= far) & (near > 0)
            s = np.where(hit & (near < s), near, s)
    depth = np.where(np.isfinite(s) & (s < 4.0), s * 1000.0, 0)
    return depth.astype(np.uint16), us, vs


TRUE_PITCH = np.radians(42.0)
TF_PITCH = TRUE_PITCH + np.radians(3.0)      # joint readings off by ~3 deg (servo backlash)
BOX = (0.55, 0.65, -0.05, 0.05, 0.05)        # 10 x 10 x 5 cm box


def test_plane_fit_ignores_a_minority_of_raised_points():
    rng = np.random.default_rng(1)
    xy = rng.uniform(0.3, 1.0, size=(300, 2))
    z = 0.02 * xy[:, 0] - 0.01
    z[:20] += 0.05
    coef = fit_floor_plane(np.column_stack((xy, z)))
    assert coef == pytest.approx([0.02, 0.0, -0.01], abs=1e-6)


def test_empty_floor_has_no_obstacle_even_with_tilted_tf():
    background, us, vs = render(camera_rotation(TRUE_PITCH))
    result = floor_plane_points(background, background, us, vs, INTR, camera_rotation(TF_PITCH), CAM, 60)
    assert result is not None
    obstacle, free, points, _ = result
    assert obstacle.sum() == 0
    assert free.sum() > 0.5 * (background > 0).sum()
    assert np.abs(points[free][:, 2]).max() < 0.01


def test_low_box_height_is_measured_from_the_visible_floor():
    rotation = camera_rotation(TRUE_PITCH)
    background, us, vs = render(rotation)
    depth, _, _ = render(rotation, BOX)
    tilted = camera_rotation(TF_PITCH)
    obstacle, _, points, _ = floor_plane_points(depth, background, us, vs, INTR, tilted, CAM, 60)
    assert obstacle.sum() > 5
    top = points[obstacle][:, 2].max()
    assert top == pytest.approx(0.05, abs=0.01)
    # Without the plane the same TF error puts the box top far off (what 061 measured).
    # 한글: 평면 없이 같은 TF 오차면 상자 높이가 크게 틀어진다(061 측정).
    fx, fy, cx, cy = INTR
    z = depth / 1000.0
    raw = (np.stack(((us - cx) * z / fx, (vs - cy) * z / fy, z), axis=-1) @ tilted.T + CAM)[..., 2]
    assert abs(raw[obstacle].max() - 0.05) > 0.015


def test_no_floor_visible_returns_none():
    background, us, vs = render(camera_rotation(TRUE_PITCH))
    wall = np.full_like(background, 300)       # something covers the whole view
    assert floor_plane_points(wall, background, us, vs, INTR, camera_rotation(TRUE_PITCH), CAM, 60) is None
