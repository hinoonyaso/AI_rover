"""Verify isolated knowledge indexing and failure recovery. / 격리 색인 및 실패 복구를 검증한다."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent / 'backend'))
import knowledge


class Embedder:
    """Small deterministic test encoder. / 결정적인 시험용 임베딩 인코더."""
    def embed(self, texts, **kwargs):
        import numpy as np
        for text in texts:
            v = np.zeros(384, dtype='float32'); v[0] = 1
            yield v
    def query_embed(self, text):
        return self.embed([text])


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'safe.md').write_text('라이다 센서 연결 점검')
        (self.root / '.env').write_text('SECRET=do-not-index')
        (self.root / 'link.md').symlink_to(self.root / '.env')
        self.sources = patch.dict(knowledge.SOURCES, {'safe.md': '시험', 'link.md': '시험'}, clear=True)
        self.sources.start()
        self.db = knowledge.Knowledge(self.root / 'data', self.root, Embedder())

    def tearDown(self):
        self.db.client.close(); self.sources.stop(); self.tmp.cleanup()

    def test_index_search_and_exclude_links(self):
        self.db.rebuild()
        self.assertEqual(self.db.status()['chunks'], 1)
        self.assertEqual(self.db.search('라이다')[0]['source'], 'safe.md')
        self.assertNotIn('SECRET', str(self.db.browse()))

    def test_failed_rebuild_preserves_active_generation(self):
        self.db.rebuild(); original = self.db.active()
        with patch.object(self.db, 'documents', side_effect=ValueError('failure')):
            with self.assertRaises(ValueError): self.db.rebuild()
        self.assertEqual(self.db.active(), original)
        self.assertEqual(len(self.db.search('라이다')), 1)
        self.assertEqual(self.db.status()['error'], 'failure')

    def test_no_evidence_answer(self):
        self.assertIn('근거를 찾지 못', self.db.answer('질문', []))

    def test_neighbor_context_uses_indexed_revision(self):
        original = '시작내용' + '가' * 310 + '라이다수신문제 ' + '나' * 310 + '필요한인접근거' + '다' * 310
        (self.root / 'safe.md').write_text(original)
        self.db.rebuild()
        (self.root / 'safe.md').write_text('색인후비공개변경')
        results = self.db.search('라이다수신문제')
        self.assertTrue(results)
        self.assertIn('필요한인접근거', results[0]['text'])
        self.assertNotIn('색인후비공개변경', results[0]['text'])

    def test_current_readings_are_not_answered_from_documents(self):
        self.db.rebuild()
        for question in ('현재 배터리 전압은?', '지금 로봇 위치는?'):
            self.assertEqual(self.db.search(question), [])
            self.assertIn('실시간 상태', self.db.answer(question, []))

    def test_default_answer_quotes_only_indexed_text(self):
        self.db.rebuild()
        results = self.db.search('라이다')
        answer = self.db.answer('라이다', results)
        self.assertIn(results[0]['text'], answer)
        self.assertIn(results[0]['source'], answer)

if __name__ == '__main__': unittest.main()

class KnowledgeApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_access_and_search(self):
        import httpx
        from fastapi import FastAPI
        from access_control import access_guard
        import knowledge_routes
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        (root / 'safe.md').write_text('라이다 수신을 확인하세요')
        with patch.dict(knowledge.SOURCES, {'safe.md': '시험'}, clear=True):
            db = knowledge.Knowledge(root / 'data', root, Embedder())
            db.rebuild()
            app = FastAPI(); app.middleware('http')(access_guard); app.include_router(knowledge_routes.router)
            with patch.object(knowledge_routes, '_instance', db), patch('access_control.request_allowed', return_value=True), patch('access_control.same_origin', return_value=True):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
                    with patch('access_control.session_role', return_value=None):
                        self.assertEqual((await client.get('/api/knowledge/status')).status_code, 401)
                    with patch('access_control.session_role', return_value='viewer'):
                        self.assertEqual((await client.post('/api/knowledge/rebuild')).status_code, 403)
                        response = await client.get('/api/knowledge/search', params={'q': '라이다'})
                        self.assertEqual(response.status_code, 200)
                        self.assertEqual(response.json()['results'][0]['source'], 'safe.md')
                        answer = await client.get('/api/knowledge/answer', params={'q': '라이다'})
                        self.assertEqual(answer.json()['mode'], 'evidence')
                        self.assertIn('라이다 수신을 확인하세요', answer.json()['answer'])
                        invalid = await client.get('/api/knowledge/answer', params={'q': '라이다', 'mode': 'invalid'})
                        self.assertEqual(invalid.status_code, 422)
            db.client.close()
        tmp.cleanup()
