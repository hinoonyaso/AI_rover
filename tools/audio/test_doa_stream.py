# Exercise WAV decoding, explicit channel mapping and silent-input handling.
# 한글: WAV 디코딩, 명시적 채널 매핑과 무음 처리를 검증한다.
import json
from pathlib import Path
import subprocess
import sys
import wave

import numpy as np

from test_doa_core import plane_wave


def test_wav_pipeline_with_permuted_channels(tmp_path):
    degrees = np.arange(6) * np.pi / 3
    positions = np.column_stack((0.035 * np.cos(degrees), 0.035 * np.sin(degrees)))
    mapping = [5, 2, 0, 6, 3, 7]
    signal = plane_wave(positions, np.pi / 2)
    audio = np.zeros((len(signal), 8), dtype='<i2')
    audio[:, mapping] = np.clip(signal, -32768, 32767).astype('<i2')
    wav = tmp_path / 'eight.wav'
    with wave.open(str(wav), 'wb') as out:
        out.setnchannels(8)
        out.setsampwidth(2)
        out.setframerate(16000)
        out.writeframes(audio.tobytes())
    geometry = tmp_path / 'geometry.json'
    geometry.write_text(json.dumps({'channels': mapping, 'mic_xy_m': positions.tolist(),
                                    'calibrated': False, 'frame_id': 'synthetic'}))
    script = Path(__file__).with_name('doa_stream.py')
    command = [sys.executable, str(script), '--wav', str(wav), '--geometry', str(geometry)]
    result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=10)
    item = json.loads(result.stdout.splitlines()[0])
    assert item['state'] == 'estimate'
    assert item['calibrated'] is False
    assert item['frame_id'] == 'synthetic'
    assert abs(item['angle_deg'] - 90) <= 4


def test_mono_input_is_rejected(tmp_path):
    wav = tmp_path / 'mono.wav'
    with wave.open(str(wav), 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(16000)
        out.writeframes(np.zeros(4000, dtype='<i2').tobytes())
    geometry = tmp_path / 'geometry.json'
    geometry.write_text(json.dumps({'channels': list(range(6)), 'mic_xy_m': [[0, 0]] * 6,
                                    'calibrated': False, 'frame_id': 'synthetic'}))
    script = Path(__file__).with_name('doa_stream.py')
    command = [sys.executable, str(script), '--wav', str(wav), '--geometry', str(geometry)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert not result.stdout
