#!/usr/bin/env python3
"""Measure authenticated HTTPS against live read-only sensors and DB via an isolated server.

한글: 격리 서버와 임시 계정으로 실제 읽기 전용 센서·DB의 HTTPS 부하를 측정한다.
"""
import concurrent.futures, http.client, json, os, pathlib, secrets, ssl, subprocess, sys, tempfile, threading, time, statistics
from collections import Counter
root=pathlib.Path.home()/'.local/share/jetinspect-ops'
backend=pathlib.Path(__file__).resolve().parent/'backend'
sys.path.insert(0,str(backend))
import access_control, psutil
cert=str(root/'tls/dashboard.crt');key=str(root/'tls/dashboard.key')
ctx=ssl.create_default_context(cafile=cert)
password=secrets.token_urlsafe(24);salt=secrets.token_hex(16)
with tempfile.TemporaryDirectory(prefix='jetinspect-load-') as tmp:
 os.chmod(tmp,0o700)
 accounts=pathlib.Path(tmp)/'accounts.json'
 accounts.write_text(json.dumps({'loadviewer':{'role':'viewer','salt':salt,'hash':access_control.password_hash(password,salt)}}));os.chmod(accounts,0o600)
 env=os.environ.copy();env.update(JETINSPECT_LAN_IP='172.30.1.82',JETINSPECT_LAN_CIDR='172.30.1.0/24',TEST_ACCOUNTS=str(accounts),PYTHONPATH=str(backend))
 program="import os,access_control,uvicorn; access_control.ACCOUNTS=os.environ['TEST_ACCOUNTS']; from pathlib import Path; access_control.ACCOUNTS=Path(access_control.ACCOUNTS); uvicorn.run('app:app',host='127.0.0.1',port=18766,ssl_keyfile=os.environ['TEST_KEY'],ssl_certfile=os.environ['TEST_CERT'],lifespan='off',log_level='error',access_log=False)"
 env.update(TEST_KEY=key,TEST_CERT=cert)
 proc=subprocess.Popen([sys.executable,'-c',program],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 host='127.0.0.1:8765';origin='https://'+host
 def request(conn,method,path,body=None,extra=None):
  headers={'Host':host,'Origin':origin};headers.update(extra or {})
  conn.request(method,path,body,headers);r=conn.getresponse();data=r.read();return r,data
 def connection():return http.client.HTTPSConnection('127.0.0.1',18766,context=ctx,timeout=8)
 try:
  for _ in range(40):
   try:
    c=connection();r,_=request(c,'GET','/api/status');c.close()
    if r.status==401:break
   except OSError:time.sleep(.5)
  else:raise RuntimeError('isolated server did not start')
  cookies=[]
  for _ in range(4):
   c=connection();r,_=request(c,'POST','/api/session/login',json.dumps({'username':'loadviewer','password':password}),{'Content-Type':'application/json'});assert r.status==200,r.status;cookies.append(r.getheader('Set-Cookie').split(';',1)[0]);c.close()
  c=connection();r,_=request(c,'POST','/api/sensor-services/lidar/stop',extra={'Cookie':cookies[0]});assert r.status==403,r.status;c.close()
  print('auth: no session 401, four viewer logins 200, write denied 403',flush=True)
  duration=int(os.environ.get('TEST_SECONDS','300'));end=time.monotonic()+duration;barrier=threading.Barrier(5);results=[];lock=threading.Lock();abort=threading.Event()
  def worker(cookie):
   c=connection();local=Counter();lat=[];barrier.wait()
   while time.monotonic()<end and not abort.is_set():
    start=time.monotonic()
    try:
     r,b=request(c,'GET','/api/status',extra={'Cookie':cookie});lat.append(time.monotonic()-start);local['requests']+=1
     if r.status!=200:local['http_error']+=1;continue
     data=json.loads(b)
     if data['database']!='connected':local['db_error']+=1
     voltage=data['robot'].get('battery_voltage')
     if voltage is not None and voltage < 10.0:
      local['battery_abort']+=1;abort.set()
     if data['robot']['status']!='monitoring':local['monitor_error']+=1
     for s in ('imu','scan','camera','depth_obstacles'):
      if data['robot']['streams'][s]['age_seconds'] is None:local[s+'_missing']+=1
    except Exception as exc:
     local['exception']+=1;local[type(exc).__name__]+=1;c.close();c=connection()
    time.sleep(.7)
   c.close()
   with lock:results.append((local,lat))
  samples=[]
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
   fs=[ex.submit(worker,c) for c in cookies];barrier.wait()
   while time.monotonic()<end and not abort.is_set():
    samples.append((psutil.cpu_percent(interval=.1),psutil.virtual_memory().percent,psutil.swap_memory().used))
    time.sleep(min(5,max(0,end-time.monotonic())))
   for f in fs:f.result()
  count=Counter();lat=[]
  for a,b in results:count.update(a);lat+=b
  lat.sort();out={'duration_s_requested':duration,'duration_s_observed':round(duration-max(0,end-time.monotonic()),1),'concurrent_authenticated_viewers':len(cookies),**count,'latency_p95_s':round(lat[int(.95*(len(lat)-1))],3),'cpu_peak_percent':max(x[0] for x in samples),'memory_peak_percent':max(x[1] for x in samples),'swap_peak_mib':round(max(x[2] for x in samples)/1024**2,1)}
  print(json.dumps(out,ensure_ascii=False),flush=True)
 finally:
  proc.terminate()
  try:proc.wait(timeout=10)
  except subprocess.TimeoutExpired:proc.kill();proc.wait()
