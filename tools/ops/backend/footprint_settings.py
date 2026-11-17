"""Safely review and version the default installed Nav2 footprint.

한글: 설치된 기본 Nav2 외형을 안전하게 검토하고 버전 관리한다.
"""
import ast
import base64
import json
import math
import os
import re
import stat
import uuid
import gyro_settings as shared


def _read(path):
    if path.is_symlink() or not path.is_file():raise ValueError('config_unavailable')
    data=path.read_bytes()
    if len(data)>2_000_000:raise ValueError('invalid_config')
    text=data.decode('utf-8');matches=[]
    for name in ('global_costmap','local_costmap'):
        section=re.search(r'(?ms)^'+name+r':\s*\n(.*?)(?=^\S|\Z)',text)
        if not section:raise ValueError('invalid_config')
        fields=list(re.finditer(r'(?m)^([ \t]*footprint:[ \t]*)["\'](\[.*\])["\']([ \t]*(?:#.*)?)$',section.group()))
        if len(fields)!=1:raise ValueError('invalid_config')
        m=fields[0]
        try:points=ast.literal_eval(m.group(2))
        except (ValueError,SyntaxError):raise ValueError('invalid_config') from None
        if (not isinstance(points,list) or len(points)<3 or len(points)>100 or
            any(not isinstance(p,(list,tuple)) or len(p)!=2 or any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in p) for p in points)):
            raise ValueError('invalid_config')
        matches.append((section.start()+m.start(),section.start()+m.end(),m.group(1),m.group(3),points))
    return data,text,matches


def preview(path,candidate):
    """Allow only measured rectangles that contain both current footprints.

    한글: 현재 두 외형을 모두 포함하는 실측 사각형만 적용 가능하게 한다.
    """
    data,text,matches=_read(path)
    if not isinstance(candidate,dict) or candidate.get('applied') is not False or candidate.get('frame_id')!='base_footprint':
        raise ValueError('candidate_unavailable')
    points=candidate.get('polygon_m')
    if (not isinstance(points,list) or len(points)!=4 or
        any(not isinstance(p,list) or len(p)!=2 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v)>3 for v in p) for p in points)):
        raise ValueError('invalid_footprint')
    xs=[p[0] for p in points];ys=[p[1] for p in points]
    expected=[[max(xs),max(ys)],[max(xs),min(ys)],[min(xs),min(ys)],[min(xs),max(ys)]]
    if points!=expected or min(xs)>=0 or max(xs)<=0 or min(ys)>=0 or max(ys)<=0:
        raise ValueError('invalid_footprint')
    if any(not min(xs)<=x<=max(xs) or not min(ys)<=y<=max(ys) for *_,old in matches for x,y in old):
        raise ValueError('footprint_shrinks')
    return {'polygon_m':points,'current_footprints':[m[4] for m in matches],'config_hash':shared._hash(data),
            'candidate_hash':shared._hash(json.dumps(points).encode()),'requires_restart':True}


def apply(path,storage,candidate,config_hash,candidate_hash):
    """Back up and update both costmaps, without changing padding.

    한글: 여유값은 유지하고 두 비용지도의 외형을 백업 후 수정한다.
    """
    plan=preview(path,candidate);data,text,matches=_read(path)
    if plan['candidate_hash']!=candidate_hash:raise ValueError('candidate_changed')
    if plan['config_hash']!=config_hash or shared._hash(data)!=config_hash:raise ValueError('config_changed')
    value=json.dumps(plan['polygon_m'],separators=(',',':'))
    for start,end,prefix,suffix,_ in sorted(matches,reverse=True):text=text[:start]+prefix+'"'+value+'"'+suffix+text[end:]
    result=text.encode();storage.mkdir(mode=0o700,parents=True,exist_ok=True);backup_id=uuid.uuid4().hex
    record={'id':backup_id,'previous_base64':base64.b64encode(data).decode(), 'before_hash':shared._hash(data),'after_hash':shared._hash(result)}
    fd=os.open(storage/(backup_id+'.json'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as out:json.dump(record,out);out.flush();os.fsync(out.fileno())
    if shared._hash(path.read_bytes())!=config_hash:raise ValueError('config_changed')
    shared._atomic(path,result,stat.S_IMODE(path.stat().st_mode))
    return {'backup_id':backup_id,'requires_restart':True}


def restore(path,storage,backup_id):
    """Restore only an unchanged result, preserving later operator changes.

    한글: 이후 작업으로 변경되지 않은 결과에만 이전 설정을 복원한다.
    """
    if not re.fullmatch('[0-9a-f]{32}',backup_id):raise ValueError('invalid_backup')
    backup=storage/(backup_id+'.json')
    if backup.is_symlink() or not backup.is_file():raise ValueError('invalid_backup')
    record=json.loads(backup.read_text());previous=base64.b64decode(record['previous_base64'],validate=True)
    if record.get('id')!=backup_id or shared._hash(previous)!=record.get('before_hash'):raise ValueError('invalid_backup')
    data,_,_=_read(path)
    if shared._hash(data)!=record.get('after_hash'):raise ValueError('config_changed')
    shared._atomic(path,previous,stat.S_IMODE(path.stat().st_mode))
    return {'restored':True,'requires_restart':True}
