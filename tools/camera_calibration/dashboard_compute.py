#!/usr/bin/python3
"""Compute a camera candidate from private, locally captured frames.

한글: 로컬 사용자 전용으로 촬영된 영상에서 카메라 보정 후보를 계산한다.
"""
import json
import sys
from pathlib import Path
import cv2
from calibration_math import calibrate_checkerboard

try:
    payload = json.load(sys.stdin)
    files = [Path(p) for p in payload['paths']]
    images = [cv2.imread(str(p), cv2.IMREAD_COLOR) for p in files]
    result = calibrate_checkerboard(images, payload['columns'], payload['rows'], payload['square_m'])
    result.update({'source': 'camera_color_bgr8_lossless_png', 'scope': 'color_intrinsics'})
    print(json.dumps({'result': result}, allow_nan=False))
except (ValueError, OSError, KeyError, TypeError) as error:
    print(json.dumps({'error': str(error)}))
    sys.exit(1)
