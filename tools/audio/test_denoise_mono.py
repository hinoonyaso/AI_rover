# The tests use generated signals only; no user microphone audio is stored.
# 한글: 합성 신호만 사용하며 사용자 음성은 저장하지 않는다.
from denoise_mono import suppress_noise
import numpy as np
import pytest


def test_identity_when_strength_is_zero():
    rng = np.random.default_rng(13)
    x = rng.normal(0, 0.05, 48000)
    y = suppress_noise(x, 16000, noise_seconds=1.5, strength=0.0)
    assert len(y) == len(x)
    np.testing.assert_allclose(y, x, atol=1e-10)


def test_stationary_noise_is_reduced_and_tone_remains():
    rng = np.random.default_rng(43)
    fs = 16000
    t = np.arange(fs * 4) / fs
    noise = rng.normal(0, 0.02, len(t))
    tone = np.where(t >= 1.6, 0.18 * np.sin(2 * np.pi * 730 * t), 0)
    x = noise + tone
    y = suppress_noise(x, fs)
    assert np.sqrt(np.mean(y[4000:20000] ** 2)) < 0.7 * np.sqrt(np.mean(x[4000:20000] ** 2))
    assert abs(np.dot(y[32000:48000], tone[32000:48000])) > 0.75 * np.dot(
        tone[32000:48000], tone[32000:48000])


@pytest.mark.parametrize('audio,rate', [([0] * 100, 16000), ([[0, 0]] * 32000, 16000),
                                        ([0] * 32000, 8000), ([float('nan')] * 32000, 16000)])
def test_invalid_input_is_rejected(audio, rate):
    with pytest.raises(ValueError):
        suppress_noise(audio, rate)
