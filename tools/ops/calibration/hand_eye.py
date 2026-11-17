#!/usr/bin/python3
"""Estimate camera pose relative to link4 from manually supplied rigid poses.

한글: 수동 입력한 강체 자세로 link4 기준 카메라 자세를 추정한다.
"""
import json
import sys
import cv2
import numpy as np


def matrix(value):
    """Validate a homogeneous rigid transform. / 동차 강체 변환을 검증한다."""
    m = np.asarray(value, dtype=float)
    if m.shape != (4, 4) or not np.isfinite(m).all() or np.max(np.abs(m[:3, 3])) > 10:
        raise ValueError('invalid_pose')
    r = m[:3, :3]
    if not np.allclose(m[3], [0, 0, 0, 1], atol=1e-6) or not np.allclose(r.T @ r, np.eye(3), atol=1e-4) or abs(np.linalg.det(r)-1) > 1e-4:
        raise ValueError('invalid_pose')
    return m


def fit_hand_eye(pairs):
    """Return link4←camera transform and fixed-target consistency residuals.

    한글: link4←camera 변환과 고정 표적 일관성 잔차를 반환한다.
    """
    if not 5 <= len(pairs) <= 30:
        raise ValueError('invalid_pose_count')
    arm = [matrix(p['base_T_link4']) for p in pairs]
    target = [matrix(p['camera_T_target']) for p in pairs]
    rotations = [cv2.Rodrigues(arm[0][:3,:3].T @ m[:3,:3])[0].flatten() for m in arm[1:]]
    singular = np.linalg.svd(np.asarray(rotations), compute_uv=False)
    if len(singular) < 2 or singular[1] < 0.1:
        raise ValueError('insufficient_rotation_diversity')
    rotation, translation = cv2.calibrateHandEye([m[:3,:3] for m in arm], [m[:3,3] for m in arm],
        [m[:3,:3] for m in target], [m[:3,3] for m in target], method=cv2.CALIB_HAND_EYE_PARK)
    if not np.isfinite(rotation).all() or not np.isfinite(translation).all() or abs(np.linalg.det(rotation)-1)>1e-3 or not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-3):
        raise ValueError('fit_failed')
    transform = np.eye(4)
    transform[:3,:3], transform[:3,3] = rotation, translation.flatten()
    targets = [a @ transform @ b for a,b in zip(arm,target)]
    center = np.mean([t[:3,3] for t in targets], axis=0)
    translations = [float(np.linalg.norm(t[:3,3]-center)) for t in targets]
    reference_rotation = targets[0][:3,:3]
    angles = [float(np.linalg.norm(cv2.Rodrigues(reference_rotation.T @ t[:3,:3])[0])) for t in targets]
    return {'link4_T_camera': transform.tolist(), 'translation_rms_m': float(np.sqrt(np.mean(np.square(translations)))),
            'rotation_max_rad': max(angles), 'pose_count': len(pairs), 'translation_residuals_m': translations}


def main():
    """Read bounded JSON and output a result. / 제한된 JSON 입력과 결과를 처리한다."""
    try:
        data = json.load(sys.stdin)
        print(json.dumps({'result': fit_hand_eye(data['pairs'])}, allow_nan=False))
    except (KeyError, ValueError, TypeError, np.linalg.LinAlgError, cv2.error) as exc:
        print(json.dumps({'error': str(exc)}))
        sys.exit(1)

if __name__ == '__main__': main()
