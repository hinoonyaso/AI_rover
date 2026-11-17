"""Compute a stationary gyro bias candidate without applying it.

한글: 값을 적용하지 않고 정지 자이로 bias 후보를 계산한다.
"""
import math
import statistics


def gyro_candidate(samples, current_bias, after_bias, min_samples=10, max_std=0.02):
    """Return a candidate only from finite stationary residuals and stable bias.

    한글: 유한한 정지 잔차와 변경되지 않은 현재 bias로만 후보를 반환한다.
    """
    def vector(values):
        if len(values) != 3 or not all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in values):
            raise ValueError('invalid_vector')
        return [float(x) for x in values]

    before, after = vector(current_bias), vector(after_bias)
    if any(abs(x-y) > 1e-9 for x, y in zip(before, after)):
        raise ValueError('bias_changed')
    rows = [vector(row) for row in samples]
    if len(rows) < min_samples:
        raise ValueError('insufficient_samples')
    axes = list(zip(*rows))
    mean = [statistics.mean(axis) for axis in axes]
    std = [statistics.pstdev(axis) for axis in axes]
    if any(value > max_std for value in std):
        raise ValueError('not_stationary')
    return {'samples': len(rows), 'current_bias': before, 'residual_mean': mean,
            'std': std, 'candidate': [old + residual for old, residual in zip(before, mean)],
            'unit': 'rad/s', 'applied': False}


def accel_pose_summary(samples, expected, *, min_samples=50, max_std=0.2, max_cross=3.0):
    """Validate one stationary axis-aligned accelerometer pose.

    한글: 축에 정렬된 정지 가속도계 자세 한 개를 검증한다.
    """
    axes = {'x_plus': (0, 1), 'x_minus': (0, -1), 'y_plus': (1, 1),
            'y_minus': (1, -1), 'z_plus': (2, 1), 'z_minus': (2, -1)}
    if expected not in axes:
        raise ValueError('invalid_pose')
    rows = []
    for row in samples:
        if len(row) != 3 or not all(isinstance(v, (float, int)) and not isinstance(v, bool) and math.isfinite(v) for v in row):
            raise ValueError('invalid_vector')
        rows.append(row)
    if len(rows) < min_samples:
        raise ValueError('insufficient_samples')
    columns = list(zip(*rows))
    means = [statistics.mean(values) for values in columns]
    std = [statistics.pstdev(values) for values in columns]
    if any(value > max_std for value in std):
        raise ValueError('not_stationary')
    axis, sign = axes[expected]
    if not 7.0 <= means[axis] * sign <= 12.5 or any(abs(means[i]) > max_cross for i in range(3) if i != axis):
        raise ValueError('incorrect_pose')
    return {'pose': expected, 'mean': means, 'std': std, 'samples': len(rows), 'unit': 'm/s²'}


def accel_candidate(poses):
    """Estimate diagonal offsets/scales from six validated stationary poses.

    한글: 검증된 정지 여섯 자세에서 축별 오프셋과 배율을 추정한다.
    """
    axis_names = ('x', 'y', 'z')
    if set(poses) != {f'{axis}_{sign}' for axis in axis_names for sign in ('plus', 'minus')}:
        raise ValueError('incomplete_poses')
    frames = {item.get('frame_id') for item in poses.values()}
    sources = {item.get('source_id') for item in poses.values()}
    if len(frames) != 1 or not next(iter(frames)) or len(sources) != 1 or not next(iter(sources)):
        raise ValueError('source_changed')
    settings = [(item.get('current_offset_m_s2'), item.get('current_scale')) for item in poses.values()]
    if any(not isinstance(offset, list) or not isinstance(scale, list) or len(offset) != 3 or len(scale) != 3
           or any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in offset + scale)
           or any(abs(x) > 10 for x in offset) or any(not .5 <= x <= 2 for x in scale)
           for offset, scale in settings):
        raise ValueError('accel_settings_unavailable')
    current_offset, current_scale = settings[0]
    if any(offset != current_offset or scale != current_scale for offset, scale in settings):
        raise ValueError('accel_settings_changed')
    offsets, scales = [], []
    for index, axis in enumerate(axis_names):
        plus = poses[f'{axis}_plus']['mean'][index]
        minus = poses[f'{axis}_minus']['mean'][index]
        if not all(math.isfinite(v) for v in (plus, minus)) or not 14 <= plus - minus <= 25:
            raise ValueError('invalid_range')
        offsets.append((plus + minus) / 2)
        scales.append(2 * 9.80665 / (plus - minus))
    # Compose residual calibration with the active transform instead of applying it twice.
    # 한글: 기존 변환과 잔차 보정을 합성하여 보정이 중복 적용되지 않게 한다.
    combined_offset = [current_offset[i] + offsets[i] / current_scale[i] for i in range(3)]
    combined_scale = [current_scale[i] * scales[i] for i in range(3)]
    if any(abs(v) > 10 for v in combined_offset) or any(not .5 <= v <= 2 for v in combined_scale):
        raise ValueError('invalid_range')
    return {'offset_m_s2': combined_offset, 'scale': combined_scale, 'current_offset_m_s2':current_offset,
            'current_scale':current_scale, 'residual_offset_m_s2':offsets, 'residual_scale':scales,
            'frame_id': next(iter(frames)), 'source_id': next(iter(sources)), 'method': 'six_pose_diagonal',
            'poses': poses, 'applied': False}
