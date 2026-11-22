"""Verify voice boundaries and local transcription integration.

한글: 음성 요청의 경계와 로컬 전사 연동을 검증한다.
"""
import asyncio
import io
from pathlib import Path
import sys
import threading
import time
import unittest
from unittest.mock import Mock, patch
import wave

import httpx
from fastapi import FastAPI
sys.path.insert(0, str(Path(__file__).parent / 'backend'))
from access_control import access_guard
from voice_intent import interpret
import voice_routes


def wav_bytes(rate=16000, frames=16000):
    """Create a bounded test WAV. / 제한된 시험 WAV를 만든다."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(rate); f.writeframes(b'\0\0' * frames)
    return buf.getvalue()


class IntentTests(unittest.TestCase):
    def test_wake_intents_and_rejection(self):
        cases = {'모의 점검 시작해':'sleep', '로버 모의 점검 시작해':'simulation_start',
                 '로버야 모의 임무 실행해':'simulation_start', '로버 모의 임무 취소해':'simulation_cancel',
                 '로버 전진하고 모의 점검 시작해':'unsupported', '로버 가제보 주행 시작해':'unsupported',
                 '로버 배터리 상태 알려줘':'status', '로버 배터리 선택 알려줘':'status', '로버 임무 상태 알려줘':'mission_status',
                 '로버 카메라 연결 방법 알려줘':'knowledge', '로버 확인':'confirm', '로버 취소해':'dismiss',
                 '로버 조명을 켜줘':'unsupported', '제트 로버, 배터리 상태 알려줘':'status', '제트로버 확인':'confirm'}
        for text, expected in cases.items():
            with self.subTest(text=text): self.assertEqual(interpret(text)['intent'], expected)


class VoiceApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = FastAPI(); self.app.middleware('http')(access_guard); self.app.include_router(voice_routes.router)
        self.guards = [patch('access_control.request_allowed', return_value=True), patch('access_control.same_origin', return_value=True)]
        for guard in self.guards: guard.start()
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url='http://test')

    async def asyncTearDown(self):
        await self.client.aclose()
        for guard in self.guards: guard.stop()

    async def test_authorization_wav_validation_and_result(self):
        with patch('access_control.session_role', return_value='viewer'):
            self.assertEqual((await self.client.post('/api/voice/interpret', json={'text':'로버 확인'})).status_code, 403)
        with patch('access_control.session_role', return_value='operator'):
            self.assertEqual((await self.client.post('/api/voice/transcribe', content=wav_bytes(rate=8000))).status_code, 400)
            self.assertEqual((await self.client.post('/api/voice/transcribe', content=b'x'*320129)).status_code, 413)
            with patch.object(voice_routes.subprocess, 'run', return_value=Mock(stdout='로버 모의 점검 시작해\n')):
                result = await self.client.post('/api/voice/transcribe', content=wav_bytes())
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()['intent'], 'simulation_start')

    async def test_robot_microphone_routes_are_operator_only(self):
        fake = Mock(); fake.snapshot.return_value = {'running': False, 'stage': 'off'}
        with patch.object(voice_routes, '_robot', fake):
            with patch('access_control.session_role', return_value='viewer'):
                self.assertEqual((await self.client.get('/api/voice/robot')).status_code, 200)
                self.assertEqual((await self.client.post('/api/voice/robot/start')).status_code, 403)
                fake.start.assert_not_called()
            with patch('access_control.session_role', return_value='operator'):
                self.assertEqual((await self.client.post('/api/voice/robot/start')).status_code, 200)
                fake.start.assert_called_once()
                self.assertEqual((await self.client.post('/api/voice/robot/drive')).status_code, 404)

    async def test_stt_does_not_block_event_loop_and_busy_is_reported(self):
        started = asyncio.Event()
        @self.app.get('/health')
        async def health(): return {'ok':True}
        def slow(*args, **kwargs):
            time.sleep(.4); return Mock(stdout='로버 확인')
        with patch('access_control.session_role', return_value='operator'), patch.object(voice_routes.subprocess, 'run', side_effect=slow):
            pending = asyncio.create_task(self.client.post('/api/voice/transcribe', content=wav_bytes()))
            await asyncio.sleep(.05)
            begin = time.monotonic(); response = await self.client.get('/health')
            self.assertEqual(response.status_code, 200); self.assertLess(time.monotonic()-begin, .25)
            self.assertEqual((await self.client.post('/api/voice/transcribe', content=wav_bytes())).status_code, 409)
            self.assertEqual((await pending).status_code, 200)


    async def test_cancelled_request_keeps_worker_lock_and_file_until_done(self):
        observed = []; started = threading.Event()
        def slow(args, **kwargs):
            started.set(); time.sleep(.35)
            observed.append(Path(args[-1]).exists())
            return Mock(stdout='로버 확인')
        with patch('access_control.session_role', return_value='operator'), patch.object(voice_routes.subprocess, 'run', side_effect=slow):
            pending = asyncio.create_task(self.client.post('/api/voice/transcribe', content=wav_bytes()))
            for _ in range(100):
                if started.is_set(): break
                await asyncio.sleep(.01)
            self.assertTrue(started.is_set())
            pending.cancel()
            await asyncio.sleep(.06)
            self.assertTrue(voice_routes.LOCK.locked())
            with self.assertRaises(asyncio.CancelledError): await pending
            for _ in range(100):
                if not voice_routes.LOCK.locked(): break
                await asyncio.sleep(.01)
        self.assertEqual(observed, [True])
        self.assertFalse(voice_routes.LOCK.locked())


if __name__ == '__main__': unittest.main()
