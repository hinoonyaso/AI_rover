#!/usr/bin/env python3
"""Measure DOA behavior on synthetic signals; this is not a hardware benchmark.

한글: 합성 신호의 DOA 동작을 측정하며 실제 하드웨어 시험을 대체하지 않는다.
"""
from collections import Counter
import math

from doa_core import estimate_doa
import numpy as np
from test_doa_core import plane_wave


def main():
    """Run reproducible direction and independent-noise checks.

    한글: 재현 가능한 방향 및 독립 잡음 시험을 실행한다.
    """
    angles = np.arange(6) * math.pi / 3
    geometry = np.column_stack((0.035 * np.cos(angles), 0.035 * np.sin(angles)))
    for snr in (10, 0, -10):
        errors = []
        rejected = 0
        for target in range(7, 360, 30):
            for seed in range(5, 10):
                signal = plane_wave(geometry, math.radians(target), seed=seed)
                rng = np.random.default_rng(seed + target * 200)
                sigma = np.sqrt(np.mean(signal ** 2)) * 10 ** (-snr / 20)
                result = estimate_doa(signal + rng.normal(0, sigma, signal.shape), 16000, geometry)
                if result is None:
                    rejected += 1
                else:
                    errors.append(abs((result['angle_deg'] - target + 180) % 360 - 180))
        print(f'SNR={snr:+}dB trials=60 estimated={len(errors)} rejected={rejected} '
              f'within_10deg={sum(error <= 10 for error in errors)} '
              f'max_error_deg={max(errors, default=None)}')
    rng = np.random.default_rng(2377)
    counts = Counter()
    for _ in range(200):
        result = estimate_doa(rng.normal(0, 2000, (4000, 6)), 16000, geometry)
        counts['estimate' if result else 'no_estimate'] += 1
    print(f'independent_noise_only trials=200 estimate={counts["estimate"]} '
          f'no_estimate={counts["no_estimate"]}')


if __name__ == '__main__':
    main()
