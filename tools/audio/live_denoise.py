#!/usr/bin/env python3
"""Experimental streaming mono denoising and low-volume ALSA monitoring.

한글: 실험용 모노 실시간 소음 억제와 낮은 음량의 ALSA 모니터링이다.
"""
import argparse
import subprocess
import sys
import time

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal.windows import hann

RATE = 16000
FRAME = 512
HOP = 128


class StreamingDenoiser:
    """Suppress stationary noise using a fixed noise-only calibration.

    한글: 소음만 포함한 초기 구간을 기준으로 지속적인 소음을 억제한다.
    """

    def __init__(self, noise, strength=1.2, min_gain=0.25):
        noise = np.asarray(noise, dtype=np.float64)
        if (noise.ndim != 1 or len(noise) < FRAME or not np.isfinite(noise).all()
                or not np.isfinite(strength) or strength < 0
                or not np.isfinite(min_gain) or not 0 < min_gain <= 1):
            raise ValueError('invalid noise profile or suppression settings')
        self.window = np.sqrt(hann(FRAME, sym=False))
        frames = np.lib.stride_tricks.sliding_window_view(noise, FRAME)[::HOP]
        self.noise_power = np.median(abs(np.fft.rfft(frames * self.window)) ** 2, axis=0)
        self.strength = strength
        self.min_gain = min_gain
        self.history = np.zeros(FRAME)
        self.overlap = np.zeros(FRAME)
        self.gain = np.ones(FRAME // 2 + 1)

    def process(self, samples):
        """Process one 8 ms hop, preserving overlap state across calls.

        한글: 8ms 단위를 처리하며 호출 사이에 중첩 상태를 유지한다.
        """
        samples = np.asarray(samples, dtype=np.float64)
        if samples.shape != (HOP,) or not np.isfinite(samples).all():
            raise ValueError('expected 128 finite mono samples')
        self.history[:-HOP] = self.history[HOP:]
        self.history[-HOP:] = samples
        spectrum = np.fft.rfft(self.history * self.window)
        power = abs(spectrum) ** 2
        gain = np.maximum(self.min_gain, 1 - self.strength * self.noise_power / (power + 1e-12))
        gain = gaussian_filter1d(gain, 0.8)
        self.gain = 0.7 * self.gain + 0.3 * gain
        # Four overlapping sqrt-Hann windows have squared sum 2.
        # 한글: 4개 중첩된 sqrt-Hann 창의 제곱합이 2이므로 이를 나눈다.
        self.overlap += np.fft.irfft(spectrum * self.gain) * self.window / 2
        result = self.overlap[:HOP].copy()
        self.overlap[:-HOP] = self.overlap[HOP:]
        self.overlap[-HOP:] = 0
        return np.clip(result, -1, 1)


def read_exact(stream, size):
    """Read an entire audio block or fail if capture ended.

    한글: 오디오 블록을 끝까지 읽고 입력이 종료되면 오류를 낸다.
    """
    data = bytearray()
    while len(data) < size:
        chunk = stream.read(size - len(data))
        if not chunk:
            raise RuntimeError('microphone capture ended unexpectedly')
        data.extend(chunk)
    return bytes(data)


def main():
    """Run a time-limited monitoring session without saving audio.

    한글: 녹음을 저장하지 않고 제한 시간 동안 모니터링한다.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=int, default=20, choices=range(1, 121))
    parser.add_argument('--volume', type=float)
    parser.add_argument('--deferred', action='store_true',
                        help='play processed audio after capture to avoid feedback')
    parser.add_argument('--capture', default='hw:CARD=XFMDPV0018,DEV=0')
    parser.add_argument('--playback', default='plughw:CARD=Device,DEV=0')
    args = parser.parse_args()
    if args.volume is None:
        args.volume = 0.5 if args.deferred else 0.1
    max_volume = 0.8 if args.deferred else 0.3
    if not 0 <= args.volume <= max_volume:
        parser.error(f'volume must be between 0 and {max_volume}')
    common = ['-q', '-t', 'raw', '-f', 'S16_LE', '-r', str(RATE), '-c', '1',
              '--buffer-time=64000', '--period-time=16000']
    capture = None
    player = None
    try:
        capture = subprocess.Popen(['arecord', '-D', args.capture] + common,
                                   stdout=subprocess.PIPE, bufsize=0)
        print('소음 측정 중: 2초간 조용히 해 주세요.', flush=True)
        raw = read_exact(capture.stdout, RATE * 2 * 2)
        noise = np.frombuffer(raw, dtype='<i2').astype(np.float64) / 32768
        processor = StreamingDenoiser(noise)
        if not args.deferred:
            player = subprocess.Popen(['aplay', '-D', args.playback] + common,
                                      stdin=subprocess.PIPE, bufsize=0)
        buffered = bytearray()
        print('실시간 처리 시작: 이제 말씀해 주세요.', flush=True)
        start = time.monotonic()
        peak = 0.0
        max_proc = 0.0
        for _ in range(args.seconds * RATE // HOP):
            data = read_exact(capture.stdout, HOP * 2)
            samples = np.frombuffer(data, dtype='<i2').astype(np.float64) / 32768
            peak = max(peak, float(np.max(np.abs(samples))))
            before = time.monotonic()
            clean = processor.process(samples)
            max_proc = max(max_proc, time.monotonic() - before)
            output = (clean * args.volume * 32767).astype('<i2').tobytes()
            if args.deferred:
                buffered.extend(output)
            else:
                player.stdin.write(output)
        elapsed = time.monotonic() - start
        if args.deferred:
            capture.terminate()
            capture.wait(timeout=2)
            print('입력 종료, 처리된 음성을 재생합니다.', flush=True)
            player = subprocess.Popen(['aplay', '-D', args.playback] + common,
                                      stdin=subprocess.PIPE, bufsize=0)
            player.stdin.write(buffered)
        player.stdin.close()
        if player.wait(timeout=10) != 0:
            raise RuntimeError('playback failed')
        print(f'완료: 처리 시간 최대 {max_proc * 1000:.2f} ms/8 ms, '
              f'처리 경과 {elapsed:.1f}초, 입력 피크 {peak:.4f}', flush=True)
    finally:
        for proc in (capture, player):
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f'오디오 시험 실패: {exc}', file=sys.stderr)
        sys.exit(1)
