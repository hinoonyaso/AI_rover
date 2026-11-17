"""Review and install color CameraInfo override with guarded backup.

한글: 컬러 CameraInfo 재정의 설정을 검토하고 안전 백업 후 설치한다.
"""
import base64
import json
import math
import os
from pathlib import Path
import re
import stat
import uuid
import gyro_settings as shared


def _configuration(path):
    if path.is_symlink() or not path.is_file():raise ValueError('config_unavailable')
    data=path.read_bytes()
    if len(data)>1_000_000:raise ValueError('invalid_config')
    text=data.decode('utf-8')
    if not re.search(r'(?m)^/\*\*:[ \t]*$',text) or not re.search(r'(?m)^  ros__parameters:[ \t]*$',text):
        raise ValueError('invalid_config')
    matches=list(re.finditer(r'(?m)^[ \t]*color_info_url[ \t]*:[^\n]*$',text))
    anchors=list(re.finditer(r'(?m)^    enable_color[ \t]*:[ \t]*true[ \t]*(?:#.*)?$',text))
    if len(matches)>1 or len(anchors)!=1:raise ValueError('invalid_config')
    return data,text,matches,anchors[0]


def _candidate(candidate, info):
    if not isinstance(candidate,dict) or candidate.get('applied') is not False:raise ValueError('candidate_unavailable')
    width,height=candidate.get('width'),candidate.get('height')
    if (not isinstance(width,int) or isinstance(width,bool) or not isinstance(height,int) or isinstance(height,bool)
            or not 0<width<=10000 or not 0<height<=10000):raise ValueError('invalid_camera_candidate')
    if not isinstance(info,dict) or (info.get('width'),info.get('height'))!=(width,height):raise ValueError('camera_resolution_mismatch')
    matrix=candidate.get('camera_matrix');d=candidate.get('distortion')
    if not isinstance(matrix,list) or len(matrix)!=3 or any(not isinstance(row,list) or len(row)!=3 for row in matrix):raise ValueError('invalid_camera_candidate')
    if not isinstance(d,list) or len(d)!=5:raise ValueError('invalid_camera_candidate')
    values=sum(matrix,[])+d
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v)>1e6 for v in values):raise ValueError('invalid_camera_candidate')
    if matrix[0][0]<=0 or matrix[1][1]<=0 or abs(matrix[2][2]-1)>1e-6:raise ValueError('invalid_camera_candidate')
    return {'width':width,'height':height,'matrix':matrix,'distortion':d}


def preview(path,candidate,info):
    """Confirm resolution and compute review hashes. / 해상도와 검토 해시를 확인한다."""
    data,_,_,_=_configuration(path);values=_candidate(candidate,info)
    return {**values,'config_hash':shared._hash(data),
            'candidate_hash':shared._hash(json.dumps(values,sort_keys=True).encode()),'requires_restart':True}


def _yaml(values):
    k=values['matrix'];d=values['distortion'];width=values['width'];height=values['height']
    def row(v):return '['+', '.join(format(x,'.12g') for x in v)+']'
    return ('image_width: '+str(width)+'\nimage_height: '+str(height)+'\ncamera_name: depth_cam_color\n'
            'camera_matrix:\n  rows: 3\n  cols: 3\n  data: '+row(sum(k,[]))+'\n'
            'distortion_model: plumb_bob\ndistortion_coefficients:\n  rows: 1\n  cols: 5\n  data: '+row(d)+'\n'
            'rectification_matrix:\n  rows: 3\n  cols: 3\n  data: [1, 0, 0, 0, 1, 0, 0, 0, 1]\n'
            'projection_matrix:\n  rows: 3\n  cols: 4\n  data: '+row([k[0][0],k[0][1],k[0][2],0,k[1][0],k[1][1],k[1][2],0,0,0,1,0])+'\n').encode()


def apply(path,storage,candidate,info,config_hash,candidate_hash):
    """Create a versioned calibration file and atomically switch configuration.

    한글: 버전별 보정 파일 생성 후 설정을 원자적으로 전환한다.
    """
    plan=preview(path,candidate,info);data,text,matches,anchor=_configuration(path)
    if plan['candidate_hash']!=candidate_hash:raise ValueError('candidate_changed')
    if plan['config_hash']!=config_hash or shared._hash(data)!=config_hash:raise ValueError('config_changed')
    storage.mkdir(mode=0o700,parents=True,exist_ok=True)
    backup_id=uuid.uuid4().hex
    calibration=storage/('color-'+backup_id+'.yaml')
    line='    color_info_url: "'+calibration.as_uri()+'"'
    updated=(text[:matches[0].start()]+line+text[matches[0].end():]) if matches else (text[:anchor.end()]+'\n'+line+text[anchor.end():])
    encoded=updated.encode('utf-8')
    record={'id':backup_id,'previous_base64':base64.b64encode(data).decode('ascii'),
            'before_hash':shared._hash(data),'after_hash':shared._hash(encoded)}
    for target, content in ((calibration,_yaml(plan)),(storage/(backup_id+'.json'),json.dumps(record).encode())):
        fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'wb') as out:out.write(content);out.flush();os.fsync(out.fileno())
    if shared._hash(path.read_bytes())!=config_hash:raise ValueError('config_changed')
    shared._atomic(path,encoded,stat.S_IMODE(path.stat().st_mode))
    return {'backup_id':backup_id,'requires_restart':True}


def restore(path,storage,backup_id):
    """Restore exact prior driver configuration only when unchanged.

    한글: 드라이버 설정이 변경되지 않은 경우에만 이전 파일을 복원한다.
    """
    if not re.fullmatch('[0-9a-f]{32}',backup_id):raise ValueError('invalid_backup')
    backup=storage/(backup_id+'.json')
    if backup.is_symlink() or not backup.is_file():raise ValueError('invalid_backup')
    record=json.loads(backup.read_text());previous=base64.b64decode(record['previous_base64'],validate=True)
    if record.get('id')!=backup_id or shared._hash(previous)!=record.get('before_hash'):raise ValueError('invalid_backup')
    data,_,_,_=_configuration(path)
    if shared._hash(data)!=record.get('after_hash'):raise ValueError('config_changed')
    shared._atomic(path,previous,stat.S_IMODE(path.stat().st_mode))
    return {'restored':True,'requires_restart':True}
