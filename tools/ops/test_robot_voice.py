"""Robot-microphone voice worker tests with fake serial/microphone/STT; no hardware.

한글: 가짜 시리얼·마이크·STT로 로봇 마이크 음성 작업자를 시험한다. 하드웨어를 쓰지 않는다.
"""
import json
from pathlib import Path
import struct
import sys
import time
import unittest

sys.path.insert(0, str(Path(__file__).parent / 'backend'))
from robot_voice import hallucinated, RobotVoice, segment_command  # noqa: E402
from r818_doa import SYNC  # noqa: E402


def frame(msg_type, msg_id, payload):
    body = bytes((SYNC, 1, msg_type)) + len(payload).to_bytes(2, 'little') + msg_id.to_bytes(2, 'little') + payload
    return body + bytes((-sum(body) & 0xFF,))


def wake_frame(angle=90.0):
    info = json.dumps({'ivw': {'angle': angle, 'score': 600.0, 'keyword': 'hello hi wonder'}})
    return frame(4, 1, json.dumps({'type': 'aiui_event', 'content': {'eventType': 4, 'info': info}}).encode())


def tone_frames(loud=40, quiet=60, amplitude=3000):
    loud_frame = struct.pack('<320h', *([amplitude, -amplitude] * 160))
    return [b'\0' * 640] * 5 + [loud_frame] * loud + [b'\0' * 640] * quiet


class FakeSerial:
    def __init__(self, chunks):
        self.chunks, self.written = list(chunks), []

    def read(self, _):
        time.sleep(0.01)
        return self.chunks.pop(0) if self.chunks else b''

    def write(self, data):
        self.written.append(data)

    def reset_input_buffer(self):
        pass

    def close(self):
        pass


class FakeMissions:
    def __init__(self, rows=()):
        self.rows, self.calls = list(rows), []

    def create(self, payload):
        self.calls.append(('create', payload['mode'], payload['kind']))
        row = {'id': 'a' * 32, 'mode': 'simulation', 'state': 'created'}
        self.rows.append(row)
        return row, True

    def start(self, mission_id):
        self.calls.append(('start', mission_id))

    def cancel(self, mission_id):
        self.calls.append(('cancel', mission_id))

    def get(self, mission_id):
        return next(r for r in self.rows if r['id'] == mission_id)

    def list_recent(self, limit=50):
        return list(self.rows)


def worker(missions=None, transcripts=(), **kwargs):
    spoken = []
    texts = list(transcripts)
    voice = RobotVoice(
        missions=lambda: missions,
        status=lambda: {'robot': {'battery_voltage': 12.34, 'streams': {'imu': {'age_seconds': 0.4}}}},
        knowledge=lambda q: [{'source': 'troubleshooting/012-ch341.md'}] if 'lidar' in q.lower() or '라이다' in q else [],
        transcribe=lambda wav: texts.pop(0),
        record=lambda: tone_frames(), speak=spoken.append, beep=lambda: None, **kwargs)
    return voice, spoken


class SegmentTests(unittest.TestCase):
    def test_speech_is_cut_and_silence_is_none(self):
        pcm = segment_command(tone_frames())
        self.assertIsNotNone(pcm)
        self.assertGreaterEqual(len(pcm) // 640, 40)
        self.assertIsNone(segment_command([b'\0' * 640] * 300))

    def test_beep_echo_and_short_click_are_not_speech(self):
        loud = struct.pack('<320h', *([9000, -9000] * 160))
        # beep echo inside the skipped window, then a 5-frame click: not a command
        # 한글: 건너뛰는 구간의 비프 잔향과 5프레임 잡음은 명령이 아니다.
        self.assertIsNone(segment_command([loud] * 6 + [b'\0' * 640] * 5 + [loud] * 5 + [b'\0' * 640] * 80))

    def test_hallucination_filter(self):
        for text in ('[구독]', '(박수)', '-뭐야. -뭐야. -뭐야. -뭐야.', '  '):
            self.assertTrue(hallucinated(text), text)
        for text in ('모의 점검 시작해.', '확인.', '배터리 상태 알려줘.'):
            self.assertFalse(hallucinated(text), text)


class HandleTests(unittest.TestCase):
    def test_status_and_knowledge(self):
        voice, _ = worker()
        reply = voice.handle({'intent': 'status', 'command': '배터리 상태'})
        self.assertIn('12.3 볼트', reply)
        self.assertIn('IMU 수신 중', reply)
        self.assertIn('라이다 수신 미확인', reply)
        self.assertIn('012-ch341.md', voice.handle({'intent': 'knowledge', 'command': '라이다 연결 방법'}))
        self.assertIn('찾지 못했습니다', voice.handle({'intent': 'knowledge', 'command': '점심 메뉴 설명'}))

    def test_start_needs_confirmation_and_runs_once(self):
        missions = FakeMissions()
        voice, _ = worker(missions)
        voice.handle({'intent': 'simulation_start', 'command': '모의 점검 시작해'})
        self.assertEqual(missions.calls, [])
        self.assertEqual(voice.snapshot()['pending']['kind'], 'start')
        self.assertIn('시작했습니다', voice.handle({'intent': 'confirm', 'command': '확인'}))
        self.assertEqual(missions.calls, [('create', 'simulation', 'inspection_demo'), ('start', 'a' * 32)])
        self.assertIn('없습니다', voice.confirm())
        self.assertEqual(len(missions.calls), 2)

    def test_pending_expires(self):
        now = [0.0]
        missions = FakeMissions()
        voice, _ = worker(missions, clock=lambda: now[0])
        voice.handle({'intent': 'simulation_start', 'command': '모의 점검 시작해'})
        now[0] = 31.0
        self.assertIn('없습니다', voice.confirm())
        self.assertEqual(missions.calls, [])

    def test_cancel_only_single_active_simulation(self):
        rows = [{'id': 'b' * 32, 'mode': 'simulation', 'state': 'running'},
                {'id': 'c' * 32, 'mode': 'gazebo', 'state': 'running'}]
        missions = FakeMissions(rows)
        voice, _ = worker(missions)
        voice.handle({'intent': 'simulation_cancel', 'command': '모의 임무 취소'})
        voice.confirm()
        self.assertEqual(missions.calls, [('cancel', 'b' * 32)])
        missions.rows.append({'id': 'd' * 32, 'mode': 'simulation', 'state': 'queued'})
        self.assertIn('한 개로 확인되지', voice.handle({'intent': 'simulation_cancel', 'command': '모의 임무 취소'}))

    def test_real_motion_and_missing_store(self):
        voice, _ = worker(None)
        self.assertIn('지원하지 않는', voice.handle({'intent': 'unsupported', 'command': '앞으로 주행'}))
        voice.handle({'intent': 'simulation_start', 'command': '모의 점검 시작'})
        self.assertIn('연결되지 않았습니다', voice.confirm())


class LoopTests(unittest.TestCase):
    def test_wake_record_transcribe_reply(self):
        handshake = bytes.fromhex('a5 01 01 04 00 00 00 a5 00 00 00 b0')
        port = FakeSerial([handshake, wake_frame(45.0)])
        voice, spoken = worker(FakeMissions(), transcripts=['배터리 상태 알려줘'],
                               open_serial=lambda: port)
        voice.start()
        deadline = time.monotonic() + 3
        while not voice.snapshot()['history'] and time.monotonic() < deadline:
            time.sleep(0.02)
        voice.stop()
        history = voice.snapshot()['history']
        self.assertEqual(history[0]['intent'], 'status')
        self.assertEqual(history[0]['angle'], 45.0)
        # 45° device = 45-146 = -101° robot (right) with the 2026-11-22 calibration
        self.assertEqual((history[0]['bearing'], history[0]['direction']), (-101, '오른쪽'))
        self.assertIn('배터리 전압은 12.3 볼트', spoken[0])
        self.assertTrue(port.written, 'frames must be acknowledged')
        self.assertEqual(voice.snapshot()['stage'], 'off')

    def test_serial_failure_is_reported(self):
        def broken():
            raise OSError('no such device')
        voice, _ = worker(open_serial=broken)
        voice.start()
        voice.thread.join(2)
        state = voice.snapshot()
        self.assertEqual(state['stage'], 'error')
        self.assertIn('no such device', state['error'])


if __name__ == '__main__':
    unittest.main()
