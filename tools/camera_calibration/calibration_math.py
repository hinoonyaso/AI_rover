"""Estimate a colour camera calibration candidate from checkerboard images.

한글: 체커보드 영상으로 컬러 카메라 내부 보정 후보를 계산한다.
"""
import math
import cv2
import numpy as np


def calibrate_checkerboard(images, columns, rows, square_m):
    """Estimate intrinsics from diverse views; never write device settings.

    한글: 서로 다른 시야의 영상에서 내부 파라미터를 추정하며 장치 설정을 변경하지 않는다.
    """
    if (type(columns) is not int or type(rows) is not int or not 3 <= columns <= 20 or not 3 <= rows <= 20
            or isinstance(square_m, bool) or not isinstance(square_m, (int, float))
            or not math.isfinite(square_m) or not 0.001 <= square_m <= 0.5):
        raise ValueError('invalid_board')
    if not 8 <= len(images) <= 40:
        raise ValueError('image_count')
    points = np.zeros((rows * columns, 3), np.float32)
    points[:, :2] = np.mgrid[0:columns, 0:rows].T.reshape(-1, 2) * square_m
    objects, corners_all, centers = [], [], []
    size = None
    for image in images:
        if not isinstance(image, np.ndarray) or image.dtype != np.uint8 or image.ndim not in (2, 3):
            raise ValueError('invalid_image')
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
        current_size = (gray.shape[1], gray.shape[0])
        if size is not None and size != current_size:
            raise ValueError('size_mismatch')
        size = current_size
        found, corners = cv2.findChessboardCorners(gray, (columns, rows))
        if not found:
            continue
        corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1),
                                   (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
        objects.append(points.copy())
        corners_all.append(corners)
        centers.append(np.mean(corners.reshape(-1, 2), axis=0))
    if len(objects) < 8:
        raise ValueError('insufficient_detections')
    # Repeated identical frames do not provide independent calibration views.
    # 한글: 동일한 반복 영상은 서로 다른 보정 시야로 간주하지 않는다.
    if max(float(np.linalg.norm(a - b)) for a in centers for b in centers) < min(size) * 0.08:
        raise ValueError('insufficient_diversity')
    rms, matrix, distortion, _, _ = cv2.calibrateCamera(objects, corners_all, size, None, None)
    if not math.isfinite(rms) or not np.isfinite(matrix).all() or not np.isfinite(distortion).all():
        raise ValueError('invalid_result')
    return {'width': size[0], 'height': size[1], 'camera_matrix': matrix.tolist(),
            'distortion': distortion.ravel().tolist(), 'reprojection_rms_px': float(rms),
            'detected_views': len(objects), 'total_views': len(images), 'square_size_m': square_m,
            'applied': False}
