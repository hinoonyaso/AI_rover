#!/usr/bin/env python3
"""Evaluate live retrieval against fixed source labels. / 고정된 출처 정답으로 실제 검색을 평가한다."""
import json
import os
from pathlib import Path
import sys
import time
import httpx


def main():
    """Measure source hit rates and negative rejection without printing credentials.

    한글: 비밀번호 출력 없이 출처 적중률과 무관 질문 거부율을 측정한다.
    """
    cases = json.loads(Path(__file__).with_name('knowledge_cases.json').read_text())
    password = os.environ.get('JETINSPECT_EVAL_PASSWORD')
    if not password:
        raise SystemExit('JETINSPECT_EVAL_PASSWORD required')
    url = os.environ.get('JETINSPECT_EVAL_URL', 'https://172.30.1.82:8765')
    rows = []
    with httpx.Client(base_url=url, verify=False, trust_env=False, timeout=60, headers={'Origin': url}) as client:
        login = client.post('/api/session/login', json={'username': 'operator', 'password': password})
        login.raise_for_status()
        try:
            for case in cases:
                start = time.monotonic()
                result = client.get('/api/knowledge/search', params={'q': case['q']})
                result.raise_for_status()
                found = [x['source'] for x in result.json()['results']]
                positive = bool(case['sources'])
                hit = bool(set(found) & set(case['sources'])) if positive else not found
                rows.append({'question': case['q'], 'expected': case['sources'], 'found': found,
                             'pass': hit, 'latency_ms': round((time.monotonic()-start)*1000)})
        finally:
            client.post('/api/session/logout')
    positives = [r for r in rows if r['expected']]
    negatives = [r for r in rows if not r['expected']]
    output = {'positive_hits': sum(r['pass'] for r in positives), 'positives': len(positives),
              'negative_rejected': sum(r['pass'] for r in negatives), 'negatives': len(negatives), 'cases': rows}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__': sys.exit(main())
