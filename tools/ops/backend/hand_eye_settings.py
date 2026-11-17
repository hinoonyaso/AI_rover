"""Review and safely persist a link4-to-camera hand-eye candidate.

한글: link4 기준 카메라 핸드아이 후보를 검토하고 안전하게 저장한다.
"""
import base64
import json
import math
import os
import re
import stat
import uuid
import xml.etree.ElementTree as ET
import gyro_settings as shared


def _matrix(value):
    if not isinstance(value, list) or len(value) != 4 or any(not isinstance(row, list) or len(row) != 4 for row in value):
        raise ValueError('invalid_pose')
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for row in value for x in row):
        raise ValueError('invalid_pose')
    if any(abs(value[3][i] - (1 if i == 3 else 0)) > 1e-5 for i in range(4)):
        raise ValueError('invalid_pose')
    r = [row[:3] for row in value[:3]]
    for i in range(3):
        for j in range(3):
            if abs(sum(r[k][i] * r[k][j] for k in range(3)) - (1 if i == j else 0)) > 1e-4:
                raise ValueError('invalid_pose')
    det = (r[0][0]*(r[1][1]*r[2][2]-r[1][2]*r[2][1]) - r[0][1]*(r[1][0]*r[2][2]-r[1][2]*r[2][0]) + r[0][2]*(r[1][0]*r[2][1]-r[1][1]*r[2][0]))
    if abs(det - 1) > 1e-4 or any(abs(value[i][3]) > 2 for i in range(3)):
        raise ValueError('invalid_pose')
    return value


def _target(candidate, mount):
    a, b = _matrix(candidate), _matrix(mount)
    # link4_T_mount = link4_T_optical * inverse(mount_T_optical).
    # link4_T_mount = link4_T_optical * inverse(mount_T_optical)이다.
    rot = [[sum(a[i][k] * b[j][k] for k in range(3)) for j in range(3)] for i in range(3)]
    xyz = [a[i][3] - sum(rot[i][j] * b[j][3] for j in range(3)) for i in range(3)]
    if any(abs(x) > 2 for x in xyz):
        raise ValueError('invalid_pose')
    pitch = math.atan2(-rot[2][0], math.hypot(rot[0][0], rot[1][0]))
    if abs(math.cos(pitch)) > 1e-8:
        roll, yaw = math.atan2(rot[2][1], rot[2][2]), math.atan2(rot[1][0], rot[0][0])
    else:
        roll, yaw = math.atan2(-rot[1][2], rot[1][1]), 0.0
    return xyz, [roll, pitch, yaw]


def _read(path):
    if path.is_symlink() or not path.is_file(): raise ValueError('config_unavailable')
    data = path.read_bytes()
    if len(data) > 2_000_000: raise ValueError('invalid_config')
    text = data.decode('utf-8')
    try:
        tree = ET.fromstring(text)
        joints = [j for j in tree.findall('joint') if j.get('name') == 'camera_connect_joint']
        if len(joints) != 1 or joints[0].get('type') != 'fixed' or joints[0].find('parent').get('link') != 'link4' or joints[0].find('child').get('link') != 'camera_connect_link': raise ValueError()
        origin = joints[0].find('origin')
        current = {'xyz': origin.get('xyz'), 'rpy': origin.get('rpy')}
        if not all(current.values()): raise ValueError()
    except (ET.ParseError, AttributeError, ValueError): raise ValueError('invalid_config') from None
    matches = list(re.finditer(r'(?s)<joint\b(?=[^>]*\bname\s*=\s*["\']camera_connect_joint["\'])[^>]*>.*?</joint\s*>', text))
    if len(matches) != 1: raise ValueError('invalid_config')
    chunk = matches[0]
    origins = list(re.finditer(r'(?s)<origin\b[^>]*?/>', chunk.group()))
    if len(origins) != 1: raise ValueError('invalid_config')
    origin_match = origins[0]; origin_text = origin_match.group()
    xyz = list(re.finditer(r'\bxyz\s*=\s*["\']([^"\']+)["\']', origin_text))
    rpy = list(re.finditer(r'\brpy\s*=\s*["\']([^"\']+)["\']', origin_text))
    if len(xyz) != 1 or len(rpy) != 1: raise ValueError('invalid_config')
    offset = chunk.start() + origin_match.start()
    return data, text, [(offset + xyz[0].start(1), offset + xyz[0].end(1)), (offset + rpy[0].start(1), offset + rpy[0].end(1))], current


def preview(path, candidate, mount):
    """Preview only a confirmed-frame camera mount candidate.

    한글: 프레임이 확인된 카메라 장착 후보만 미리 본다.
    """
    data, _, _, current = _read(path)
    if not isinstance(candidate, dict) or candidate.get('applied') is not False or candidate.get('parent_frame') != 'link4' or candidate.get('camera_frame') != 'depth_cam_color_optical_frame': raise ValueError('candidate_unavailable')
    xyz, rpy = _target(candidate.get('link4_T_camera'), mount)
    review = {'current': current, 'target_xyz_m': xyz, 'target_rpy_rad': rpy, 'mount_T_optical': mount}
    return {**review, 'config_hash': shared._hash(data), 'candidate_hash': shared._hash(json.dumps(review, sort_keys=True).encode()), 'requires_restart': True}


def apply(path, storage, candidate, mount, config_hash, candidate_hash):
    """Back up and update only camera_connect_joint origin.

    한글: 백업을 남기고 camera_connect_joint 원점만 변경한다.
    """
    plan = preview(path, candidate, mount); data, text, spans, _ = _read(path)
    if plan['candidate_hash'] != candidate_hash: raise ValueError('candidate_changed')
    if plan['config_hash'] != config_hash or shared._hash(data) != config_hash: raise ValueError('config_changed')
    for (start, end), values in sorted(zip(spans, (plan['target_xyz_m'], plan['target_rpy_rad'])), reverse=True):
        text = text[:start] + ' '.join(format(x, '.12g') for x in values) + text[end:]
    result = text.encode(); storage.mkdir(mode=0o700, parents=True, exist_ok=True); backup_id = uuid.uuid4().hex
    record = {'id': backup_id, 'previous_base64': base64.b64encode(data).decode(), 'before_hash': shared._hash(data), 'after_hash': shared._hash(result)}
    fd = os.open(storage / (backup_id + '.json'), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as out: json.dump(record, out); out.flush(); os.fsync(out.fileno())
    if shared._hash(path.read_bytes()) != config_hash: raise ValueError('config_changed')
    shared._atomic(path, result, stat.S_IMODE(path.stat().st_mode))
    return {'backup_id': backup_id, 'requires_restart': True}


def restore(path, storage, backup_id):
    """Restore an unchanged camera model from its backup.

    한글: 변경되지 않은 카메라 모델을 백업에서 복원한다.
    """
    if not re.fullmatch('[0-9a-f]{32}', backup_id): raise ValueError('invalid_backup')
    backup = storage / (backup_id + '.json')
    if backup.is_symlink() or not backup.is_file(): raise ValueError('invalid_backup')
    record = json.loads(backup.read_text()); previous = base64.b64decode(record['previous_base64'], validate=True)
    if record.get('id') != backup_id or shared._hash(previous) != record.get('before_hash'): raise ValueError('invalid_backup')
    data, *_ = _read(path)
    if shared._hash(data) != record.get('after_hash'): raise ValueError('config_changed')
    shared._atomic(path, previous, stat.S_IMODE(path.stat().st_mode))
    return {'restored': True, 'requires_restart': True}
