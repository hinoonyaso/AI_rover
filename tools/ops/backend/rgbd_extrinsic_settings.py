"""Review and persist RGB-D reprojection candidates separately from hardware.

한글: 하드웨어 설정과 별도로 RGB-D 투영 후보를 검토·저장한다.
"""
import base64
import json
import math
import os
import re
import uuid
import battery_settings as files
import gyro_settings as shared


def candidate(value):
    """Validate a depth-to-color rigid transform and bounded fit residual.

    한글: 깊이→컬러 강체 변환과 유한한 잔차를 검증한다.
    """
    if not isinstance(value,dict) or value.get('source_frame')!='depth_cam_depth_optical_frame' or value.get('target_frame')!='depth_cam_color_optical_frame' or value.get('applied') is not False:raise ValueError('candidate_unavailable')
    r=value.get('rotation_matrix');t=value.get('translation_m');rms=value.get('rms_m')
    valid=lambda x:isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)
    if not isinstance(r,list) or len(r)!=3 or any(not isinstance(row,list) or len(row)!=3 for row in r) or not isinstance(t,list) or len(t)!=3 or not all(valid(x) for row in r for x in row) or not all(valid(x) and abs(x)<=2 for x in t) or not valid(rms) or not 0<=rms<=.05:raise ValueError('invalid_candidate')
    for i in range(3):
        for j in range(3):
            if abs(sum(r[k][i]*r[k][j] for k in range(3))-(1 if i==j else 0))>1e-4:raise ValueError('invalid_candidate')
    det=r[0][0]*(r[1][1]*r[2][2]-r[1][2]*r[2][1])-r[0][1]*(r[1][0]*r[2][2]-r[1][2]*r[2][0])+r[0][2]*(r[1][0]*r[2][1]-r[1][1]*r[2][0])
    if abs(det-1)>1e-4:raise ValueError('invalid_candidate')
    return {'source_frame':value['source_frame'],'target_frame':value['target_frame'],'rotation_matrix':r,'translation_m':t,'rms_m':rms}


def preview(path,value):
    """Preview candidate and current active-file hash. / 후보와 현재 파일 해시를 확인한다."""
    current=files._read(path);v=candidate(value)
    return {'candidate':v,'config_hash':shared._hash(current or b''),'candidate_hash':shared._hash(json.dumps(v,sort_keys=True).encode())}


def apply(path,storage,value,config_hash,candidate_hash):
    """Back up and activate a candidate for the separate reprojection node.

    한글: 별도 투영 노드에 사용할 후보를 백업 후 활성화한다.
    """
    plan=preview(path,value);current=files._read(path)
    if plan['config_hash']!=config_hash or shared._hash(current or b'')!=config_hash:raise ValueError('config_changed')
    if plan['candidate_hash']!=candidate_hash:raise ValueError('candidate_changed')
    data=json.dumps(plan['candidate'],sort_keys=True,allow_nan=False).encode();path.parent.mkdir(mode=0o700,parents=True,exist_ok=True);storage.mkdir(mode=0o700,parents=True,exist_ok=True);backup_id=uuid.uuid4().hex
    record={'id':backup_id,'previous_base64':base64.b64encode(current).decode() if current is not None else None,'before_hash':shared._hash(current or b''),'after_hash':shared._hash(data)}
    fd=os.open(storage/(backup_id+'.json'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as output:json.dump(record,output);output.flush();os.fsync(output.fileno())
    if shared._hash(files._read(path) or b'')!=config_hash:raise ValueError('config_changed')
    shared._atomic(path,data,0o600);return {'backup_id':backup_id,'topic':'/depth_cam/depth_corrected/image_raw'}


def restore(path,storage,backup_id):
    """Restore a matching previous active candidate. / 일치하는 이전 활성 후보를 복원한다."""
    return files.restore(path,storage,backup_id)
