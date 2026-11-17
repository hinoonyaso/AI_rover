"""Manage dashboard-only battery voltage display correction.

한글: 대시보드 표시 전용 배터리 전압 보정을 관리한다.
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
    if not isinstance(candidate,dict) or candidate.get('method')!='linear_reference_fit' or candidate.get('applied') is not False:
        raise ValueError('candidate_unavailable')
    slope,intercept,samples=candidate.get('slope'),candidate.get('intercept_v'),candidate.get('samples')
    if (any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (slope,intercept))
            or not .5<=slope<=2 or abs(intercept)>10 or not isinstance(samples,list) or not 3<=len(samples)<=10):
        raise ValueError('invalid_battery_candidate')
    values=[p.get('sensor_v') if isinstance(p,dict) else None for p in samples]
    if (any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<v<=60 for v in values)
            or max(values)-min(values)<.2):raise ValueError('invalid_battery_candidate')
    return {'slope':slope,'intercept_v':intercept,'sensor_min_v':min(values),'sensor_max_v':max(values)}


def preview(path,candidate):
    """Return reviewed correction and active-file version. / 검토 후보와 활성 파일 버전을 반환한다."""
    current=_read(path);values=_candidate(candidate)
    return {**values,'config_hash':shared._hash(current or b''),
            'candidate_hash':shared._hash(json.dumps(values,sort_keys=True).encode()),'display_only':True}


def apply(path,storage,candidate,config_hash,candidate_hash):
    """Apply only a dashboard display correction and save its previous version.

    한글: 대시보드 표시 보정만 적용하고 이전 버전을 백업한다.
    """
    plan=preview(path,candidate);current=_read(path)
    if plan['config_hash']!=config_hash or shared._hash(current or b'')!=config_hash:raise ValueError('config_changed')
    if plan['candidate_hash']!=candidate_hash:raise ValueError('candidate_changed')
    data=json.dumps({key:plan[key] for key in ('slope','intercept_v','sensor_min_v','sensor_max_v')},allow_nan=False).encode()
    path.parent.mkdir(mode=0o700,parents=True,exist_ok=True);storage.mkdir(mode=0o700,parents=True,exist_ok=True)
    backup_id=uuid.uuid4().hex
    record={'id':backup_id,'previous_base64':base64.b64encode(current).decode() if current is not None else None,
            'before_hash':shared._hash(current or b''),'after_hash':shared._hash(data)}
    fd=os.open(storage/(backup_id+'.json'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as out:json.dump(record,out);out.flush();os.fsync(out.fileno())
    if shared._hash(_read(path) or b'')!=config_hash:raise ValueError('config_changed')
    shared._atomic(path,data,0o600)
    return {'backup_id':backup_id,'display_only':True}


def restore(path,storage,backup_id):
    """Restore an unchanged display configuration; raw safety data is untouched.

    한글: 원본 안전 데이터는 건드리지 않고 변경되지 않은 표시 설정을 복원한다.
    """
    if not re.fullmatch('[0-9a-f]{32}',backup_id):raise ValueError('invalid_backup')
    backup=storage/(backup_id+'.json')
    if backup.is_symlink() or not backup.is_file():raise ValueError('invalid_backup')
    record=json.loads(backup.read_text());old=record.get('previous_base64')
    previous=base64.b64decode(old,validate=True) if old is not None else None
    if record.get('id')!=backup_id or shared._hash(previous or b'')!=record.get('before_hash'):raise ValueError('invalid_backup')
    current=_read(path)
    if current is None or shared._hash(current)!=record.get('after_hash'):raise ValueError('config_changed')
    if previous is None:path.unlink()
    else:shared._atomic(path,previous,0o600)
    return {'restored':True,'display_only':True}


def corrected(path,voltage):
    """Return interpolated display voltage, never extrapolate past references.

    한글: 기준 범위 내 표시 전압만 계산하며 범위 밖으로 외삽하지 않는다.
    """
    try:
        data=_read(path)
        if data is None or not isinstance(voltage,(int,float)) or isinstance(voltage,bool) or not math.isfinite(voltage):return None
        active=json.loads(data);slope,intercept,lo,hi=(active[k] for k in ('slope','intercept_v','sensor_min_v','sensor_max_v'))
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (slope,intercept,lo,hi)) or not .5<=slope<=2 or abs(intercept)>10 or not 0<lo<hi<=60 or not lo<=voltage<=hi:return None
        result=slope*voltage+intercept
        return result if 0<result<=60 else None
    except (OSError,ValueError,KeyError,TypeError):return None
