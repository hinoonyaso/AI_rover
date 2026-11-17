"""Validate received wheel-feedback diagnostics without inferring absent samples.

한글: 미수신을 추측하지 않고 휠 피드백 진단을 검증한다.
"""
import math


def wheel_feedback_snapshot(statuses, now):
    """Return four decoded controller-port values or None for invalid diagnostics.

    한글: 올바른 진단에서만 컨트롤러 네 포트 값을 반환한다.
    """
    selected = [status for status in statuses if status.name == 'wheel_feedback' and status.hardware_id == 'rrc_m4']
    if len(selected) != 1:
        return None
    try:
        pairs = [(v.key, v.value) for v in selected[0].values]
        data = dict(pairs)
        if len(data) != len(pairs):
            return None
        speeds = [float(data[f'port_{i}_rps']) for i in range(1, 5)]
        counters = [int(data[f'port_{i}_counter']) for i in range(1, 5)]
        if any(not math.isfinite(v) or abs(v) > 100 for v in speeds):
            return None
        if any(not -(2**31) <= v < 2**31 for v in counters):
            return None
        return {'port_rps': speeds, 'port_counter': counters, 'received_at': now}
    except (KeyError, TypeError, ValueError, OverflowError):
        return None


def fresh_wheel_feedback(snapshot, now):
    """Return current wheel feedback only when monitor and observation are fresh.

    한글: 모니터와 관측이 모두 최신일 때만 휠 피드백을 제공한다.
    """
    try:
        item = snapshot['wheel_feedback']
        timestamp, received = snapshot['timestamp'], item['received_at']
        speeds, counters = item['port_rps'], item['port_counter']
        if (not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in (timestamp, received))
                or not 0 <= now - timestamp < 8 or not 0 <= now - received < 5 or received > timestamp
                or len(speeds) != 4 or len(counters) != 4
                or any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) or abs(v)>100 for v in speeds)
                or any(not isinstance(v, int) or isinstance(v, bool) or not -(2**31) <= v < 2**31 for v in counters)):
            return None
        return item
    except (KeyError, TypeError, ValueError):
        return None
