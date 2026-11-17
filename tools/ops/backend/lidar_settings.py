"""Guard the installed lidar_link translation without changing its rotation.

한글: 회전을 바꾸지 않고 설치된 lidar_link 위치만 안전하게 관리한다.
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


def _read(path):
    if path.is_symlink() or not path.is_file():raise ValueError('config_unavailable')
    data=path.read_bytes()
    if len(data)>1_000_000:raise ValueError('invalid_config')
    text=data.decode('utf-8')
    try:
        tree=ET.fromstring(text)
        joints=[j for j in tree.findall('joint') if j.get('name')=='lidar_joint']
        if len(joints)!=1:raise ValueError()
        joint=joints[0]
        if joint.find('parent').get('link')!='base_link' or joint.find('child').get('link')!='lidar_link':raise ValueError()
        origin=joint.find('origin');xyz=[float(x) for x in origin.get('xyz').split()];rpy=origin.get('rpy')
        if len(xyz)!=3 or any(not math.isfinite(x) for x in xyz) or not rpy:raise ValueError()
    except (ET.ParseError,AttributeError,ValueError,TypeError):raise ValueError('invalid_config') from None
    chunks=list(re.finditer(r'(?s)<joint\b(?=[^>]*\bname\s*=\s*["\']lidar_joint["\'])[^>]*>.*?</joint\s*>',text))
    if len(chunks)!=1:raise ValueError('invalid_config')
    chunk=chunks[0]
    origins=list(re.finditer(r'(?s)<origin\b[^>]*\bxyz\s*=\s*["\']([^"\']+)["\'][^>]*?/>',chunk.group()))
    if len(origins)!=1:raise ValueError('invalid_config')
    match=origins[0]
    return data,text,chunk.start()+match.start(1),chunk.start()+match.end(1),xyz,rpy


def preview(path,candidate):
    """Validate manually measured position and capture review hashes.

    한글: 수동 측정 위치와 검토 해시를 확인한다.
    """
    data,_,_,_,current,rpy=_read(path)
    if not isinstance(candidate,dict) or candidate.get('applied') is not False or candidate.get('parent_frame')!='base_link' or candidate.get('child_frame')!='lidar_link':
        raise ValueError('candidate_unavailable')
    values=candidate.get('translation_m')
    if (not isinstance(values,list) or len(values)!=3 or
        any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v)>3 for v in values)):
        raise ValueError('invalid_position')
    return {'current_m':current,'candidate_m':values,'rotation_rpy':rpy,'config_hash':shared._hash(data),
            'candidate_hash':shared._hash(json.dumps(values).encode()),'requires_restart':True}


def apply(path,storage,candidate,config_hash,candidate_hash):
    """Back up and update only lidar_joint xyz; never change scan rotation.

    한글: lidar_joint 위치만 백업 후 바꾸고 스캔 회전은 변경하지 않는다.
    """
    plan=preview(path,candidate);data,text,start,end,_,_=_read(path)
    if plan['candidate_hash']!=candidate_hash:raise ValueError('candidate_changed')
    if plan['config_hash']!=config_hash or shared._hash(data)!=config_hash:raise ValueError('config_changed')
    result=(text[:start]+' '.join(format(v,'.9g') for v in plan['candidate_m'])+text[end:]).encode()
    storage.mkdir(mode=0o700,parents=True,exist_ok=True);backup_id=uuid.uuid4().hex
    record={'id':backup_id,'previous_base64':base64.b64encode(data).decode(),'before_hash':shared._hash(data),'after_hash':shared._hash(result)}
    fd=os.open(storage/(backup_id+'.json'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as out:json.dump(record,out);out.flush();os.fsync(out.fileno())
    if shared._hash(path.read_bytes())!=config_hash:raise ValueError('config_changed')
    shared._atomic(path,result,stat.S_IMODE(path.stat().st_mode))
    return {'backup_id':backup_id,'requires_restart':True}


def restore(path,storage,backup_id):
    """Restore only an unchanged installed file. / 변경되지 않은 설치 파일만 복원한다."""
    if not re.fullmatch('[0-9a-f]{32}',backup_id):raise ValueError('invalid_backup')
    backup=storage/(backup_id+'.json')
    if backup.is_symlink() or not backup.is_file():raise ValueError('invalid_backup')
    record=json.loads(backup.read_text());previous=base64.b64decode(record['previous_base64'],validate=True)
    if record.get('id')!=backup_id or shared._hash(previous)!=record.get('before_hash'):raise ValueError('invalid_backup')
    data,*_=_read(path)
    if shared._hash(data)!=record.get('after_hash'):raise ValueError('config_changed')
    shared._atomic(path,previous,stat.S_IMODE(path.stat().st_mode))
    return {'restored':True,'requires_restart':True}


def _yaw_fields(path):
    """Read the numeric planar mounting rotation without changing scan-frame rotation.

    한글: 스캔 프레임 회전을 바꾸지 않고 평면 장착 회전을 읽는다.
    """
    data,text,_,_,xyz,rpy=_read(path)
    try:
        angles=[float(value) for value in rpy.split()]
        if len(angles)!=3 or not all(math.isfinite(value) for value in angles) or abs(angles[0])>1e-8 or abs(angles[1])>1e-8:raise ValueError()
    except (ValueError,AttributeError):raise ValueError('invalid_config') from None
    chunks=list(re.finditer(r'(?s)<joint\b(?=[^>]*\bname\s*=\s*["\']lidar_joint["\'])[^>]*>.*?</joint\s*>',text))
    origins=list(re.finditer(r'(?s)<origin\b[^>]*?/>',chunks[0].group()))
    if len(origins)!=1:raise ValueError('invalid_config')
    field=list(re.finditer(r'\brpy\s*=\s*["\']([^"\']+)["\']',origins[0].group()))
    if len(field)!=1:raise ValueError('invalid_config')
    offset=chunks[0].start()+origins[0].start()
    return data,text,offset+field[0].start(1),offset+field[0].end(1),xyz,angles


def preview_yaw(path,candidate):
    """Review a user-measured base-to-lidar mounting yaw.

    한글: 사용자가 실측한 베이스-라이다 장착 yaw를 검토한다.
    """
    data,_,_,_,xyz,angles=_yaw_fields(path)
    if not isinstance(candidate,dict) or candidate.get('applied') is not False or candidate.get('parent_frame')!='base_link' or candidate.get('child_frame')!='lidar_link':raise ValueError('candidate_unavailable')
    yaw=candidate.get('yaw_deg')
    if isinstance(yaw,bool) or not isinstance(yaw,(int,float)) or not math.isfinite(yaw) or abs(yaw)>180:raise ValueError('invalid_yaw')
    current=math.degrees(angles[2]);difference=(yaw-current+180)%360-180
    if abs(difference)>30:raise ValueError('yaw_change_too_large')
    review={'current_deg':current,'candidate_deg':yaw,'difference_deg':difference,'position_m':xyz}
    return {**review,'config_hash':shared._hash(data),'candidate_hash':shared._hash(json.dumps(review,sort_keys=True).encode()),'requires_restart':True}


def apply_yaw(path,storage,candidate,config_hash,candidate_hash):
    """Back up and modify only the planar lidar_joint mounting yaw.

    한글: 백업 후 lidar_joint의 평면 장착 yaw만 변경한다.
    """
    plan=preview_yaw(path,candidate);data,text,start,end,_,_=_yaw_fields(path)
    if plan['candidate_hash']!=candidate_hash:raise ValueError('candidate_changed')
    if plan['config_hash']!=config_hash or shared._hash(data)!=config_hash:raise ValueError('config_changed')
    result=(text[:start]+'0 0 '+format(math.radians(plan['candidate_deg']),'.12g')+text[end:]).encode()
    storage.mkdir(mode=0o700,parents=True,exist_ok=True);backup_id=uuid.uuid4().hex
    record={'id':backup_id,'previous_base64':base64.b64encode(data).decode(),'before_hash':shared._hash(data),'after_hash':shared._hash(result)}
    fd=os.open(storage/(backup_id+'.json'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as out:json.dump(record,out);out.flush();os.fsync(out.fileno())
    if shared._hash(path.read_bytes())!=config_hash:raise ValueError('config_changed')
    shared._atomic(path,result,stat.S_IMODE(path.stat().st_mode))
    return {'backup_id':backup_id,'requires_restart':True}
