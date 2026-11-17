#!/usr/bin/env python3
"""Capture and compare mono microphone audio in memory.

한글: 모노 마이크를 녹음해 원본과 소음 억제 결과를 메모리에서 비교한다.
"""
import argparse
import subprocess
import sys
import time

from denoise_mono import suppress_noise
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=int, default=20, choices=range(4, 61))
    parser.add_argument('--capture', default='hw:CARD=XFMDPV0018,DEV=0')
    parser.add_argument('--playback', default='plughw:CARD=Device,DEV=0')
    args = parser.parse_args()
    rate = 16000
    print('녹음 시작: 처음 2초는 조용히, 그 후 말씀해 주세요.', flush=True)
    record = subprocess.run(
        ['arecord', '-q', '-D', args.capture, '-t', 'raw', '-f', 'S16_LE',
         '-r', str(rate), '-c', '1', '-d', str(args.seconds)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=args.seconds + 10,
        check=True)
    if len(record.stdout) != args.seconds * rate * 2:
        raise RuntimeError('incomplete audio capture')
    original = np.frombuffer(record.stdout, dtype='<i2').astype(np.float64) / 32768
    cleaned = suppress_noise(original, rate, noise_seconds=2.0)
    reference = slice(0, rate * 2)
    before = float(np.sqrt(np.mean(original[reference] ** 2)))
    after = float(np.sqrt(np.mean(cleaned[reference] ** 2)))
    print(f'초기 배경 소음 RMS: {before:.6f} → {after:.6f}', flush=True)
    print(f'전체 입력 피크: {np.max(np.abs(original)):.6f}', flush=True)
    for name, audio in [('원본', original), ('소음 억제본', cleaned)]:
        print(f'{name} 재생 중', flush=True)
        pcm = (np.clip(audio * 0.35, -1, 1) * 32767).astype('<i2').tobytes()
        subprocess.run(['aplay', '-q', '-D', args.playback, '-t', 'raw', '-f',
                        'S16_LE', '-r', str(rate), '-c', '1'], input=pcm,
                       check=True, timeout=args.seconds + 10)
        time.sleep(1)
    print('비교 재생 완료 (녹음 파일은 저장하지 않았습니다).', flush=True)


if __name__ == '__main__':
    try:
        main()
    except (subprocess.SubprocessError, OSError, ValueError, RuntimeError) as exc:
        print(f'시험 실패: {exc}', file=sys.stderr)
        sys.exit(1)
