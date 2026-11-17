"""Combine arm joint observations and diagnostics without controlling hardware.

한글: 하드웨어 구동 없이 관절 관측과 서보 진단을 결합한다.
"""
import math


def valid_mapping(names, ids):
    """Validate the runtime parameter mapping without inventing a default.

    한글: 기본값을 추측하지 않고 런타임 파라미터의 관절 대응을 검증한다.
    """
    if (not names or len(names) != len(ids) or len(names) > 32 or
            len(set(names)) != len(names) or len(set(ids)) != len(ids)):
        return {}
    if any(not isinstance(n, str) or not n or len(n) > 80 for n in names):
        return {}
    if any(isinstance(i, bool) or not isinstance(i, int) or not 0 < i <= 255 for i in ids):
        return {}
    return dict(zip(names, ids))


def arm_observation(mapping, mapping_at, joints, joint_at, diagnostics, diagnostics_at, now, offsets=None, source_confirmed=False):
    """Report observed joints and independently age their servo responses.

    한글: 관절 관측과 서보 응답 경과 시간을 독립적으로 표시한다.
    """
    if not mapping or not 0 <= now - mapping_at < 15:
        return {'mapping_confirmed': False, 'joints': {}}
    result = {}
    for name, servo in mapping.items():
        value = joints.get(name)
        age = diagnostics.get(servo)
        joint_fresh = 0 <= now - joint_at < 3
        stats_fresh = 0 <= now - diagnostics_at < 3
        valid_value = isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
        valid_age = isinstance(age, (int, float)) and not isinstance(age, bool) and math.isfinite(age) and age >= 0
        effective_age = age + now - diagnostics_at if stats_fresh and valid_age else None
        result[name] = {'servo_id': servo, 'position_rad': value if joint_fresh and valid_value else None,
                        'joint_message_age_s': now - joint_at if joint_fresh else None,
                        'servo_response_age_s': effective_age, 'offset_rad': (offsets or {}).get(name),
                        'fresh': bool(joint_fresh and valid_value and effective_age is not None and effective_age < 1.5)}
    return {'mapping_confirmed': True, 'source_confirmed': bool(source_confirmed), 'joints': result}


def fresh_arm_observation(snapshot, now):
    """Age saved observations again at API read time, rejecting stale snapshots.

    한글: API 조회 시각으로 경과 시간을 재계산하고 오래된 스냅샷은 버린다.
    """
    try:
        timestamp = snapshot['timestamp']
        delay = now - timestamp
        if not math.isfinite(delay) or not 0 <= delay < 3:
            return {'mapping_confirmed': False, 'joints': {}}
        arm = snapshot['arm']
        if arm.get('mapping_confirmed') is not True or not isinstance(arm.get('joints'), dict):
            return {'mapping_confirmed': False, 'joints': {}}
        joints = {}
        for name, item in arm['joints'].items():
            if not isinstance(name, str) or not isinstance(item, dict):
                continue
            position, servo_age, message_age = item.get('position_rad'), item.get('servo_response_age_s'), item.get('joint_message_age_s')
            valid = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
            if not valid(position) or not valid(servo_age) or not valid(message_age) or servo_age < 0 or message_age < 0:
                continue
            joints[name] = {'position_rad': position, 'servo_id': item.get('servo_id'),
                            'servo_response_age_s': servo_age + delay, 'joint_message_age_s': message_age + delay,
                            'offset_rad': item.get('offset_rad'),
                            'fresh': servo_age + delay < 1.5 and message_age + delay < 3}
        return {'mapping_confirmed': True, 'source_confirmed': arm.get('source_confirmed') is True, 'joints': joints}
    except (KeyError, TypeError, ValueError, AttributeError):
        return {'mapping_confirmed': False, 'joints': {}}
