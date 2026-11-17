"""Review installed end-effector position derived from a pivot TCP candidate.

한글: 접점 TCP 후보로 설치된 엔드이펙터 위치를 검토한다.
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


def _vec(value):
    try: v=[float(x) for x in value.split()]
    except (ValueError,AttributeError):raise ValueError('invalid_config') from None
    if len(v)!=3 or not all(math.isfinite(x) for x in v):raise ValueError('invalid_config')
    return v


def _rotate(v,rpy):
    roll,pitch,yaw=rpy; cr,sr=math.cos(roll),math.sin(roll);cp,sp=math.cos(pitch),math.sin(pitch);cy,sy=math.cos(yaw),math.sin(yaw)
    x,y,z=v
    return [(cy*cp)*x+(cy*sp*sr-sy*cr)*y+(cy*sp*cr+sy*sr)*z,
            (sy*cp)*x+(sy*sp*sr+cy*cr)*y+(sy*sp*cr-cy*sr)*z,
            -sp*x+cp*sr*y+cp*cr*z]


def _read(path):
    if path.is_symlink() or not path.is_file():raise ValueError('config_unavailable')
    data=path.read_bytes()
    if len(data)>2_000_000:raise ValueError('invalid_config')
    text=data.decode('utf-8')
    try:
        tree=ET.fromstring(text)
        def joint(name,parent,child):
            found=[j for j in tree.findall('joint') if j.get('name')==name]
            if len(found)!=1 or found[0].get('type')!='fixed' or found[0].find('parent').get('link')!=parent or found[0].find('child').get('link')!=child:raise ValueError()
            origin=found[0].find('origin')
            return _vec(origin.get('xyz')),_vec(origin.get('rpy'))
        gripper_xyz,gripper_rpy=joint('gripper_joint','link5','gripper_link')
        current,rpy=joint('end_effector_joint','link5','end_effector_link')
    except (ET.ParseError,AttributeError,TypeError,ValueError):raise ValueError('invalid_config') from None
    chunks=list(re.finditer(r'(?s)<joint\b(?=[^>]*\bname\s*=\s*["\']end_effector_joint["\'])[^>]*>.*?</joint\s*>',text))
    if len(chunks)!=1:raise ValueError('invalid_config')
    chunk=chunks[0];origins=list(re.finditer(r'(?s)<origin\b[^>]*\bxyz\s*=\s*["\']([^"\']+)["\'][^>]*?/>',chunk.group()))
    if len(origins)!=1:raise ValueError('invalid_config')
    match=origins[0]
    return data,text,chunk.start()+match.start(1),chunk.start()+match.end(1),gripper_xyz,gripper_rpy,current,rpy


def preview(path,candidate):
    """Convert gripper-frame TCP into the installed link5 frame for review.

    한글: 그리퍼 기준 TCP를 설치된 link5 프레임으로 변환해 검토한다.
    """
    data,_,_,_,origin,rotation,current,rpy=_read(path)
    if not isinstance(candidate,dict) or candidate.get('applied') is not False or candidate.get('parent_frame')!='gripper_link' or candidate.get('reference_frame')!='base_link':raise ValueError('candidate_unavailable')
    tcp=candidate.get('tcp_gripper_m')
    if not isinstance(tcp,list) or len(tcp)!=3 or any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or abs(x)>2 for x in tcp):raise ValueError('invalid_tcp')
    rotated=_rotate(tcp,rotation);target=[a+b for a,b in zip(origin,rotated)]
    if any(abs(x)>2 for x in target):raise ValueError('invalid_tcp')
    review={'tcp_gripper_m':tcp,'target_link5_m':target,'current_link5_m':current,'rotation_rpy':rpy}
    return {**review,'config_hash':shared._hash(data),'candidate_hash':shared._hash(json.dumps(review,sort_keys=True).encode()),'requires_restart':True}


def apply(path,storage,candidate,config_hash,candidate_hash):
    """Update only end_effector_joint xyz with a recoverable backup.

    한글: 복구 백업을 남기고 end_effector_joint 위치만 변경한다.
    """
    plan=preview(path,candidate);data,text,start,end,*_=_read(path)
    if plan['candidate_hash']!=candidate_hash:raise ValueError('candidate_changed')
    if plan['config_hash']!=config_hash or shared._hash(data)!=config_hash:raise ValueError('config_changed')
    result=(text[:start]+' '.join(format(x,'.9g') for x in plan['target_link5_m'])+text[end:]).encode()
    storage.mkdir(mode=0o700,parents=True,exist_ok=True);backup_id=uuid.uuid4().hex
    record={'id':backup_id,'previous_base64':base64.b64encode(data).decode(),'before_hash':shared._hash(data),'after_hash':shared._hash(result)}
    fd=os.open(storage/(backup_id+'.json'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as out:json.dump(record,out);out.flush();os.fsync(out.fileno())
    if shared._hash(path.read_bytes())!=config_hash:raise ValueError('config_changed')
    shared._atomic(path,result,stat.S_IMODE(path.stat().st_mode))
    return {'backup_id':backup_id,'requires_restart':True}


def restore(path,storage,backup_id):
    """Restore a matching installed arm model. / 일치하는 설치 팔 모델을 복원한다."""
    if not re.fullmatch('[0-9a-f]{32}',backup_id):raise ValueError('invalid_backup')
    backup=storage/(backup_id+'.json')
    if backup.is_symlink() or not backup.is_file():raise ValueError('invalid_backup')
    record=json.loads(backup.read_text());previous=base64.b64decode(record['previous_base64'],validate=True)
    if record.get('id')!=backup_id or shared._hash(previous)!=record.get('before_hash'):raise ValueError('invalid_backup')
    data,*_=_read(path)
    if shared._hash(data)!=record.get('after_hash'):raise ValueError('config_changed')
    shared._atomic(path,previous,stat.S_IMODE(path.stat().st_mode))
    return {'restored':True,'requires_restart':True}
