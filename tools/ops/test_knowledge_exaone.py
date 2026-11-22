"""Verify explicit EXAONE transfer boundaries. / EXAONE 외부 전송 경계를 검증한다."""
import sys
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
import httpx
from fastapi import FastAPI

sys.path.insert(0, str(Path(__file__).parent / 'backend'))
import knowledge_exaone
import knowledge_routes
from access_control import access_guard


class ExaoneTests(unittest.IsolatedAsyncioTestCase):
    async def test_role_consent_and_missing_evidence(self):
        app = FastAPI()
        app.middleware('http')(access_guard)
        app.include_router(knowledge_routes.router)
        store = Mock()
        store.search.return_value = []
        store.answer.return_value = '근거 없음'
        with patch('access_control.request_allowed', return_value=True), patch('access_control.same_origin', return_value=True), \
             patch.object(knowledge_routes, 'manager', return_value=store), patch.object(knowledge_exaone, 'generate') as send:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
                with patch('access_control.session_role', return_value='viewer'):
                    response = await client.post('/api/knowledge/answer/exaone', json={'q': '질문 내용', 'consent': True})
                    self.assertEqual(response.status_code, 403)
                with patch('access_control.session_role', return_value='operator'):
                    response = await client.post('/api/knowledge/answer/exaone', json={'q': '질문 내용', 'consent': False})
                    self.assertEqual(response.status_code, 400)
                    response = await client.post('/api/knowledge/answer/exaone', json={'q': '질문 내용', 'consent': True})
                    self.assertEqual(response.status_code, 200)
                    self.assertFalse(response.json()['sent'])
                    send.assert_not_called()
                    store.search.return_value = [{'source':f'doc{i}', 'classification':'test', 'text':'근거'} for i in range(5)]
                    send.return_value = {'answer': '답변 [1]', 'finish_reason':'stop'}
                    response = await client.post('/api/knowledge/answer/exaone', json={'q': '질문 내용', 'consent': True})
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(response.json()['sent'])
                    self.assertEqual(response.json()['answer'], '답변 [1]')
                    self.assertEqual(len(response.json()['results']), 3)

    def test_client_sends_only_selected_evidence_and_handles_limits(self):
        rows = [{'source':f'doc{i}', 'classification':'test', 'text':str(i)*1400} for i in range(5)]
        response = Mock(status_code=429, is_success=False)
        client = Mock()
        client.post.return_value = response
        context = Mock()
        context.__enter__ = Mock(return_value=client)
        context.__exit__ = Mock(return_value=False)
        with patch.object(knowledge_exaone, 'api_key', return_value='secret'), patch.object(knowledge_exaone.httpx, 'Client', return_value=context):
            with self.assertRaisesRegex(RuntimeError, '제한'):
                knowledge_exaone.generate('질문', rows)
            payload = client.post.call_args.kwargs['json']
            text = payload['messages'][1]['content']
            self.assertIn('[3]', text)
            self.assertNotIn('[4]', text)
            self.assertNotIn('0' * 1051, text)
            self.assertNotIn('secret', str(payload))



class AskFallbackTests(unittest.TestCase):
    """EXAONE-first answers with a local fallback. / EXAONE 우선, 로컬 대체."""
    def setUp(self):
        self.store = Mock()
        self.store.answer.return_value = '로컬 근거 답변'
        self.rows = [{'source': 'troubleshooting/012-ch341.md', 'classification': '기록', 'text': 'x'}]

    def run_ask(self, rows, provider='exaone', generate=None):
        self.store.search.return_value = rows
        with patch.object(knowledge_routes, 'manager', return_value=self.store), \
             patch.object(knowledge_exaone, 'preferred_provider', return_value=provider), \
             patch.object(knowledge_exaone, 'generate', side_effect=generate) as send:
            return knowledge_routes.ask_with_fallback('라이다 연결 방법'), send

    def test_exaone_first(self):
        result, send = self.run_ask(self.rows, generate=lambda q, r: {'answer': 'EXAONE 답', 'finish_reason': 'stop'})
        self.assertEqual((result['provider'], result['sent'], result['answer']), ('exaone', True, 'EXAONE 답'))
        send.assert_called_once()

    def test_no_evidence_is_never_sent(self):
        result, send = self.run_ask([])
        self.assertEqual((result['provider'], result['fallback_reason'], result['sent']), ('local', 'no_evidence', False))
        send.assert_not_called()

    def test_failure_and_local_setting_fall_back(self):
        def fail(q, r):
            raise RuntimeError('EXAONE 응답을 받지 못했습니다.')
        result, _ = self.run_ask(self.rows, generate=fail)
        self.assertEqual((result['provider'], result['fallback_reason'], result['answer']), ('local', 'exaone_error', '로컬 근거 답변'))
        result, send = self.run_ask(self.rows, provider='local')
        self.assertEqual(result['fallback_reason'], 'local_selected')
        send.assert_not_called()


if __name__ == '__main__':
    unittest.main()
