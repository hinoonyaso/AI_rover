"""Offline routing and image privacy tests. / 분기와 이미지 전송 조건 오프라인 시험."""
import base64
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

import router


class RouterTests(unittest.TestCase):
    def test_rules_and_classifier(self):
        classifier = Mock(return_value='cloud')
        self.assertEqual(router.classify('내 앞에 뭐가 보여?', classifier), 'vision')
        self.assertEqual(router.classify('자세히 분석해줘', classifier), 'cloud')
        self.assertEqual(router.classify('안녕하세요', classifier), 'local')
        self.assertEqual(router.classify('오늘 날씨 알려줘', classifier), 'cloud')
        self.assertEqual(router.classify('안녕', lambda _: 'other'), 'local')

    def test_graph_routes_and_permission_gates(self):
        local, cloud, vision, capture = (Mock(return_value=x) for x in ('local-ok', 'cloud-ok', 'vision-ok', None))
        graph = router.build_graph(local, cloud, lambda _: 'local', vision, capture)
        state = {'text': '안녕', 'route': 'auto'}
        self.assertEqual(graph.invoke(state)['reply'], 'local-ok')
        state.update(route='cloud', allow_cloud=False)
        self.assertIn('허용', graph.invoke(state)['reply'])
        cloud.assert_not_called()
        state['allow_cloud'] = True
        self.assertEqual(graph.invoke(state)['reply'], 'cloud-ok')
        state.update(route='vision', allow_images=False, camera=True)
        self.assertIn('허용', graph.invoke(state)['reply'])
        capture.assert_not_called()
        state['allow_images'] = True
        self.assertEqual(graph.invoke(state)['reply'], 'vision-ok')
        capture.assert_called_once()

    def test_cloud_error_does_not_leak_or_switch(self):
        cloud = Mock(side_effect=RuntimeError('secret'))
        graph = router.build_graph(Mock(), cloud, lambda _: 'cloud')
        result = graph.invoke({'text': '요청', 'route': 'auto', 'allow_cloud': True})
        self.assertIn('실패', result['reply'])
        self.assertNotIn('secret', result['reply'])

    def test_vision_sends_image_to_configured_endpoint(self):
        calls = {}
        class Client:
            def __init__(self, **kwargs):
                calls['client'] = kwargs
                self.chat = types.SimpleNamespace(completions=self)
            def create(self, **kwargs):
                calls['request'] = kwargs
                return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content='사과'))])
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / 'image.png'
            payload = b'\x89PNG\r\n\x1a\nexample'
            image.write_bytes(payload)
            with patch('openai.OpenAI', Client), patch.dict(os.environ, {'VOICE_VISION_API_KEY': 'fake', 'VOICE_VISION_BASE_URL': 'https://example.test/v1', 'VOICE_VISION_MODEL': 'vision'}):
                self.assertEqual(router.vision_reply('무엇?', image), '사과')
            url = calls['request']['messages'][1]['content'][1]['image_url']['url']
            self.assertEqual(base64.b64decode(url.split(',')[1]), payload)
            self.assertEqual(calls['request']['model'], 'vision')

    def test_reject_bad_image_before_network(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / 'bad.jpg'
            image.write_bytes(b'not an image')
            with patch.dict(os.environ, {'VOICE_VISION_API_KEY': 'fake'}), patch('openai.OpenAI') as client:
                with self.assertRaises(ValueError):
                    router.vision_reply('무엇?', image)
                client.assert_not_called()


if __name__ == '__main__':
    unittest.main()
