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


if __name__ == '__main__':
    unittest.main()
