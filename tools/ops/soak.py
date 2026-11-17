#!/usr/bin/env python3
"""Record dashboard health during a user-selected stability trial.

한글: 사용자가 정한 안정성 시험 동안 관제 상태를 기록한다.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from urllib.request import urlopen


def main():
    """Write timestamped samples and failures to a private JSONL file. / 상태와 실패를 개인 JSONL 파일로 저장한다."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--minutes', type=int, default=60)
    parser.add_argument('--interval', type=int, default=30)
    args = parser.parse_args()
    if not 1 <= args.minutes <= 10080 or not 5 <= args.interval <= 3600:
        parser.error('minutes: 1~10080, interval: 5~3600')
    directory = Path.home() / '.local/share/jetinspect-ops/soak'
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = directory / (datetime.now().strftime('%Y%m%d-%H%M%S') + '.jsonl')
    end = time.monotonic() + args.minutes * 60
    count = errors = 0
    with path.open('x', encoding='utf-8') as out:
        while time.monotonic() < end:
            sample = {'captured_at': datetime.now(timezone.utc).isoformat()}
            try:
                with urlopen('http://127.0.0.1:8765/api/status', timeout=5) as response:
                    sample['status'] = json.load(response)
                if sample['status']['database'] != 'connected':
                    errors += 1
            except Exception as exc:
                errors += 1
                sample['error'] = type(exc).__name__
            out.write(json.dumps(sample, ensure_ascii=False) + '\n')
            out.flush()
            count += 1
            time.sleep(min(args.interval, max(0, end - time.monotonic())))
    print(f'기록: {path}, 표본 {count}, 오류 {errors}')


if __name__ == '__main__':
    main()
