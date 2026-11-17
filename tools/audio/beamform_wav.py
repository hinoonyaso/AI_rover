#!/usr/bin/env python3
"""Beamform a six-channel recording using explicit microphone geometry.

한글: 명시된 마이크 좌표를 이용해 6채널 녹음의 방향성 집음을 수행한다.
"""
import argparse
import sys
import wave

from beamform_array import beamform
from doa_stream import load_geometry
import numpy as np


def main():
    """Read a multichannel WAV and write a new mono WAV.

    한글: 다채널 WAV를 읽어 새 모노 WAV로 저장한다.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wav', required=True)
    parser.add_argument('--geometry', required=True)
    parser.add_argument('--angle', required=True, type=float)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        with wave.open(args.wav, 'rb') as reader:
            if reader.getsampwidth() != 2 or reader.getcomptype() != 'NONE':
                raise ValueError('input must be uncompressed 16-bit PCM WAV')
            channels, rate = reader.getnchannels(), reader.getframerate()
            mapping, xy, calibrated, frame = load_geometry(args.geometry, channels)
            if not calibrated:
                print('경고: 마이크 좌표와 채널이 보정되지 않았습니다.', file=sys.stderr)
            raw = reader.readframes(reader.getnframes())
            if len(raw) % (channels * 2):
                raise ValueError('input has an incomplete audio frame')
            samples = np.frombuffer(raw, dtype='<i2').reshape(-1, channels)[:, mapping]
        output = beamform(samples, rate, xy, args.angle)
        pcm = np.clip(np.rint(output), -32768, 32767).astype('<i2').tobytes()
        # Exclusive creation avoids overwriting an existing recording.
        # 한글: 기존 녹음을 덮어쓰지 않도록 새 파일만 생성한다.
        with open(args.output, 'xb') as file:
            with wave.open(file, 'wb') as writer:
                writer.setnchannels(1)
                writer.setsampwidth(2)
                writer.setframerate(rate)
                writer.writeframes(pcm)
        print(f'집음 완료: frame={frame}, calibrated={calibrated}, angle={args.angle}°')
        return 0
    except (OSError, ValueError, KeyError, wave.Error) as exc:
        print(f'집음 실패: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
