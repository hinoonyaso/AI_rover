"""Pure mission contract; it never talks to a robot or database.

한글: 로봇이나 데이터베이스에 접근하지 않는 임무 상태 계약이다.
"""
from enum import StrEnum
from uuid import UUID


class MissionState(StrEnum):
    """Mission lifecycle values. / 임무 생명주기 상태 값."""
    CREATED = 'created'
    QUEUED = 'queued'
    RUNNING = 'running'
    CANCEL_REQUESTED = 'cancel_requested'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    CANCELED = 'canceled'
    INTERRUPTED = 'interrupted'


# Cancellation may race a final result: accept a confirmed outcome, never infer one.
# 한글: 취소 요청과 완료 결과가 경쟁할 수 있으므로 확인된 결과만 반영한다.
TRANSITIONS = {
    MissionState.CREATED: frozenset((MissionState.QUEUED, MissionState.CANCELED)),
    MissionState.QUEUED: frozenset((MissionState.RUNNING, MissionState.CANCEL_REQUESTED, MissionState.FAILED, MissionState.INTERRUPTED)),
    MissionState.RUNNING: frozenset((MissionState.CANCEL_REQUESTED, MissionState.SUCCEEDED, MissionState.FAILED, MissionState.INTERRUPTED)),
    MissionState.CANCEL_REQUESTED: frozenset((MissionState.CANCELED, MissionState.SUCCEEDED, MissionState.FAILED, MissionState.INTERRUPTED)),
    MissionState.SUCCEEDED: frozenset(),
    MissionState.FAILED: frozenset(),
    MissionState.CANCELED: frozenset(),
    MissionState.INTERRUPTED: frozenset(),
}


class ContractError(ValueError):
    """Machine-readable contract failure. / 기계 판독 가능한 계약 오류."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def validate_transition(current, target):
    """Validate one state transition. / 상태 전이 한 건을 검증한다."""
    try:
        current, target = MissionState(current), MissionState(target)
    except (ValueError, TypeError):
        raise ContractError('invalid_state') from None
    if target not in TRANSITIONS[current]:
        raise ContractError('invalid_transition')
    return target


def validate_create_request(payload):
    """Validate a simulation-only request and normalize its idempotency key.

    한글: 시뮬레이션 전용 요청을 검증하고 중복 방지 키를 정규화한다.
    """
    if not isinstance(payload, dict) or set(payload) != {'request_id', 'mode', 'kind', 'parameters'}:
        raise ContractError('invalid_request')
    try:
        key = payload['request_id']
        if not isinstance(key, str) or len(key) != 36 or str(UUID(key)) != key:
            raise ValueError()
    except (ValueError, AttributeError, TypeError):
        raise ContractError('invalid_request_id') from None
    if payload['mode'] not in ('simulation', 'gazebo'):
        raise ContractError('mode_unavailable')
    supported = {'simulation': ('inspection_demo',), 'gazebo': ('navigate_demo', 'inspect_stack_light')}[payload['mode']]
    if payload['kind'] not in supported:
        raise ContractError('unsupported_kind')
    if payload['parameters'] != {} or not isinstance(payload['parameters'], dict):
        raise ContractError('invalid_parameters')
    return {'request_id': key, 'mode': payload['mode'], 'kind': payload['kind'], 'parameters': {}}


def valid_inspection_result(result):
    """Validate simulated color evidence before recording success. / 성공 기록 전 색상 관측 근거를 검증한다."""
    import math
    if not isinstance(result, dict) or set(result) != {'red', 'yellow', 'green'}:
        return False
    for value in result.values():
        if not isinstance(value, dict) or set(value) != {'state', 'reason', 'samples', 'duration_s'}:
            return False
        if (value['state'] not in ('on', 'off', 'blinking') or value['reason'] is not None or
                type(value['samples']) is not int or value['samples'] < 5 or
                type(value['duration_s']) not in (float, int) or
                not math.isfinite(value['duration_s']) or value['duration_s'] < 2):
            return False
    return True
