"""Behavior checks for streaming denoising.

한글: 실시간 소음 억제 동작 검증이다.
"""
from live_denoise import FRAME, HOP, StreamingDenoiser
import numpy as np
import pytest


def stream(processor, x):
    return np.concatenate([processor.process(x[i:i + HOP]) for i in range(0, len(x), HOP)])


def test_identity_with_fixed_stream_delay():
    rng = np.random.default_rng(13)
    audio = rng.normal(0, 0.02, HOP * 300)
    out = stream(StreamingDenoiser(audio[:16000], strength=0), audio)
    np.testing.assert_allclose(out[FRAME:], audio[HOP: -FRAME + HOP], atol=1e-10)


def test_stationary_noise_is_reduced():
    rng = np.random.default_rng(2)
    noise = rng.normal(0, 0.02, HOP * 500)
    out = stream(StreamingDenoiser(noise[:16000]), noise)
    assert np.sqrt(np.mean(out[16000:] ** 2)) < 0.8 * np.sqrt(np.mean(noise[16000:] ** 2))


def test_invalid_blocks_are_rejected():
    p = StreamingDenoiser(np.zeros(FRAME))
    with pytest.raises(ValueError):
        p.process(np.zeros(HOP - 1))
