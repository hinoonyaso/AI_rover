"""Simulation-only stack light classification helpers.

한글: 시뮬레이션 전용 경광등 판정 함수. 임계값은 실제 장비용으로 검증되지 않았다.
"""
import math

import cv2
import numpy as np


HUE_RANGES = {'red': ((0, 10), (170, 179)), 'yellow': ((20, 35),),
              'green': ((45, 85),)}


def classify(frames, regions, now):
    """Classify timestamped RGB frames in explicit pixel regions.

    한글: 시간 정보가 있는 RGB 영상의 지정된 픽셀 영역을 색상별로 판정한다.
    """
    result = {name: {'state': 'unknown', 'reason': 'insufficient_observation'}
              for name in HUE_RANGES}
    if not math.isfinite(now) or len(frames) < 5:
        return result
    try:
        times = [float(t) for t, _ in frames]
        if (not all(math.isfinite(t) for t in times) or
                any(b <= a or b - a > .6 for a, b in zip(times, times[1:])) or
                times[-1] - times[0] < 2 or not 0 <= now - times[-1] <= .6):
            return result
        images = [image for _, image in frames]
        shape = images[0].shape
        if (len(shape) != 3 or shape[2] != 3 or
                any(image.shape != shape or image.dtype != np.uint8 for image in images)):
            return result
        hsv_images = [cv2.cvtColor(image, cv2.COLOR_RGB2HSV) for image in images]
    except (TypeError, ValueError, AttributeError, cv2.error):
        return result

    for name, ranges in HUE_RANGES.items():
        try:
            x, y, width, height = regions[name]
            if (any(type(v) is not int for v in (x, y, width, height)) or
                    x < 0 or y < 0 or width < 4 or height < 4 or
                    x + width > shape[1] or y + height > shape[0]):
                raise ValueError('invalid region')
            readings = []
            for hsv in hsv_images:
                region = hsv[y:y + height, x:x + width]
                hue, saturation, value = (region[:, :, i] for i in range(3))
                matches = np.zeros(hue.shape, dtype=bool)
                for low, high in ranges:
                    matches |= (hue >= low) & (hue <= high)
                matches &= (saturation >= 100) & (value >= 15)
                # Require visible coloured surface before interpreting a dark lamp as off.
                # 한글: 어두운 조명을 소등으로 보려면 색 표면이 충분히 보여야 한다.
                if np.count_nonzero(matches) < width * height * .5:
                    raise ValueError('target_not_visible')
                brightness = float(np.median(value[matches]))
                if 65 < brightness < 160:
                    raise ValueError('ambiguous_brightness')
                readings.append(brightness >= 160)
            transitions = sum(a != b for a, b in zip(readings, readings[1:]))
            if transitions == 1:
                raise ValueError('incomplete_cycle')
            state = 'blinking' if transitions >= 2 else ('on' if readings[0] else 'off')
            result[name] = {'state': state, 'reason': None, 'samples': len(readings),
                            'duration_s': times[-1] - times[0]}
        except (KeyError, TypeError, ValueError) as exc:
            result[name]['reason'] = str(exc) if str(exc) else 'invalid_region'
    return result
