"""Verify beam steering on simulated signals; not real-device evidence.

한글: 합성 신호의 집음 방향을 검증하며 실기 증거는 아니다.
"""
import json
import math
from pathlib import Path
import subprocess
import sys
import wave

from beamform_array import beamform
import numpy as np
import pytest
from test_doa_core import plane_wave


def test_steering_preserves_target_and_reduces_interference():
    angles = np.arange(6) * (2 * math.pi / 6)
    xy = np.column_stack((0.035 * np.cos(angles), 0.035 * np.sin(angles)))
    target = plane_wave(xy, 0, seed=1)
    interference = plane_wave(xy, math.pi / 2, seed=2)
    target_out = beamform(target, 16000, xy, 0)[64:-64]
    interference_out = beamform(interference, 16000, xy, 0)[64:-64]
    target_in = target[64:-64, 0]
    interference_in = interference[64:-64, 0]
    target_gain = np.mean(target_out ** 2) / np.mean(target_in ** 2)
    interference_gain = np.mean(interference_out ** 2) / np.mean(interference_in ** 2)
    assert target_gain > 0.9
    assert interference_gain < 0.5


def test_bad_geometry_and_channel_count_rejected():
    with pytest.raises(ValueError):
        beamform(np.zeros((1024, 1)), 16000, np.zeros((6, 2)), 0)
    with pytest.raises(ValueError):
        beamform(np.zeros((1024, 6)), 16000, np.zeros((6, 2)), 0)


def test_wav_cli_uses_mapping_and_never_overwrites(tmp_path):
    angles = np.arange(6) * (2 * math.pi / 6)
    xy = np.column_stack((0.035 * np.cos(angles), 0.035 * np.sin(angles)))
    x = np.clip(plane_wave(xy, 0), -32768, 32767).astype('<i2')
    wav = tmp_path / 'input.wav'
    config = tmp_path / 'geometry.json'
    output = tmp_path / 'output.wav'
    with wave.open(str(wav), 'wb') as f:
        f.setnchannels(6)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(x.tobytes())
    config.write_text(json.dumps({'channels': list(range(6)), 'mic_xy_m': xy.tolist(),
                                  'frame_id': 'test', 'calibrated': False}))
    cmd = [sys.executable, str(Path(__file__).with_name('beamform_wav.py')), '--wav',
           str(wav), '--geometry', str(config), '--angle', '0', '--output', str(output)]
    assert subprocess.run(cmd, capture_output=True).returncode == 0
    with wave.open(str(output), 'rb') as f:
        assert f.getnchannels() == 1 and f.getnframes() == len(x)
    assert subprocess.run(cmd, capture_output=True).returncode != 0
