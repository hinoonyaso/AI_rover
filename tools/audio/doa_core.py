#!/usr/bin/env python3
"""Offline SRP-PHAT direction estimator for calibrated planar microphone arrays.

한글: 보정된 평면 마이크 배열의 오프라인 SRP-PHAT 음원 방향 추정기.
"""
import math

import numpy as np


def estimate_doa(samples, sample_rate, mic_xy, *, rms_threshold=40.0,
                 frequency_min=300.0, frequency_max=3500.0, step_degrees=2.0,
                 min_contrast=0.03, min_spatial_coherence=0.05, sound_speed=343.0):
    """Estimate arrival direction in array coordinates; return None if unreliable.

    한글: 배열 좌표의 음원 방향을 추정하며 신호가 불충분하거나 모호하면 None을 반환한다.
    Samples are signed PCM-scale values, shape (frames, microphones); coordinates are metres.
    한글: 입력은 PCM 스케일의 (프레임, 마이크) 배열이며 좌표 단위는 미터이다.
    A result is a diagnostic estimate, not a calibrated probability or motion command.
    """
    audio = np.asarray(samples, dtype=np.float64)
    positions = np.asarray(mic_xy, dtype=np.float64)
    scalars = (sample_rate, rms_threshold, frequency_min, frequency_max,
               step_degrees, min_contrast, min_spatial_coherence, sound_speed)
    if not all(math.isfinite(v) for v in scalars):
        raise ValueError('non-finite parameter')
    if (audio.ndim != 2 or audio.shape[0] < 64 or audio.shape[1] < 3 or
            positions.shape != (audio.shape[1], 2) or not np.isfinite(audio).all() or
            not np.isfinite(positions).all()):
        raise ValueError('invalid audio or microphone geometry')
    if (sample_rate <= 0 or rms_threshold < 0 or not 0 < frequency_min < frequency_max or
            frequency_max >= sample_rate / 2 or not 0 < step_degrees <= 30 or
            not 0 <= min_contrast <= 1 or not 0 <= min_spatial_coherence <= 1 or
            sound_speed <= 0):
        raise ValueError('invalid estimator settings')
    distances = np.linalg.norm(positions[:, None, :] - positions[None, :, :], axis=2)
    if np.max(distances) < 0.01 or np.any(distances[np.triu_indices(len(positions), 1)] < 0.001):
        raise ValueError('microphone positions overlap or array is too small')
    audio = audio - np.mean(audio, axis=0, keepdims=True)
    rms = float(np.sqrt(np.mean(audio * audio)))
    if rms < rms_threshold:
        return None
    count = audio.shape[0]
    nfft = 1 << (2 * count - 1).bit_length()
    frequencies = np.fft.rfftfreq(nfft, 1.0 / sample_rate)
    mask = (frequencies >= frequency_min) & (frequencies <= frequency_max)
    spectrum = np.fft.rfft(audio * np.hanning(count)[:, None], n=nfft, axis=0)
    angles = np.arange(0.0, 360.0, step_degrees)
    radians = np.deg2rad(angles)
    directions = np.column_stack((np.cos(radians), np.sin(radians)))
    scores = np.zeros(len(angles), dtype=np.float64)
    pairs = 0
    possible_peak = 0.0
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            cross = spectrum[:, i] * np.conj(spectrum[:, j])
            magnitude = np.abs(cross)
            phat = np.zeros_like(cross)
            valid = mask & (magnitude > 1e-12)
            if np.count_nonzero(valid) < 8:
                continue
            phat[valid] = cross[valid] / magnitude[valid]
            correlation = np.fft.irfft(phat, n=nfft)
            delays = (directions @ (positions[j] - positions[i])) * sample_rate / sound_speed
            low = np.floor(delays).astype(np.int64)
            fraction = delays - low
            scores += ((1.0 - fraction) * correlation[low % nfft] +
                       fraction * correlation[(low + 1) % nfft])
            possible_peak += float(np.fft.irfft(valid.astype(float), n=nfft)[0])
            pairs += 1
    if pairs < 3 or not np.isfinite(scores).all():
        return None
    best = int(np.argmax(scores))
    difference = np.abs((angles - angles[best] + 180.0) % 360.0 - 180.0)
    alternatives = scores[difference >= 30.0]
    peak = float(scores[best])
    if not len(alternatives) or peak <= 1e-12:
        return None
    contrast = max(0.0, float((peak - np.max(alternatives)) / abs(peak)))
    coherence = peak / possible_peak
    # Reject spatially uncorrelated noise; this threshold is experimental, not a safety guarantee.
    # 한글: 공간적으로 무관한 잡음을 거부하지만 이 문턱은 실험값이며 안전을 보장하지 않는다.
    if contrast < min_contrast or coherence < min_spatial_coherence:
        return None
    return {'angle_deg': float(angles[best]), 'relative_contrast': contrast,
            'spatial_coherence': coherence, 'rms': rms}
