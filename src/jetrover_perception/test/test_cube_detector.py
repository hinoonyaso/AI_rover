# 한글: cube_detector.py의 순수 함수 시험(ROS 없이) — 합성 영상에 색 사각형을 그리고 위치·depth·역투영을 확인한다.
# Unit tests for the pure helpers of cube_detector.py on synthetic images (no ROS).
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
from cube_detector import (  # noqa: E402, I100
    blob_depth_m, colour_masks, correct_pitch, largest_blob, pixel_to_point)

K = [362.5, 0.0, 318.5, 0.0, 362.5, 177.4, 0.0, 0.0, 1.0]   # the robot camera's colour intrinsics


def scene():
    img = np.full((360, 640, 3), 200, np.uint8)            # grey floor
    img[100:120, 100:120] = (230, 20, 20)                  # red
    img[200:230, 300:330] = (20, 200, 20)                  # green
    img[50:60, 500:510] = (20, 20, 220)                    # blue, small (100 px)
    return img


def test_each_colour_found_at_its_centre():
    masks = colour_masks(scene())
    centres = {'red': (109.5, 109.5), 'green': (314.5, 214.5), 'blue': (504.5, 54.5)}
    for name, (u, v) in centres.items():
        b = largest_blob(masks[name], 50)
        assert b is not None, name
        assert abs(b[0] - u) < 1.0 and abs(b[1] - v) < 1.0, (name, b[:2])


def test_grey_floor_and_other_colours_are_not_detected():
    masks = colour_masks(np.full((360, 640, 3), 200, np.uint8))
    assert all(largest_blob(m, 10) is None for m in masks.values())


def test_min_area_rejects_small_blobs():
    masks = colour_masks(scene())
    assert largest_blob(masks['blue'], 150) is None        # 100 px blob


def test_blob_depth_ignores_zero_and_far_pixels():
    depth = np.zeros((360, 640), np.uint16)
    depth[200:230, 300:330] = 300                          # 0.30 m
    depth[200:205, 300:330] = 0                            # holes
    depth[225:230, 300:330] = 5000                         # far outlier
    blob = largest_blob(colour_masks(scene())['green'], 50)[3]
    assert abs(blob_depth_m(depth, blob, 1.2) - 0.30) < 1e-6


def test_back_projection():
    x, y, z = pixel_to_point(318.5 + 36.25, 177.4, 0.5, K)   # 36.25 px right of centre at 0.5 m
    assert abs(x - 0.05) < 1e-9 and abs(y) < 1e-9 and z == 0.5


def test_pitch_correction():
    import math
    p = math.radians(5.0)
    y, z = correct_pitch(0.0, 1.0, p)      # the camera axis itself tilts 5 deg down
    assert abs(y - math.sin(p)) < 1e-12 and abs(z - math.cos(p)) < 1e-12
    assert correct_pitch(0.2, 0.7, 0.0) == (0.2, 0.7)


def test_magenta_red_in_daylight_is_red():
    # 2026-10-18 실기 큐브 색(H 167, S ~110, V ~200, OpenCV HSV) / the real cube in morning light
    import cv2
    img = np.full((60, 60, 3), 200, np.uint8)
    hsv = np.full((20, 20, 3), (167, 110, 200), np.uint8)
    img[20:40, 20:40] = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    assert largest_blob(colour_masks(img)['red'], 60) is not None
