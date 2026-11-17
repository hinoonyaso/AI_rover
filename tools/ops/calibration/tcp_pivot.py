#!/usr/bin/python3
"""Estimate tool centre from multiple poses around a fixed pivot.

한글: 고정 접점 주위의 여러 자세로 도구 중심을 추정한다.
"""
import json
import sys
import numpy as np
from hand_eye import matrix


def fit_tcp(poses):
    """Solve base_T_gripper poses for gripper-frame TCP and base-frame pivot.

    한글: base_T_gripper 자세들로 그리퍼 기준 TCP와 기준점 위치를 구한다.
    """
    if not 5 <= len(poses) <= 30:
        raise ValueError('invalid_pose_count')
    transforms = [matrix(pose) for pose in poses]
    a = np.vstack([np.hstack((t[:3,:3], -np.eye(3))) for t in transforms])
    b = np.concatenate([-t[:3,3] for t in transforms])
    solution, _, rank, singular = np.linalg.lstsq(a, b, rcond=None)
    if rank != 6 or singular[-1] < 0.05:
        raise ValueError('insufficient_pose_diversity')
    tcp, pivot = solution[:3], solution[3:]
    if np.max(np.abs(tcp)) > 2 or np.max(np.abs(pivot)) > 10:
        raise ValueError('fit_failed')
    distances = [float(np.linalg.norm(t[:3,:3] @ tcp + t[:3,3] - pivot)) for t in transforms]
    return {'tcp_gripper_m': tcp.tolist(), 'pivot_base_m': pivot.tolist(), 'residuals_m': distances,
            'rms_m': float(np.sqrt(np.mean(np.square(distances)))), 'pose_count':len(poses)}


def main():
    """Read poses as JSON and emit a result. / JSON 자세를 읽고 결과를 출력한다."""
    try:
        print(json.dumps({'result':fit_tcp(json.load(sys.stdin)['poses'])}, allow_nan=False))
    except (KeyError, ValueError, TypeError, np.linalg.LinAlgError) as exc:
        print(json.dumps({'error':str(exc)})); sys.exit(1)

if __name__ == '__main__': main()
