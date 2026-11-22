#!/usr/bin/env python3
"""Run five synthetic fixture cases; this is not an independent accuracy benchmark.

합성 시험판 다섯 사례를 평가하며 독립적인 실물 정확도 평가가 아니다.
"""
import cv2,json,numpy as np,tempfile
from pathlib import Path
from evaluate_stack_light_videos import evaluate
R={'red':[0,0,16,16],'yellow':[16,0,16,16],'green':[32,0,16,16]}
def video(path,variant):
 w=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'MJPG'),10,(48,16))
 if not w.isOpened():raise RuntimeError('video writer unavailable')
 for frame in range(10 if variant=='short' else 40):
  t=frame/10; levels=[220,40,220]
  if variant=='blink':levels[2]=220 if t<1 or t>=2 else 40
  if variant=='ambiguous':levels[1]=100
  hsv=np.zeros((16,48,3),np.uint8)
  for i,(hue,val) in enumerate(zip((0,27,60),levels)):hsv[:,i*16:(i+1)*16]=(hue,255,val)
  out=cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR)
  if variant=='occluded':out[:,:16]=0
  w.write(out)
 w.release()
with tempfile.TemporaryDirectory(dir='/tmp') as tmp:
 d=Path(tmp);cases=[]
 expected={'normal':('on','off','on'),'blink':('on','off','blinking'), 'short':('unknown','unknown','unknown'), 'occluded':('unknown','off','on'), 'ambiguous':('on','unknown','on')}
 for key,states in expected.items():
  path=d/(key+'.avi');video(path,key);cases.append({'id':key,'source':'synthetic','video':path.name,'regions':R,'expected':dict(zip(R,states))})
 manifest=d/'cases.json';manifest.write_text(json.dumps({'cases':cases}));out=evaluate(manifest)
 print(json.dumps(out['summary_by_source'],ensure_ascii=False))
 for c in out['cases']:print(c['id'],'expected',c['expected'],'predicted',c.get('predicted'),'error',c.get('error'))
