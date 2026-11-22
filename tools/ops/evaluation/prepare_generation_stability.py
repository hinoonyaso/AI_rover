#!/usr/bin/env python3
"""Prepare fixed questions and passages from an isolated index for a load trial.

한글: 격리 색인에서 부하 시험용 질문과 근거 문단을 준비한다.
"""
import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from knowledge import Knowledge

QUESTIONS = [
    'CH340은 USB 목록에 있지만 리눅스에서 장치 파일이 없을 때 어떤 커널 모듈을 검사하나요?',
    '가속도계 여섯 자세 보정에서 센서 교차축 오차도 측정하나요?',
]


def main():
    """Write private test inputs without touching the active index. / 활성 색인을 건드리지 않고 시험 입력을 저장한다."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--store', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    store = Knowledge(args.store)
    try:
        rows = [{'query': q, 'results': store.search(q)[:3]} for q in QUESTIONS]
        if any(not x['results'] for x in rows):
            raise ValueError('시험 질문의 문서 근거가 없습니다')
    finally:
        store.client.close()
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as out:
        json.dump(rows, out, ensure_ascii=False)
    print(f'fixed questions: {len(rows)}, output: {args.output}')


if __name__ == '__main__':
    main()
