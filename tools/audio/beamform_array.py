#!/usr/bin/env python3
"""Experimental delay-and-sum beamformer for calibrated six-channel recordings.

한글: 보정된 6채널 녹음에 사용하는 실험용 지연합 빔포머이다.
"""
import math

import numpy as np


def beamform(samples, sample_rate, positions, angle_deg, speed=343.0):
    """Steer toward an angle in the microphone coordinate frame.

    한글: 마이크 좌표계의 지정 각도 방향으로 지연합 집음한다.
    Input is six synchronized channels; output has the same sample count.
    한글: 입력은 동기화된 6채널이며 출력의 샘플 수는 입력과 같다.
    FFT padding suppresses circular wraparound; this is an offline operation.
    한글: FFT 패딩으로 양 끝의 순환 결합을 줄이는 오프라인 처리다.
    """
    audio = np.asarray(samples, dtype=np.float64)
    xy = np.asarray(positions, dtype=np.float64)
    if (audio.ndim != 2 or audio.shape[1] != 6 or audio.shape[0] < 512
            or xy.shape != (6, 2) or not np.isfinite(audio).all()
            or not np.isfinite(xy).all() or not math.isfinite(angle_deg)
            or not math.isfinite(sample_rate) or sample_rate <= 0
            or not math.isfinite(speed) or speed <= 0):
        raise ValueError('expected finite synchronized six-channel samples and geometry')
    distances = np.linalg.norm(xy[:, None, :] - xy[None, :, :], axis=2)
    if np.any(distances[np.triu_indices(6, 1)] < 1e-4) or np.max(distances) > 2:
        raise ValueError('invalid microphone geometry')
    unit = np.array([math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))])
    delay = (xy - xy.mean(axis=0)) @ unit / speed
    margin = math.ceil(np.max(np.abs(delay)) * sample_rate) + 16
    n = audio.shape[0] + 2 * margin
    padded = np.pad(audio, ((margin, margin), (0, 0)))
    freq = np.fft.rfftfreq(n, 1 / sample_rate)
    # Align arrival times for a far-field source in the selected direction.
    # 한글: 선택한 방향의 원거리 음원이 각 마이크에 도달한 시간을 맞춘다.
    spectrum = np.fft.rfft(padded, axis=0)
    aligned = spectrum * np.exp(-2j * np.pi * freq[:, None] * delay[None, :])
    return np.fft.irfft(aligned.mean(axis=1), n=n)[margin:-margin]
