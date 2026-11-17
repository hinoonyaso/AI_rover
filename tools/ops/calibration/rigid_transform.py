#!/usr/bin/python3
"""Fit a rigid transform to 3-D point correspondences without robot motion.

한글: 로봇 구동 없이 3차원 대응점의 강체 변환을 계산한다.
"""
import json
import sys
import numpy as np


def fit_rigid_transform(camera_points, reference_points):
    """Return camera-to-reference rotation, translation, and residuals in metres.

    한글: 카메라→기준 좌표계 회전, 이동 및 미터 단위 잔차를 계산한다.
    """
    a = np.asarray(camera_points, dtype=float)
    b = np.asarray(reference_points, dtype=float)
    if a.ndim != 2 or a.shape != b.shape or a.shape[1] != 3 or not 4 <= len(a) <= 30:
        raise ValueError('invalid_points')
    if not np.isfinite(a).all() or not np.isfinite(b).all() or np.max(np.abs(a)) > 10 or np.max(np.abs(b)) > 10:
        raise ValueError('invalid_points')
    ac, bc = a.mean(axis=0), b.mean(axis=0)
    aa, bb = a - ac, b - bc
    # At least two well-separated directions are needed to resolve a 3-D rotation.
    # 한글: 3차원 회전에는 충분히 분리된 두 방향 이상의 점 배치가 필요하다.
    sa, sb = np.linalg.svd(aa, compute_uv=False), np.linalg.svd(bb, compute_uv=False)
    if sa[1] < 0.005 or sb[1] < 0.005:
        raise ValueError('degenerate_points')
    u, singular, vt = np.linalg.svd(aa.T @ bb)
    if singular[1] < 1e-6:
        raise ValueError('degenerate_points')
    fix = np.eye(3)
    fix[2, 2] = np.sign(np.linalg.det(vt.T @ u.T))
    rotation = vt.T @ fix @ u.T
    translation = bc - rotation @ ac
    residual = np.linalg.norm((rotation @ a.T).T + translation - b, axis=1)
    return {'rotation_matrix': rotation.tolist(), 'translation_m': translation.tolist(),
            'residuals_m': residual.tolist(), 'rms_m': float(np.sqrt(np.mean(residual ** 2))),
            'max_error_m': float(np.max(residual)), 'point_count': len(a)}


def main():
    """Read bounded JSON input and emit one JSON result. / 제한된 JSON을 읽고 결과 하나를 출력한다."""
    try:
        data = json.load(sys.stdin)
        print(json.dumps({'result': fit_rigid_transform(data['camera_points'], data['reference_points'])}, allow_nan=False))
    except (ValueError, KeyError, TypeError, np.linalg.LinAlgError) as exc:
        print(json.dumps({'error': str(exc)}))
        sys.exit(1)


if __name__ == '__main__':
    main()
