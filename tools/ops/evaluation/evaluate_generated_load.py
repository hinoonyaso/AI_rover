#!/usr/bin/env python3
"""Measure generated answers while observing ROS monitoring. / 생성 답변과 ROS 관제 상태를 함께 측정한다."""
import json
import os
from pathlib import Path
import threading
import time

import httpx
import psutil

QUESTIONS = [
    'Orbbec DaBai depth 카메라가 SDK v2에서 인식되지 않는 원인은 무엇인가요?',
    '정지 자이로 보정 결과에 기존 gyro_bias는 어떻게 반영하나요?',
]


def main():
    """Issue two sequential generated answers with resource and dashboard samples.

    한글: 생성 답변을 두 번 순차 요청하며 자원과 대시보드 상태를 수집한다.
    """
    url = os.getenv('JETINSPECT_EVAL_URL', 'https://172.30.1.82:8765')
    opts = {'base_url': url, 'verify': False, 'trust_env': False, 'timeout': 190, 'headers': {'Origin': url}}
    samples, answers, stop = [], [], threading.Event()
    with httpx.Client(**opts) as client:
        client.post('/api/session/login', json={'username':'operator','password':os.environ['JETINSPECT_EVAL_PASSWORD']}).raise_for_status()
        def monitor():
            while not stop.is_set():
                record = {'elapsed': round(time.monotonic()-started, 1), 'available_gib': round(psutil.virtual_memory().available / 1024**3, 2),
                          'swap_used_gib': round(psutil.swap_memory().used / 1024**3, 2), 'cpu_percent': psutil.cpu_percent(interval=None)}
                try:
                    response = client.get('/api/status', timeout=5)
                    data = response.json()
                    robot = data.get('robot') or {}
                    record.update(http_status=response.status_code, ros_status=robot.get('status'), snapshot_age=robot.get('snapshot_age_seconds'),
                                  streams={key: value.get('age_seconds') for key,value in robot.get('streams',{}).items()})
                except Exception as exc:
                    record['error'] = type(exc).__name__
                samples.append(record)
                stop.wait(3)
        started = time.monotonic()
        thread = threading.Thread(target=monitor, daemon=True); thread.start()
        try:
            for question in QUESTIONS:
                start = time.monotonic()
                try:
                    result = client.get('/api/knowledge/answer', params={'q':question, 'mode':'generated'})
                    data = result.json()
                    answers.append({'question':question, 'status':result.status_code, 'seconds':round(time.monotonic()-start,1),
                                    'answer':data.get('answer'), 'error':data.get('error'), 'sources':data.get('results',[])})
                except Exception as exc:
                    answers.append({'question':question, 'error':type(exc).__name__, 'seconds':round(time.monotonic()-start,1)})
        finally:
            stop.set(); thread.join(timeout=8); client.post('/api/session/logout')
    print(json.dumps({'answers':answers, 'samples':samples}, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
