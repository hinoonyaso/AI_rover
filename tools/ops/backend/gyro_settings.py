"""Prepare, apply, and restore only the installed gyro_bias setting.

한글: 설치된 gyro_bias 설정만 비교·적용·복원한다.
"""
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import tempfile
import uuid

_PATTERN = re.compile(r'(?m)^(\s*gyro_bias\s*:\s*)\[([^\]\n]*)\](\s*(?:#.*)?)$')


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _vector(values):
    if (not isinstance(values, list) or len(values) != 3 or
            any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or abs(v) > 2 for v in values)):
        raise ValueError('invalid_bias')
    return [float(v) for v in values]


def _read(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError('config_unavailable')
    data = path.read_bytes()
    if len(data) > 1_000_000:
        raise ValueError('invalid_config')
    text = data.decode('utf-8')
    matches = list(_PATTERN.finditer(text))
    if len(matches) != 1:
        raise ValueError('invalid_config')
    try:
        values = _vector([float(v.strip()) for v in matches[0].group(2).split(',')])
    except ValueError as exc:
        raise ValueError('invalid_config') from exc
    return data, text, matches[0], values


def _atomic(path, data, mode):
    fd, temp = tempfile.mkstemp(prefix='.gyro-', dir=path.parent)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, 'wb') as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def preview(path, candidate):
    """Read installed values and validate the measured candidate baseline.

    한글: 설치 설정과 측정 당시 기준값을 읽어 적용 가능성을 검증한다.
    """
    data, _, _, current = _read(path)
    if not isinstance(candidate, dict):
        raise ValueError('candidate_unavailable')
    before, target = _vector(candidate.get('current_bias')), _vector(candidate.get('candidate'))
    if any(abs(a - b) > 1e-6 for a, b in zip(before, current)):
        raise ValueError('bias_changed')
    if candidate.get('unit') != 'rad/s' or candidate.get('applied') is not False:
        raise ValueError('invalid_bias')
    return {'current': current, 'candidate': target, 'config_hash': _hash(data),
            'candidate_hash': _hash(json.dumps({'before':before, 'candidate':target}, sort_keys=True).encode()), 'requires_restart': True}


def apply(path, backup_dir, candidate, expected_hash, candidate_hash):
    """Back up and atomically update only a matching installed gyro setting.

    한글: 설치 설정이 일치할 때만 백업 후 gyro 설정을 원자적으로 바꾼다.
    """
    plan = preview(path, candidate)
    data, text, match, _ = _read(path)
    if plan['candidate_hash'] != candidate_hash:
        raise ValueError('candidate_changed')
    if plan['config_hash'] != expected_hash or _hash(data) != expected_hash:
        raise ValueError('config_changed')
    replacement = match.group(1) + '[' + ', '.join(format(v, '.9g') for v in plan['candidate']) + ']' + match.group(3)
    updated = (text[:match.start()] + replacement + text[match.end():]).encode('utf-8')
    backup_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    backup_id = uuid.uuid4().hex
    record = {'id': backup_id, 'previous_base64': base64.b64encode(data).decode('ascii'),
              'before_hash': _hash(data), 'after_hash': _hash(updated)}
    backup = backup_dir / (backup_id + '.json')
    fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as output:
        json.dump(record, output)
        output.flush()
        os.fsync(output.fileno())
    if _hash(path.read_bytes()) != expected_hash:
        raise ValueError('config_changed')
    _atomic(path, updated, stat.S_IMODE(path.stat().st_mode))
    return {'backup_id': backup_id, 'before_hash': record['before_hash'], 'after_hash': record['after_hash'], 'requires_restart': True}


def restore(path, backup_dir, backup_id):
    """Restore a backup only when the installed file still matches its result.

    한글: 적용 후 설정이 그대로인 경우에만 백업을 복원한다.
    """
    if not re.fullmatch('[0-9a-f]{32}', backup_id):
        raise ValueError('invalid_backup')
    backup = backup_dir / (backup_id + '.json')
    if backup.is_symlink() or not backup.is_file():
        raise ValueError('invalid_backup')
    record = json.loads(backup.read_text())
    previous = base64.b64decode(record['previous_base64'], validate=True)
    if record.get('id') != backup_id or _hash(previous) != record.get('before_hash'):
        raise ValueError('invalid_backup')
    data, _, _, _ = _read(path)
    if _hash(data) != record.get('after_hash'):
        raise ValueError('config_changed')
    _atomic(path, previous, stat.S_IMODE(path.stat().st_mode))
    return {'restored': True, 'requires_restart': True}
