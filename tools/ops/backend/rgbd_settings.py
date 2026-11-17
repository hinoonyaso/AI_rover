"""Review and persist the camera startup registration mode.

한글: 카메라 시작 정합 모드를 검토하고 저장한다.
"""
import base64
import json
import os
import re
import stat
import uuid
import gyro_settings as shared


def _read(path):
    if path.is_symlink() or not path.is_file(): raise ValueError('config_unavailable')
    data=path.read_bytes()
    if len(data)>1_000_000: raise ValueError('invalid_config')
    text=data.decode('utf-8')
    if not re.search(r'(?m)^/\*\*:\s*$',text) or not re.search(r'(?m)^  ros__parameters:\s*$',text): raise ValueError('invalid_config')
    fields={}
    for key in ('depth_registration','align_mode','align_target_stream'):
        matches=list(re.finditer(r'(?m)^(    '+key+r':[ \t]*)([^#\n]*?)([ \t]*(?:#.*)?)$',text))
        if len(matches)>1 or (key!='align_target_stream' and len(matches)!=1): raise ValueError('invalid_config')
        if matches: fields[key]=matches[0]
    registration=fields['depth_registration'].group(2).strip().lower()
    mode=fields['align_mode'].group(2).strip().strip('"\'').upper()
    target=fields['align_target_stream'].group(2).strip().strip('"\'').upper() if 'align_target_stream' in fields else 'COLOR'
    if registration not in ('true','false') or mode not in ('HW','SW') or target not in ('COLOR','DEPTH'):raise ValueError('invalid_config')
    current='OFF' if registration=='false' else ('HW_D2C' if mode=='HW' else ('SW_D2C' if target=='COLOR' else 'SW_C2D'))
    return data,text,fields,current


def preview(path,mode):
    """Describe the pending mode and hash the installed settings.

    한글: 적용할 모드와 설치 설정의 해시를 반환한다.
    """
    data,_,_,current=_read(path)
    if mode not in ('OFF','HW_D2C','SW_D2C'):raise ValueError('invalid_registration_mode')
    return {'current':current,'candidate':mode,'config_hash':shared._hash(data),
            'candidate_hash':shared._hash(mode.encode()),'requires_restart':True}


def apply(path,storage,mode,config_hash,candidate_hash):
    """Back up the installed camera configuration and change only registration.

    한글: 카메라 설치 설정을 백업하고 정합 설정만 변경한다.
    """
    plan=preview(path,mode);data,text,fields,_=_read(path)
    if plan['config_hash']!=config_hash or shared._hash(data)!=config_hash:raise ValueError('config_changed')
    if plan['candidate_hash']!=candidate_hash:raise ValueError('candidate_changed')
    values={'depth_registration':'false' if mode=='OFF' else 'true','align_mode':'SW' if mode=='SW_D2C' else 'HW','align_target_stream':'COLOR'}
    for key,match in sorted(fields.items(),key=lambda item:item[1].start(),reverse=True):
        text=text[:match.start(2)]+values[key]+text[match.end(2):]
    if 'align_target_stream' not in fields:
        anchor=list(re.finditer(r'(?m)^    align_mode:.*$',text))
        if len(anchor)!=1:raise ValueError('invalid_config')
        pos=anchor[0].end();text=text[:pos]+'\n    align_target_stream: COLOR'+text[pos:]
    result=text.encode();storage.mkdir(mode=0o700,parents=True,exist_ok=True);backup_id=uuid.uuid4().hex
    record={'id':backup_id,'previous_base64':base64.b64encode(data).decode(),'before_hash':shared._hash(data),'after_hash':shared._hash(result)}
    fd=os.open(storage/(backup_id+'.json'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as out:json.dump(record,out);out.flush();os.fsync(out.fileno())
    if shared._hash(path.read_bytes())!=config_hash:raise ValueError('config_changed')
    shared._atomic(path,result,stat.S_IMODE(path.stat().st_mode))
    return {'backup_id':backup_id,'requires_restart':True}


def restore(path,storage,backup_id):
    """Restore a backup only if the applied file is unchanged.

    한글: 적용된 파일이 바뀌지 않았을 때만 백업을 복원한다.
    """
    if not re.fullmatch('[0-9a-f]{32}',backup_id):raise ValueError('invalid_backup')
    backup=storage/(backup_id+'.json')
    if backup.is_symlink() or not backup.is_file():raise ValueError('invalid_backup')
    record=json.loads(backup.read_text());previous=base64.b64decode(record['previous_base64'],validate=True)
    if record.get('id')!=backup_id or shared._hash(previous)!=record.get('before_hash'):raise ValueError('invalid_backup')
    data,*_=_read(path)
    if shared._hash(data)!=record.get('after_hash'):raise ValueError('config_changed')
    shared._atomic(path,previous,stat.S_IMODE(path.stat().st_mode))
    return {'restored':True,'requires_restart':True}
