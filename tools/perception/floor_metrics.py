# 한글: home_pose_eval.py의 계산 부분(ROS 없이 numpy만) — CI에서 단위시험하려고 분리.
"""Floor-coverage metrics of a depth image in base_footprint (pure numpy, unit-tested)."""
import math

import numpy as np

FOOT_X, FOOT_Y = 0.18, 0.25  # planner footprint half sizes (nav2_params.yaml) / 플래너 footprint 반치수


def floor_metrics(d, fx, fy, cx, cy, R, t):
    """Compute floor-coverage metrics.

    d: depth image [mm]; R, t: optical frame -> base_footprint rotation/translation.
    한글: depth를 base_footprint로 투영해 바닥 지표를 계산한다.
    """
    vs, us = np.indices(d.shape)
    valid = d > 0
    z = d[valid] / 1000.0
    pc = np.stack([(us[valid] - cx) * z / fx, (vs[valid] - cy) * z / fy, z], 1)
    pb = pc @ R.T + t  # points in base_footprint
    axis = R @ np.array([0, 0, 1.0])  # optical z axis in base frame
    floor = pb[np.abs(pb[:, 2]) < 0.03]
    low = pb[(pb[:, 2] > 0.03) & (pb[:, 2] < 0.25)]
    in_body = ((np.abs(pb[:, 0]) < FOOT_X + 0.05) & (np.abs(pb[:, 1]) < FOOT_Y + 0.05) &
               (pb[:, 2] < 0.25))
    lane = floor[np.abs(floor[:, 1]) < FOOT_Y]
    bins = np.arange(0.20, 1.00, 0.05)
    covered = sum(1 for b in bins if np.any((lane[:, 0] >= b) & (lane[:, 0] < b + 0.05)))

    def width_at(x0):
        s = floor[np.abs(floor[:, 0] - x0) < 0.03]
        return float(s[:, 1].max() - s[:, 1].min()) if len(s) > 5 else 0.0
    return {
        'pb': pb, 'floor': floor, 'low': low, 'in_body': in_body,
        'valid': float(valid.mean()),
        'cam_pitch': math.degrees(math.atan2(-axis[2], math.hypot(axis[0], axis[1]))),
        'near': float(np.percentile(floor[:, 0], 5)) if len(floor) else None,
        'far': float(np.percentile(floor[:, 0], 95)) if len(floor) else None,
        'lane_cover': covered / len(bins),
        'w05': width_at(0.5), 'w10': width_at(1.0),
        'self_frac': float(in_body.mean()) if len(pb) else 0.0,
        'low_frac': len(low) / max(len(pb), 1),
    }
