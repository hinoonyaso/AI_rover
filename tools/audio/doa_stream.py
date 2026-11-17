#!/usr/bin/env python3
"""Estimate direction from explicit multichannel WAV or ALSA input, without robot motion.

한글: 명시된 다채널 WAV 또는 ALSA 입력의 방향을 추정하며 로봇을 움직이지 않는다.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
import sys
import wave

from doa_core import estimate_doa
import numpy as np


def load_geometry(path, channels):
    """Validate channel mapping and microphone positions in metres.

    한글: 채널 매핑과 미터 단위 마이크 좌표를 검증한다.
    """
    config = json.loads(Path(path).read_text(encoding='utf-8'))
    mapping = config.get('channels')
    positions = np.asarray(config.get('mic_xy_m'), dtype=np.float64)
    if (not isinstance(mapping, list) or len(mapping) != 6 or
            any(not isinstance(i, int) or isinstance(i, bool) or i < 0 or i >= channels
                for i in mapping) or len(set(mapping)) != 6 or
            positions.shape != (6, 2) or not np.isfinite(positions).all()):
        raise ValueError('need six unique channel indexes and six finite xy positions')
    if not isinstance(config.get('calibrated'), bool):
        raise ValueError('calibrated must be explicitly true or false')
    if not isinstance(config.get('frame_id'), str) or not config['frame_id'].strip():
        raise ValueError('frame_id must be a nonempty string')
    return mapping, positions, config['calibrated'], config['frame_id']


def analyse(raw, channels, mapping, positions, rate, calibrated, frame_id, offset,
            rms_threshold, min_contrast, min_coherence):
    """Estimate one PCM block and label its frame and calibration status.

    한글: PCM 블록 하나를 추정하고 좌표계와 보정 상태를 함께 표시한다.
    """
    samples = np.frombuffer(raw, dtype='<i2').reshape(-1, channels)[:, mapping]
    result = estimate_doa(samples, rate, positions, rms_threshold=rms_threshold,
                          min_contrast=min_contrast, min_spatial_coherence=min_coherence)
    out = {'offset_s': round(offset, 3), 'frame_id': frame_id, 'calibrated': calibrated}
    if result is None:
        out['state'] = 'no_estimate'
    else:
        out.update(state='estimate', **result)
    return out


def main():
    """Read blocks and print JSONL estimates; requires explicit array geometry.

    한글: 입력 블록의 추정값을 JSONL로 출력하며 배열 좌표를 명시해야 한다.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--wav', help='16-bit PCM multichannel WAV')
    source.add_argument('--device', help='ALSA capture device providing real multichannel PCM')
    parser.add_argument('--geometry', required=True,
                        help='JSON channel mapping and measured mic coordinates')
    parser.add_argument('--channels', type=int, help='input channel count, required for ALSA')
    parser.add_argument('--rate', type=int, default=16000, help='ALSA sample rate')
    parser.add_argument('--window', type=float, default=0.25, help='block duration in seconds')
    parser.add_argument('--rms-threshold', type=float, default=40.0, help='PCM RMS gate')
    parser.add_argument('--min-contrast', type=float, default=0.03, help='relative peak gate')
    parser.add_argument('--min-coherence', type=float, default=0.05, help='spatial coherence gate')
    args = parser.parse_args()
    if not math.isfinite(args.window) or not 0.05 <= args.window <= 2.0:
        parser.error('--window must be 0.05–2 seconds')
    process = None
    reader = None
    try:
        if args.wav:
            reader = wave.open(args.wav, 'rb')
            if reader.getsampwidth() != 2 or reader.getcomptype() != 'NONE':
                raise ValueError('WAV must be uncompressed signed 16-bit PCM')
            channels, rate = reader.getnchannels(), reader.getframerate()
        else:
            if not args.channels or args.channels < 6 or args.rate <= 0:
                raise ValueError('ALSA requires --channels >= 6 and a positive --rate')
            channels, rate = args.channels, args.rate
        mapping, positions, calibrated, frame_id = load_geometry(args.geometry, channels)
        if not calibrated:
            print('경고: 채널 배치·방향 미보정; 실제 로봇 방향으로 사용하지 마세요.', file=sys.stderr)
        if args.device:
            command = ['arecord', '-q', '-D', args.device, '-t', 'raw', '-f', 'S16_LE',
                       '-c', str(channels), '-r', str(rate)]
            process = subprocess.Popen(command, stdout=subprocess.PIPE)
        frames = round(rate * args.window)
        offset = 0
        while True:
            raw = (reader.readframes(frames) if reader
                   else process.stdout.read(frames * channels * 2))
            if not raw:
                if process is not None and process.wait(timeout=3) != 0:
                    raise RuntimeError(f'arecord failed with exit code {process.returncode}')
                break
            if len(raw) != frames * channels * 2:
                print('불완전한 마지막 블록은 버립니다.', file=sys.stderr)
                break
            result = analyse(raw, channels, mapping, positions, rate, calibrated,
                             frame_id, offset / rate, args.rms_threshold, args.min_contrast,
                             args.min_coherence)
            print(json.dumps(result, ensure_ascii=False), flush=True)
            offset += frames
        if process is not None and process.poll() not in (None, 0):
            raise RuntimeError(f'arecord failed with exit code {process.returncode}')
    except (OSError, ValueError, KeyError, wave.Error, RuntimeError,
            subprocess.TimeoutExpired) as exc:
        print(f'DOA 입력 오류: {exc}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    finally:
        if reader is not None:
            reader.close()
        if process is not None:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
            if process.stdout is not None:
                process.stdout.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
