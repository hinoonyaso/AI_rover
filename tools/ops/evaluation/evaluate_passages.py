#!/usr/bin/env python3
"""Evaluate source passages and preserve auditable results. / 문단 검색을 평가하고 결과를 기록한다."""
import argparse
import json
import os
from pathlib import Path
import time
import httpx


def main():
    """Check whether answer-bearing text is present in the first three results.

    한글: 기본 답변에 포함되는 상위 세 문단의 정답 근거를 확인한다.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--cases', type=Path, default=Path(__file__).with_name('knowledge_passage_cases.json'))
    cases = json.loads(parser.parse_args().cases.read_text())
    url = os.getenv('JETINSPECT_EVAL_URL', 'https://172.30.1.82:8765')
    password = os.environ['JETINSPECT_EVAL_PASSWORD']
    output = []
    with httpx.Client(base_url=url, verify=False, trust_env=False, timeout=30, headers={'Origin': url}) as client:
        client.post('/api/session/login', json={'username':'operator','password':password}).raise_for_status()
        try:
            for case in cases:
                t = time.monotonic()
                response = client.get('/api/knowledge/answer', params={'q':case['q']})
                response.raise_for_status()
                data = response.json()
                passages = data['results'][:3]
                hit = any(p['source'] == case['source'] and any(term.lower() in p['text'].lower() for term in case['terms']) for p in passages)
                output.append({'question':case['q'], 'expected_source':case['source'], 'expected_terms':case['terms'],
                               'pass':hit, 'latency_ms':round(1000*(time.monotonic()-t)),
                               'passages':[{k:p[k] for k in ('source','score','offset')} for p in passages]})
        finally:
            client.post('/api/session/logout')
    print(json.dumps({'hits':sum(row['pass'] for row in output),'total':len(output),'cases':output},ensure_ascii=False,indent=2))

if __name__ == '__main__': main()
