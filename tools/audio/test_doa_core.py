# Direction estimates are tested with synthetic microphone signals, not a robot.
# 한글: 방향 추정은 실제 로봇이 아닌 합성 마이크 신호로 시험한다.
import math

from doa_core import estimate_doa
import numpy as np
import pytest


@pytest.fixture
def geometry():
    angles = np.arange(6) * (2 * math.pi / 6)
    return np.column_stack((0.035 * np.cos(angles), 0.035 * np.sin(angles)))


def plane_wave(positions, direction, seed=42):
    rng = np.random.default_rng(seed)
    fs, length = 16000, 16384
    spectrum = np.fft.rfft(rng.normal(size=length))
    freq = np.fft.rfftfreq(length, 1 / fs)
    unit = np.array([math.cos(direction), math.sin(direction)])
    result = []
    for p in positions:
        phase = np.exp(2j * np.pi * freq * np.dot(p, unit) / 343.0)
        result.append(np.fft.irfft(spectrum * phase, n=length)[2048:6144] * 4000)
    return np.column_stack(result)


@pytest.mark.parametrize('degrees', [0, 45, 90, 180, 270, 358])
def test_synthetic_plane_wave(geometry, degrees):
    result = estimate_doa(plane_wave(geometry, math.radians(degrees)), 16000, geometry)
    assert result is not None
    error = abs((result['angle_deg'] - degrees + 180) % 360 - 180)
    assert error <= 4


def test_silence_and_identical_channels_do_not_produce_a_direction(geometry):
    assert estimate_doa(np.zeros((1024, 6)), 16000, geometry) is None
    identical = np.tile(np.random.default_rng(2).normal(size=(1024, 1)) * 2000, (1, 6))
    assert estimate_doa(identical, 16000, geometry) is None


def test_invalid_geometry_or_data_fail():
    with pytest.raises(ValueError):
        estimate_doa(np.zeros((1024, 6)), 16000, np.zeros((6, 2)))
    with pytest.raises(ValueError):
        estimate_doa(np.full((1024, 6), np.nan), 16000, np.ones((6, 2)))


def test_independent_noise_has_no_direction(geometry):
    rng = np.random.default_rng(731)
    for _ in range(100):
        noise = rng.normal(0, 2000, (4000, 6))
        assert estimate_doa(noise, 16000, geometry) is None
