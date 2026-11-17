"""Synthetic-image tests; Gazebo and real-world validation are separate.

한글: 합성 영상 단위 시험이며 Gazebo 및 실기 검증과 구분한다.
"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from stack_light import classify  # noqa: E402

REGIONS = {'red': (0, 0, 10, 10), 'yellow': (10, 0, 10, 10),
           'green': (20, 0, 10, 10)}


def frames(states):
    """Build timestamped RGB fixtures. / 한글: 시각이 있는 RGB 시험 영상을 만든다."""
    out = []
    for i, values in enumerate(zip(*states)):
        hsv = np.zeros((10, 30, 3), np.uint8)
        for index, (hue, value) in enumerate(zip((0, 27, 60), values)):
            hsv[:, index * 10:(index + 1) * 10] = (hue, 255, value)
        out.append((i * .5, cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)))
    return out


def test_each_colour_and_blinking():
    data = frames([[220] * 5, [40] * 5, [220, 220, 40, 40, 220]])
    result = classify(data, REGIONS, 2.0)
    assert [result[c]['state'] for c in REGIONS] == ['on', 'off', 'blinking']
    assert result['green']['samples'] == 5


def test_single_transition_is_not_blinking():
    data = frames([[220, 220, 40, 40, 40]] * 3)
    assert all(item['reason'] == 'incomplete_cycle'
               for item in classify(data, REGIONS, 2).values())


def test_missing_stale_and_gapped_frames_are_unknown():
    data = frames([[220] * 5] * 3)
    for sample, now in ((data[:4], 2), (data, 3),
                        ([(t * 2, image) for t, image in data], 4)):
        assert all(item['state'] == 'unknown' for item in classify(sample, REGIONS, now).values())


def test_occlusion_ambiguous_brightness_and_invalid_region():
    data = frames([[220] * 5, [100] * 5, [220] * 5])
    for _, image in data:
        image[:, :10] = 0
    regions = dict(REGIONS, green=(-1, 0, 10, 10))
    result = classify(data, regions, 2)
    assert result['red']['reason'] == 'target_not_visible'
    assert result['yellow']['reason'] == 'ambiguous_brightness'
    assert result['green']['state'] == 'unknown'
