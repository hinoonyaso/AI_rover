"""Fit and safely persist command-based odometry scale candidates.

한글: 명령 기반 오도메트리 배율 후보를 계산하고 안전하게 저장한다.
"""
import base64
import json
import math
import os
import re
import stat
import uuid
import gyro_settings as shared

_NAMES=('odom_linear_scale','odom_lateral_scale','odom_angular_scale')


def _read(path):
    data,text,_,_=shared._read(path);fields={}
    for name in _NAMES:
        matches=list(re.finditer(r'(?m)^([ \t]*'+name+r'[ \t]*:[ \t]*)([^\s#]+)([ \t]*(?:#.*)?)$',text))
        if len(matches)!=1:raise ValueError('invalid_config')
        try:value=float(matches[0].group(2))
        except ValueError:raise ValueError('invalid_config') from None
        if not math.isfinite(value) or not .1<=value<=3:raise ValueError('invalid_config')
        fields[name]=(matches[0],value)
    return data,text,fields


def fit(path,motion,records):
    """Fit at least three explicitly selected raw-command trials.

    한글: 사용자가 선택한 보정 전 명령 적분 시험 3개 이상으로 계산한다.
    """
    if motion not in ('forward','lateral','rotation') or not 3<=len(records)<=10:raise ValueError('invalid_trials')
    data,_,fields=_read(path)
    x=[];y=[]
    for item in records:
        r=item.get('result',{})
        if item.get('kind')!='odometry' or r.get('motion')!=motion or r.get('source')!='command' or r.get('method')!='manual_single_trial_comparison':
            raise ValueError('invalid_trials')
        a,b=r.get('recorded'),r.get('reference')
        if (any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (a,b))
                or abs(a)<1 or abs(b)<1 or a*b<=0):raise ValueError('invalid_trials')
        x.append(a);y.append(b)
    factor=sum(a*b for a,b in zip(x,y))/sum(a*a for a in x)
    name={'forward':'odom_linear_scale','lateral':'odom_lateral_scale','rotation':'odom_angular_scale'}[motion]
    proposed=factor/(fields['odom_linear_scale'][1] if motion=='lateral' else 1)
    if not .5<=proposed<=1.5:raise ValueError('invalid_scale')
    residuals=[factor*a-b for a,b in zip(x,y)]
    return {'motion':motion,'parameter':name,'current':fields[name][1],'candidate':proposed,
            'trial_count':len(records),'rms':math.sqrt(sum(r*r for r in residuals)/len(residuals)),
            'unit':'deg' if motion=='rotation' else 'cm','config_hash':shared._hash(data),
            'baseline_scales':{name:fields[name][1] for name in _NAMES}, 'method':'raw_command_least_squares',
            'applied':False,'independent_validation':False}


def preview(path,candidate):
    """Verify the candidate against all current odometry scale parameters.

    한글: 현재 모든 오도메트리 배율이 후보의 기준과 같은지 확인한다.
    """
    data,_,fields=_read(path)
    if not isinstance(candidate,dict) or candidate.get('applied') is not False or candidate.get('method')!='raw_command_least_squares':raise ValueError('candidate_unavailable')
    name=candidate.get('parameter');target=candidate.get('candidate');baseline=candidate.get('baseline_scales')
    if name not in _NAMES or isinstance(target,bool) or not isinstance(target,(int,float)) or not math.isfinite(target) or not .5<=target<=1.5 or not isinstance(baseline,dict):raise ValueError('invalid_scale')
    if any(isinstance(baseline.get(key),bool) or not isinstance(baseline.get(key),(int,float)) or not math.isfinite(baseline[key]) or abs(fields[key][1]-baseline[key])>1e-9 for key in _NAMES):raise ValueError('odom_settings_changed')
    review={'parameter':name,'candidate':target,'baseline_scales':baseline}
    return {**review,'current':fields[name][1],'config_hash':shared._hash(data),
            'candidate_hash':shared._hash(json.dumps(review,sort_keys=True).encode()),'requires_restart':True}


def apply(path,storage,candidate,config_hash,candidate_hash):
    """Update only the reviewed scale with backup; never send motion.

    한글: 구동 명령 없이 검토한 배율만 백업 후 변경한다.
    """
    plan=preview(path,candidate);data,text,fields=_read(path)
    if plan['candidate_hash']!=candidate_hash:raise ValueError('candidate_changed')
    if plan['config_hash']!=config_hash or shared._hash(data)!=config_hash:raise ValueError('config_changed')
    m=fields[plan['parameter']][0]
    result=(text[:m.start()]+m.group(1)+format(plan['candidate'],'.9g')+m.group(3)+text[m.end():]).encode()
    storage.mkdir(mode=0o700,parents=True,exist_ok=True);backup_id=uuid.uuid4().hex
    record={'id':backup_id,'previous_base64':base64.b64encode(data).decode(),'before_hash':shared._hash(data),'after_hash':shared._hash(result)}
    fd=os.open(storage/(backup_id+'.json'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as out:json.dump(record,out);out.flush();os.fsync(out.fileno())
    if shared._hash(path.read_bytes())!=config_hash:raise ValueError('config_changed')
    shared._atomic(path,result,stat.S_IMODE(path.stat().st_mode))
    return {'backup_id':backup_id,'requires_restart':True}
