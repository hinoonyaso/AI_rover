"""Offline checks for cloud routing and audio input validation.

한글: 클라우드 선택 및 오디오 입력 검증을 네트워크 없이 시험한다.
"""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import wave

spec = importlib.util.spec_from_file_location('voice_tool', Path(__file__).with_name('voice.py'))
voice = importlib.util.module_from_spec(spec)
spec.loader.exec_module(voice)


class VoiceTests(unittest.TestCase):
    def test_cloud_requires_key(self):
        with patch.dict(os.environ, {'VOICE_CLOUD_API_KEY': ''}):
            with self.assertRaisesRegex(ValueError, '키가 없습니다'):
                voice.cloud_reply('시험')

    def test_cloud_routes_to_configured_provider(self):
        calls = {}

        class FakeClient:
            def __init__(self, **kwargs):
                calls['client'] = kwargs
                self.chat = types.SimpleNamespace(completions=self)

            def create(self, **kwargs):
                calls['request'] = kwargs
                return types.SimpleNamespace(choices=[types.SimpleNamespace(
                    message=types.SimpleNamespace(content='안녕하세요'))])

        module = types.SimpleNamespace(OpenAI=FakeClient)
        values = {'VOICE_CLOUD_API_KEY': 'fake-secret',
                  'VOICE_CLOUD_BASE_URL': 'https://example.test/v1',
                  'VOICE_CLOUD_MODEL': 'fake-model'}
        with patch.dict(sys.modules, {'openai': module}), patch.dict(os.environ, values):
            self.assertEqual(voice.cloud_reply('테스트'), '안녕하세요')
        self.assertEqual(calls['client']['base_url'], values['VOICE_CLOUD_BASE_URL'])
        self.assertEqual(calls['request']['model'], 'fake-model')
        self.assertEqual(calls['request']['messages'][1]['content'], '테스트')

    def test_real_sdk_uses_compatible_endpoint_without_network(self):
        import httpx
        import openai

        requests = []

        def fake_http(request):
            requests.append(request)
            return httpx.Response(200, json={
                'id': 'test', 'object': 'chat.completion', 'created': 1,
                'model': 'test', 'choices': [{'index': 0, 'finish_reason': 'stop',
                                              'message': {'role': 'assistant',
                                                          'content': '테스트 응답'}}]})

        client_class = openai.OpenAI
        http_client = httpx.Client(transport=httpx.MockTransport(fake_http))

        def client_factory(**kwargs):
            return client_class(http_client=http_client, **kwargs)

        values = {'VOICE_CLOUD_API_KEY': 'fake-secret',
                  'VOICE_CLOUD_BASE_URL': 'https://example.test/openai/v1',
                  'VOICE_CLOUD_MODEL': 'fake-model'}
        with patch.object(openai, 'OpenAI', client_factory), patch.dict(os.environ, values):
            self.assertEqual(voice.cloud_reply('안녕'), '테스트 응답')
        self.assertEqual(str(requests[0].url), 'https://example.test/openai/v1/chat/completions')
        self.assertEqual(requests[0].headers['authorization'], 'Bearer fake-secret')
        http_client.close()

    def test_bad_wav_format_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.wav'
            with wave.open(str(path), 'wb') as f:
                f.setnchannels(2)
                f.setsampwidth(2)
                f.setframerate(16000)
                f.writeframes(b'\0' * 64)
            with self.assertRaisesRegex(ValueError, '모노'):
                voice.transcribe(path)


if __name__ == '__main__':
    unittest.main()
