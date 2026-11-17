#!/usr/bin/env python3
"""Offline noise-profile suppression for mono audio; no microphone access.

한글: 모노 음성의 소음 구간을 이용한 오프라인 억제기이며 직접 녹음하지 않는다.
"""
import math

import numpy as np
from scipy import ndimage, signal


def suppress_noise(samples, rate, noise_seconds=1.5, strength=1.2, min_gain=0.25):
    """Reduce stationary noise using a noise-only prefix and a bounded spectral mask.

    한글: 처음 무음 구간의 소음 스펙트럼과 제한된 마스크로 지속적인 소음을 줄인다.
    Input and output are mono floating point, with nominal amplitude in [-1, 1].
    한글: 입력과 출력은 통상 [-1, 1] 범위의 모노 부동소수점 신호이다.
    This is an offline experiment, not an acoustic echo canceller or speech separator.
    """
    audio = np.asarray(samples, dtype=np.float64)
    settings = (rate, noise_seconds, strength, min_gain)
    if (audio.ndim != 1 or not np.isfinite(audio).all() or
            not all(math.isfinite(x) for x in settings)):
        raise ValueError('invalid mono audio or non-finite setting')
    if (rate != 16000 or not 0.5 <= noise_seconds <= 5 or strength < 0 or
            not 0 < min_gain <= 1):
        raise ValueError('unsupported sample rate or noise suppression setting')
    if len(audio) < int((noise_seconds + 0.25) * rate):
        raise ValueError('audio is shorter than the noise profile plus 0.25 seconds')
    if np.max(np.abs(audio), initial=0.0) > 1.0:
        raise ValueError('audio amplitude must be within [-1, 1]')
    # The noise reference must precede speech; no live adaptive update can erase a speaker.
    # 한글: 소음 구간은 발화보다 앞에 있어야 하며 발화 중 소음 프로필을 자동 갱신하지 않는다.
    _, times, spectrum = signal.stft(audio, fs=rate, nperseg=512, noverlap=384,
                                     boundary='zeros', padded=True)
    reference = times <= noise_seconds - 0.016
    power = np.abs(spectrum) ** 2
    noise_power = np.median(power[:, reference], axis=1, keepdims=True)
    gain = np.maximum(min_gain, 1.0 - strength * noise_power / (power + 1e-12))
    gain = ndimage.gaussian_filter(gain, sigma=(0.8, 1.0), mode='nearest')
    _, result = signal.istft(spectrum * gain, fs=rate, nperseg=512, noverlap=384,
                             boundary=True)
    result = result[:len(audio)]
    if len(result) < len(audio):
        result = np.pad(result, (0, len(audio) - len(result)))
    return np.clip(result, -1.0, 1.0)
