"""Review and safely update one installed arm joint offset.

한글: 설치된 팔 관절 오프셋 하나를 검토하고 안전하게 변경한다.
"""
import base64
import json
import math
import os
import re
import stat
import uuid
import gyro_settings as shared


def _read(path):
    data,text,_,_=shared._read(path);fields={}
    for name in ('arm_joint_names','arm_joint_offsets_rad'):
        matches=list(re.finditer(r'(?m)^([ \t]*'+name+r'[ \t]*:[ \t]*)\[([^\]\n]*)\]([ \t]*(?:#.*)?)$',text))
        if len(matches)!=1:raise ValueError('invalid_config')
        fields[name]=matches[0]
    names=[x.strip().strip('"\'') for x in fields['arm_joint_names'].group(2).split(',')]
    try:offsets=[float(x.strip()) for x in fields['arm_joint_offsets_rad'].group(2).split(',')]
    except ValueError:raise ValueError('invalid_config') from None
    if (not names or len(names)!=len(offsets) or len(set(names))!=len(names)
            or any(not re.fullmatch('[A-Za-z0-9_]+',name) for name in names)
            or any(not math.isfinite(v) or abs(v)>3 for v in offsets)):
        raise ValueError('invalid_config')
    return data,text,fields['arm_joint_offsets_rad'],names,offsets


def preview(path,candidate):
    """Verify a single-joint baseline and reviewed correction.

    한글: 단일 관절의 기존 설정과 검토된 보정량을 확인한다.
    """
    data,_,_,names,offsets=_read(path)
    if not isinstance(candidate,dict) or candidate.get('applied') is not False or candidate.get('method')!='single_reference_offset' or candidate.get('source_confirmed') is not True:
        raise ValueError('candidate_unavailable')
    name=candidate.get('joint');before=candidate.get('current_offset_rad');target=candidate.get('candidate_offset_rad')
    if (name not in names or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (before,target))
            or abs(target)>3 or abs(target-before)>.3):raise ValueError('invalid_joint_candidate')
    if abs(offsets[names.index(name)]-before)>1e-6:raise ValueError('joint_settings_changed')
    review={'joint':name,'current':before,'candidate':target}
    return {**review,'config_hash':shared._hash(data),'candidate_hash':shared._hash(json.dumps(review,sort_keys=True).encode()),'requires_restart':True}


def apply(path,storage,candidate,config_hash,candidate_hash):
    """Back up and update exactly one joint offset; never move a motor.

    한글: 모터를 움직이지 않고 관절 오프셋 하나만 백업 후 변경한다.
    """
    plan=preview(path,candidate);data,text,match,names,offsets=_read(path)
    if plan['candidate_hash']!=candidate_hash:raise ValueError('candidate_changed')
    if plan['config_hash']!=config_hash or shared._hash(data)!=config_hash:raise ValueError('config_changed')
    offsets[names.index(plan['joint'])]=plan['candidate']
    replacement=match.group(1)+'['+', '.join(format(v,'.9g') for v in offsets)+']'+match.group(3)
    result=(text[:match.start()]+replacement+text[match.end():]).encode()
    storage.mkdir(mode=0o700,parents=True,exist_ok=True);backup_id=uuid.uuid4().hex
    record={'id':backup_id,'previous_base64':base64.b64encode(data).decode(),'before_hash':shared._hash(data),'after_hash':shared._hash(result)}
    fd=os.open(storage/(backup_id+'.json'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as out:json.dump(record,out);out.flush();os.fsync(out.fileno())
    if shared._hash(path.read_bytes())!=config_hash:raise ValueError('config_changed')
    shared._atomic(path,result,stat.S_IMODE(path.stat().st_mode))
    return {'backup_id':backup_id,'requires_restart':True}
