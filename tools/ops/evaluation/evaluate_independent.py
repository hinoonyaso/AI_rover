#!/usr/bin/env python3
"""Score answer-bearing passages and negative queries on an isolated index.

한글: 격리 색인에서 정답 근거 문단과 무관 질문 거부를 평가한다.
"""
import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from knowledge import Knowledge


def main():
    """Record top-three passage results without scoring model-generated answers.

    한글: 생성 답변 채점 없이 상위 3개 문단의 정답 근거를 기록한다.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--store', type=Path, required=True)
    parser.add_argument('--cases', type=Path, default=Path(__file__).with_name('knowledge_independent_20261119.json'))
    parser.add_argument('--term-mode', choices=('all', 'any'), default='all')
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text())
    store = Knowledge(args.store)
    rows = []
    try:
        for case in cases:
            start = time.monotonic()
            result = store.search(case['q'])
            success = (any(p['source'] == case['source'] and (all if args.term_mode == 'all' else any)(t in p['text'] for t in case['terms'])
                           for p in result[:3]) if case['source'] else not result)
            rows.append({'question': case['q'], 'expected_source': case['source'], 'expected_terms': case['terms'],
                         'pass': success, 'results': [{k: p[k] for k in ('source', 'offset', 'sha256')} for p in result],
                         'latency_ms': round(1000 * (time.monotonic() - start))})
    finally:
        store.client.close()
    positive = [row for row in rows if row['expected_source']]
    negative = [row for row in rows if not row['expected_source']]
    print(json.dumps({'positive_pass': sum(r['pass'] for r in positive), 'positive_total': len(positive),
                      'negative_pass': sum(r['pass'] for r in negative), 'negative_total': len(negative),
                      'cases': rows}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
