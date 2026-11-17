"""Bounded keyset cursors for mission data. / 임무 데이터용 제한된 키셋 커서."""
import base64
import json
from uuid import UUID


def encode_cursor(values):
    """Encode a JSON key tuple for URLs. / 키 튜플을 URL용으로 인코딩한다."""
    return base64.urlsafe_b64encode(json.dumps(values, separators=(',', ':')).encode()).decode().rstrip('=')


def decode_cursor(value, event=False):
    """Validate and decode a mission or event cursor. / 임무·이력 커서를 검증하고 디코딩한다."""
    if not isinstance(value, str) or not value or len(value) > 256:
        raise ValueError('invalid cursor')
    try:
        raw = base64.b64decode(value + '=' * (-len(value) % 4), altchars=b'-_', validate=True)
        key = json.loads(raw)
        if not isinstance(key, list) or len(key) != (3 if event else 2):
            raise ValueError('invalid cursor')
        stamp, identifier = key[:2]
        if (not isinstance(stamp, str) or not 1 <= len(stamp) <= 40 or
                not isinstance(identifier, str) or str(UUID(identifier)) != identifier):
            raise ValueError('invalid cursor')
        if event and (type(key[2]) is not int or not 1 <= key[2] <= 2147483647):
            raise ValueError('invalid cursor')
        return key
    except (ValueError, TypeError, UnicodeError, json.JSONDecodeError):
        raise ValueError('invalid cursor') from None
