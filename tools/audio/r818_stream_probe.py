#!/usr/bin/env python3
"""Receive temporary 8-channel R818 PCM over ADB and display DOA diagnostics.

한글: R818의 임시 8채널 PCM을 ADB로 수신해 방향 진단값만 표시한다.
"""
import argparse
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time

from doa_core import estimate_doa
import numpy as np


def main():
    """Run a bounded streaming probe without saving the audio.

    한글: 녹음을 저장하지 않고 시간 제한 스트리밍 진단을 실행한다.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adb', required=True)
    parser.add_argument('--geometry', required=True)
    parser.add_argument('--seconds', type=int, default=10, choices=range(1, 61))
    parser.add_argument('--min-rms', type=float, default=100.0)
    parser.add_argument('--min-coherence', type=float, default=0.35)
    args = parser.parse_args()
    if (not np.isfinite(args.min_rms) or args.min_rms < 0 or
            not np.isfinite(args.min_coherence) or not 0 <= args.min_coherence <= 1):
        parser.error('invalid diagnostic thresholds')
    geometry = json.loads(Path(args.geometry).read_text())
    mapping = geometry['channels']
    positions = np.asarray(geometry['mic_xy_m'], dtype=float)
    if (len(mapping) != 6 or len(set(mapping)) != 6 or
            any(not isinstance(i, int) or not 0 <= i < 8 for i in mapping)):
        raise ValueError('geometry must name six distinct channels from 0 to 7')
    script = Path(__file__).with_suffix('.sh')
    subprocess.run([args.adb, 'push', str(script), '/tmp/jetrover-r818-stream.sh'],
                   stdout=subprocess.DEVNULL, check=True, timeout=15)
    command = [args.adb, 'shell', f'sh /tmp/jetrover-r818-stream.sh {args.seconds}']
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
    start = time.monotonic()
    try:
        for i in range(args.seconds):
            data = bytearray()
            while len(data) < 512000:
                if not select.select([proc.stdout], [], [], 12)[0]:
                    raise RuntimeError('stream timed out')
                chunk = os.read(proc.stdout.fileno(), 512000 - len(data))
                if not chunk:
                    raise RuntimeError('stream ended before all samples arrived')
                data.extend(chunk)
            try:
                raw = bytes.fromhex(data.decode('ascii'))
            except (UnicodeDecodeError, ValueError) as exc:
                raise RuntimeError('corrupted audio transport') from exc
            if len(raw) != 256000:
                raise RuntimeError('incomplete 8-channel audio block')
            audio = np.frombuffer(raw, dtype='<i2').reshape(-1, 8)[:, mapping]
            result = estimate_doa(audio, 16000, positions, min_contrast=0,
                                  min_spatial_coherence=0)
            data = {'second': i + 1, 'elapsed_s': round(time.monotonic() - start, 2),
                    'state': 'no_estimate'}
            if result and i >= 2 and result['rms'] >= args.min_rms and (
                    result['spatial_coherence'] >= args.min_coherence):
                data.update(state='unverified_candidate', **result)
            elif i < 2:
                data['state'] = 'startup_suppressed'
            print(json.dumps(data), flush=True)
        if proc.wait(timeout=10) != 0:
            raise RuntimeError('board stream exited with an error')
        return 0
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f'스트리밍 오류: {exc}', file=sys.stderr)
        raise SystemExit(1)
