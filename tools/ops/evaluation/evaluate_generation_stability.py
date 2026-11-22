#!/usr/bin/env python3
"""Measure repeated local generation while observing real sensors and services.

한글: 실제 센서·서비스를 관찰하면서 로컬 생성 반복의 자원 부하를 측정한다.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import ssl
import subprocess
import sys
import time
from urllib.request import HTTPSHandler, ProxyHandler, build_opener

import psutil
import pymysql

ROOT = Path.home() / '.local/share/jetinspect-ops'
BACKEND = Path(__file__).resolve().parents[1] / 'backend'
CHILD = """import json,sys
sys.path.insert(0,sys.argv[1])
from knowledge import Knowledge
items=json.load(open(sys.argv[2],encoding='utf-8'))
x=items[int(sys.argv[3])%len(items)]
answer=Knowledge.__new__(Knowledge).answer(x['query'],x['results'],'generated')
if not answer.strip(): raise SystemExit(3)
"""


def main():
    """Measure bounded generation and save a private result. / 제한된 생성 시험을 수행하고 개인 결과를 저장한다."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=600)
    parser.add_argument('--url', default='https://172.30.1.82:8765/')
    parser.add_argument('--ca-file', type=Path, default=ROOT / 'tls/dashboard.crt')
    args = parser.parse_args()
    if not 60 <= args.seconds <= 3600:
        parser.error('seconds must be between 60 and 3600')
    if args.output.exists() or args.output.is_symlink():
        parser.error('output already exists')
    inputs = json.loads(args.inputs.read_text(encoding='utf-8'))
    if not isinstance(inputs, list) or not inputs or any(not x.get('results') for x in inputs):
        parser.error('no usable input evidence')
    context = ssl.create_default_context(cafile=str(args.ca_file))
    opener = build_opener(ProxyHandler({}), HTTPSHandler(context=context))
    start = time.monotonic(); end = start + args.seconds
    runs, samples = [], []
    child = None; child_started = 0.; reason = None; next_check = start; next_report = start + 60
    psutil.cpu_percent(interval=None)
    try:
        while time.monotonic() < end:
            now = time.monotonic(); memory = psutil.virtual_memory()
            if child is None:
                if memory.available < 3 * 1024**3:
                    reason = 'insufficient_memory_to_start_generation'; break
                child = subprocess.Popen([sys.executable, '-c', CHILD, str(BACKEND), str(args.inputs), str(len(runs))],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                child_started = now
            if child.poll() is not None:
                runs.append({'seconds': round(now-child_started, 2), 'exit_code': child.returncode})
                if child.returncode != 0:
                    reason = 'generation_failed'; child = None; break
                child = None
            record = {'elapsed': round(now-start, 1), 'available_gib': round(memory.available/1024**3, 3),
                      'swap_used_gib': round(psutil.swap_memory().used/1024**3, 3),
                      'cpu_percent': psutil.cpu_percent(interval=None)}
            try:
                data = json.loads((ROOT / 'run/ros-status.json').read_text())
                ts = time.time(); record['snapshot_age'] = round(ts-data['timestamp'], 2)
                record['battery_v'] = data.get('battery_voltage')
                bat_at = data.get('battery_received_at')
                record['battery_age'] = round(ts-bat_at, 2) if isinstance(bat_at, (int,float)) else None
                record['streams'] = {k: {'hz':v.get('hz'), 'age':round(ts-v['received_at'],2) if v.get('received_at') else None}
                                     for k,v in data.get('streams',{}).items()}
            except (OSError,ValueError,KeyError,TypeError):
                record['sensor_error'] = True
            if now >= next_check:
                try:
                    db = pymysql.connect(unix_socket=str(ROOT/'mysql-run/mysql.sock'),user='root',database='jetinspect',connect_timeout=2)
                    with db.cursor() as cursor:cursor.execute('SELECT 1');cursor.fetchone()
                    db.close();record['database'] = 'connected'
                except pymysql.MySQLError:record['database'] = 'unavailable'
                try:
                    with opener.open(args.url,timeout=4) as response:record['https'] = response.status
                except Exception:record['https'] = 'error'
                next_check = now + 10
            samples.append(record)
            if memory.available < 1.25*1024**3:
                reason = 'memory_safety_limit'; break
            if record.get('battery_v') is not None and record['battery_v'] < 10:
                reason = 'battery_below_10V'; break
            if record.get('battery_age') is None or record['battery_age'] < 0 or record['battery_age'] >= 15:
                reason = 'battery_measurement_unavailable'; break
            if child is not None and now-child_started > 180:
                reason = 'generation_timeout'; break
            if now >= next_report:
                print(f'elapsed={round(now-start)}s, completed={len(runs)}, battery={record["battery_v"]:.2f}V, free={record["available_gib"]:.2f}GiB',flush=True)
                next_report += 60
            time.sleep(2)
    finally:
        if child is not None and child.poll() is None:
            os.killpg(child.pid,signal.SIGKILL);child.wait()
            runs.append({'seconds':round(time.monotonic()-child_started,2),'exit_code':child.returncode,'interrupted':True})
        summary = {'requested_seconds':args.seconds,'observed_seconds':round(time.monotonic()-start,1),'stop_reason':reason,
                   'runs':runs,'samples':samples,'completed_at':datetime.now(timezone.utc).isoformat()}
        args.output.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        fd=os.open(args.output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w',encoding='utf-8') as out:json.dump(summary,out,ensure_ascii=False,indent=2)
        print('saved',args.output,'reason',reason,'runs',len(runs),flush=True)


if __name__ == '__main__':
    main()
