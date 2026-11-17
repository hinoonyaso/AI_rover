"""Review and atomically persist installed IMU accelerometer calibration.

한글: 설치된 IMU 가속도 보정을 검토하고 원자적으로 저장한다.
"""
import base64
import json
import math
import os
import re
import stat
import uuid
import gyro_settings as shared


def _values(values, offset):
    if (not isinstance(values, list) or len(values) != 3 or
            any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in values)):
        raise ValueError('invalid_accel')
    out_of_range = any(abs(v) > 10 for v in values) if offset else any(not .5 <= v <= 2 for v in values)
    if out_of_range:
        raise ValueError('invalid_accel')
    return [float(v) for v in values]


def _current(text):
    fields={}
    for name in ('accel_offset_m_s2','accel_scale'):
        matches=list(re.finditer(r'(?m)^[ \t]*'+name+r'[ \t]*:[ \t]*\[([^\]\n]*)\][ \t]*(?:#.*)?$',text))
        if len(matches)>1:raise ValueError('invalid_config')
        fields[name]=matches
    if not fields['accel_offset_m_s2'] and not fields['accel_scale']:
        return [0.,0.,0.],[1.,1.,1.], fields
    if not fields['accel_offset_m_s2'] or not fields['accel_scale']:
        raise ValueError('invalid_config')
    try:
        offset=_values([float(v.strip()) for v in fields['accel_offset_m_s2'][0].group(1).split(',')],True)
        scale=_values([float(v.strip()) for v in fields['accel_scale'][0].group(1).split(',')],False)
        return offset,scale,fields
    except ValueError as exc:
        raise ValueError('invalid_config') from exc


def preview(path, candidate):
    """Validate file and candidate baselines. / 파일과 후보의 기존 설정을 검증한다."""
    data,text,_,_=shared._read(path)
    old_offset,old_scale,_=_current(text)
    if not isinstance(candidate,dict):raise ValueError('candidate_unavailable')
    before_offset=_values(candidate.get('current_offset_m_s2'),True)
    before_scale=_values(candidate.get('current_scale'),False)
    target_offset=_values(candidate.get('offset_m_s2'),True)
    target_scale=_values(candidate.get('scale'),False)
    if candidate.get('applied') is not False or candidate.get('method') != 'six_pose_diagonal':raise ValueError('invalid_accel')
    if any(abs(a-b)>1e-6 for a,b in zip(before_offset+before_scale,old_offset+old_scale)):raise ValueError('accel_settings_changed')
    review={'before_offset':before_offset,'before_scale':before_scale,'offset':target_offset,'scale':target_scale}
    return {**review,'config_hash':shared._hash(data),
            'candidate_hash':shared._hash(json.dumps(review,sort_keys=True).encode()),'requires_restart':True}


def apply(path, backup_dir, candidate, config_hash, candidate_hash):
    """Back up and atomically update the reviewed accelerometer parameters.

    한글: 검토된 가속도 파라미터만 백업 후 원자적으로 변경한다.
    """
    plan=preview(path,candidate)
    data,text,gyro,_=shared._read(path)
    if plan['candidate_hash'] != candidate_hash:raise ValueError('candidate_changed')
    if plan['config_hash'] != config_hash or shared._hash(data) != config_hash:raise ValueError('config_changed')
    _,_,fields=_current(text)
    def line(name,values):return '    '+name+': ['+', '.join(format(v,'.9g') for v in values)+']'
    replacement={name:line(name,plan['offset'] if name=='accel_offset_m_s2' else plan['scale']) for name in fields}
    if not fields['accel_offset_m_s2']:
        insertion='\n'+replacement['accel_offset_m_s2']+'\n'+replacement['accel_scale']
        updated=text[:gyro.end()]+insertion+text[gyro.end():]
    else:
        updated=text
        edits=sorted(((matches[0].start(),matches[0].end(),replacement[name]) for name,matches in fields.items()), reverse=True)
        for start,end,value in edits:updated=updated[:start]+value+updated[end:]
    result=updated.encode('utf-8')
    backup_dir.mkdir(mode=0o700,parents=True,exist_ok=True)
    backup_id=uuid.uuid4().hex
    record={'id':backup_id,'previous_base64':base64.b64encode(data).decode('ascii'),
            'before_hash':shared._hash(data),'after_hash':shared._hash(result)}
    fd=os.open(backup_dir/(backup_id+'.json'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as output:
        json.dump(record,output);output.flush();os.fsync(output.fileno())
    if shared._hash(path.read_bytes()) != config_hash:raise ValueError('config_changed')
    shared._atomic(path,result,stat.S_IMODE(path.stat().st_mode))
    return {'backup_id':backup_id,'requires_restart':True}
