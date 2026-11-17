"""Manage display-only gripper width interpolation.

한글: 그리퍼 폭 표시 전용 보간 설정을 관리한다.
"""
import base64
import json
import math
import os
import re
import uuid
import gyro_settings as shared


def _read(path):
    if path.is_symlink():raise ValueError('config_unavailable')
    if not path.exists():return None
    if not path.is_file() or path.stat().st_size>65536:raise ValueError('invalid_config')
    return path.read_bytes()


def _candidate(candidate):
    if not isinstance(candidate,dict) or candidate.get('method')!='two_point_linear_interpolation' or candidate.get('applied') is not False:raise ValueError('candidate_unavailable')
    slope,intercept,samples=candidate.get('slope_mm_per_rad'),candidate.get('intercept_mm'),candidate.get('samples')
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (slope,intercept)) or abs(slope)>15000 or abs(intercept)>30000 or not isinstance(samples,dict):raise ValueError('invalid_gripper_candidate')
    try:
        opened,closed=samples['open'],samples['closed']
        angles=[opened['angle_rad'],closed['angle_rad']]; widths=[opened['width_mm'],closed['width_mm']]
        if (any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in angles+widths)
                or abs(angles[0]-angles[1])<.02 or widths[0]-widths[1]<1 or min(widths)<0 or max(widths)>300
                or opened['servo_id']!=closed['servo_id'] or opened['servo_id']<=0):raise ValueError()
        if any(abs((slope*a+intercept)-w)>1e-5 for a,w in zip(angles,widths)):raise ValueError()
    except (KeyError,TypeError,ValueError):raise ValueError('invalid_gripper_candidate') from None
    return {'slope_mm_per_rad':slope,'intercept_mm':intercept,'angle_min':min(angles),'angle_max':max(angles),'servo_id':opened['servo_id']}


def preview(path,candidate):
    """Return bounded reviewed interpolation and active version.

    한글: 제한된 보간 후보와 활성 설정 버전을 반환한다.
    """
    current=_read(path);values=_candidate(candidate)
    return {**values,'config_hash':shared._hash(current or b''),'candidate_hash':shared._hash(json.dumps(values,sort_keys=True).encode()),'display_only':True}


def apply(path,storage,candidate,config_hash,candidate_hash):
    """Store a display-only mapping without controlling the gripper.

    한글: 그리퍼 제어 없이 표시 전용 변환을 저장한다.
    """
    plan=preview(path,candidate);previous=_read(path)
    if plan['config_hash']!=config_hash or shared._hash(previous or b'')!=config_hash:raise ValueError('config_changed')
    if plan['candidate_hash']!=candidate_hash:raise ValueError('candidate_changed')
    fields=('slope_mm_per_rad','intercept_mm','angle_min','angle_max','servo_id')
    data=json.dumps({key:plan[key] for key in fields},allow_nan=False).encode()
    path.parent.mkdir(mode=0o700,parents=True,exist_ok=True);storage.mkdir(mode=0o700,parents=True,exist_ok=True)
    backup_id=uuid.uuid4().hex
    record={'id':backup_id,'previous_base64':base64.b64encode(previous).decode() if previous is not None else None,
            'before_hash':shared._hash(previous or b''),'after_hash':shared._hash(data)}
    fd=os.open(storage/(backup_id+'.json'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as out:json.dump(record,out);out.flush();os.fsync(out.fileno())
    if shared._hash(_read(path) or b'')!=config_hash:raise ValueError('config_changed')
    shared._atomic(path,data,0o600)
    return {'backup_id':backup_id,'display_only':True}


def restore(path,storage,backup_id):
    """Restore an unchanged display mapping. / 변경되지 않은 표시 설정을 복원한다."""
    if not re.fullmatch('[0-9a-f]{32}',backup_id):raise ValueError('invalid_backup')
    backup=storage/(backup_id+'.json')
    if backup.is_symlink() or not backup.is_file():raise ValueError('invalid_backup')
    record=json.loads(backup.read_text());old=record.get('previous_base64');previous=base64.b64decode(old,validate=True) if old is not None else None
    if record.get('id')!=backup_id or shared._hash(previous or b'')!=record.get('before_hash'):raise ValueError('invalid_backup')
    current=_read(path)
    if current is None or shared._hash(current)!=record.get('after_hash'):raise ValueError('config_changed')
    if previous is None:path.unlink()
    else:shared._atomic(path,previous,0o600)
    return {'restored':True,'display_only':True}


def width(path,position,servo_id):
    """Interpolate only within measured angles and for the recorded servo.

    한글: 측정한 서보와 각도 범위 내에서만 폭을 보간한다.
    """
    try:
        data=_read(path)
        if data is None or isinstance(position,bool) or not isinstance(position,(int,float)) or not math.isfinite(position):return None
        active=json.loads(data);slope,intercept,lo,hi=(active[k] for k in ('slope_mm_per_rad','intercept_mm','angle_min','angle_max'))
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (slope,intercept,lo,hi)) or active.get('servo_id')!=servo_id or not lo<=position<=hi:return None
        value=slope*position+intercept
        return value if 0<=value<=300 else None
    except (OSError,ValueError,KeyError,TypeError):return None
