"""Validate observed CameraInfo without treating it as calibration proof.

한글: CameraInfo 관측을 검증하되 보정 정확도의 증거로 취급하지 않는다.
"""
import math
from types import SimpleNamespace


def camera_info_snapshot(msg, received_at):
    """Create a bounded observation, or return None for invalid intrinsics.

    한글: 유효한 내부 파라미터만 제한된 관측값으로 만들고 나머지는 버린다.
    """
    try:
        width, height = int(msg.width), int(msg.height)
        matrix, distortion = list(msg.k), list(msg.d)
        if (not 0 < width <= 10000 or not 0 < height <= 10000 or len(matrix) != 9
                or len(distortion) > 32 or not all(math.isfinite(v) for v in matrix + distortion)
                or matrix[0] <= 0 or matrix[4] <= 0 or not msg.header.frame_id
                or len(msg.header.frame_id) > 256 or len(msg.distortion_model) > 128):
            return None
        return {'width': width, 'height': height, 'matrix': matrix, 'distortion': distortion,
                'distortion_model': msg.distortion_model, 'frame_id': msg.header.frame_id,
                'received_at': received_at}
    except (AttributeError, TypeError, ValueError, OverflowError):
        return None


def fresh_camera_info(snapshot, now):
    """Expose only recent snapshot and observation timestamps.

    한글: 최근 상태 파일과 관측 시각을 가진 카메라 정보만 제공한다.
    """
    try:
        timestamp = snapshot['timestamp']
        if isinstance(timestamp, bool) or not math.isfinite(timestamp) or not 0 <= now - timestamp < 8:
            return {}
        result = {}
        for name in ('color', 'depth'):
            item = snapshot.get('camera_info', {}).get(name)
            if not isinstance(item, dict):
                continue
            received = item.get('received_at')
            if isinstance(received, bool) or not isinstance(received, (int, float)) or not math.isfinite(received):
                continue
            if 0 <= now - received < 10 and received <= timestamp:
                message = SimpleNamespace(width=item.get('width'), height=item.get('height'),
                    k=item.get('matrix'), d=item.get('distortion'),
                    distortion_model=item.get('distortion_model'),
                    header=SimpleNamespace(frame_id=item.get('frame_id')))
                checked = camera_info_snapshot(message, received)
                if checked is not None:
                    result[name] = checked
        return result
    except (AttributeError, KeyError, TypeError, ValueError):
        return {}
