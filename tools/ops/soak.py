#!/usr/bin/env python3
"""Record authenticated dashboard health during a stability trial.

한글: 인증된 관제 상태를 장시간 기록한다.
"""
import argparse
from datetime import datetime, timezone
import getpass
from http.cookiejar import CookieJar
import json
from pathlib import Path
import ssl
import time
from urllib.parse import urlsplit
from urllib.request import HTTPSHandler, HTTPCookieProcessor, ProxyHandler, Request, build_opener


def main():
    """Write timestamped samples and failures to a private JSONL file. / 상태와 실패를 개인 JSONL 파일로 저장한다."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--minutes', type=int, default=60)
    parser.add_argument('--interval', type=int, default=30)
    parser.add_argument('--url', required=True, help='HTTPS origin, for example https://172.30.1.82:8765')
    parser.add_argument('--ca-file', type=Path, help='CA certificate for a private deployment')
    parser.add_argument('--username', required=True)
    args = parser.parse_args()
    origin = urlsplit(args.url)
    if (origin.scheme != 'https' or not origin.hostname or origin.path not in ('', '/') or
            origin.query or origin.fragment or origin.username or origin.password):
        parser.error('url must be an HTTPS origin without credentials or a path')
    if not 1 <= args.minutes <= 470 or not 5 <= args.interval <= 3600:
        parser.error('minutes: 1~470, interval: 5~3600 (session expires after 8 hours)')
    base = args.url.rstrip('/')
    context = ssl.create_default_context(cafile=str(args.ca_file) if args.ca_file else None)
    opener = build_opener(ProxyHandler({}), HTTPSHandler(context=context), HTTPCookieProcessor(CookieJar()))
    password = getpass.getpass('대시보드 비밀번호: ')
    payload = json.dumps({'username': args.username, 'password': password}).encode()
    del password
    request = Request(base + '/api/session/login', data=payload,
                      headers={'Content-Type': 'application/json', 'Origin': base}, method='POST')
    with opener.open(request, timeout=10) as response:
        if response.status != 200:
            raise RuntimeError('login failed')
    del payload, request
    directory = Path.home() / '.local/share/jetinspect-ops/soak'
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = directory / (datetime.now().strftime('%Y%m%d-%H%M%S') + '.jsonl')
    end = time.monotonic() + args.minutes * 60
    count = errors = 0
    try:
        with path.open('x', encoding='utf-8') as out:
            while time.monotonic() < end:
                sample = {'captured_at': datetime.now(timezone.utc).isoformat()}
                try:
                    with opener.open(base + '/api/status', timeout=5) as response:
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
    finally:
        try:
            opener.open(Request(base + '/api/session/logout', data=b'', headers={'Origin': base}, method='POST'), timeout=5).close()
        except Exception:
            pass
    print(f'기록: {path}, 표본 {count}, 오류 {errors}')


if __name__ == '__main__':
    main()
