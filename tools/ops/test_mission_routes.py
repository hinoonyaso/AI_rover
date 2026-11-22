"""Test the ASGI mission API against an isolated database. / 격리 DB로 임무 API를 시험한다."""
import asyncio
import json
import os
import sqlite3
from pathlib import Path
import sys
import tempfile
import unittest
from uuid import uuid4
from unittest.mock import patch

from fastapi import FastAPI
sys.path.insert(0, str(Path(__file__).parent / 'backend'))
from mission_routes import router
from mission_simulator import SimulationManager


class MissionApiTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir='/tmp')
        self.manager = SimulationManager(Path(self.tmp.name) / 'test.db')
        self.app = FastAPI()
        self.app.state.mission_manager = self.manager
        self.app.include_router(router)

    def tearDown(self):
        self.manager.close()
        self.tmp.cleanup()

    async def request(self, method, path, body=None, origin='http://127.0.0.1:8765',
                      host='127.0.0.1:8765', scheme='http', peer='127.0.0.1'):
        path, _, query = path.partition('?')
        raw = json.dumps(body).encode() if body is not None else b''
        headers = [(b'host', host.encode()), (b'content-type', b'application/json')]
        if origin is not None:
            headers.append((b'origin', origin.encode()))
        scope = {'type': 'http', 'asgi': {'version': '3.0'}, 'http_version': '1.1', 'method': method,
                 'scheme': scheme, 'path': path, 'raw_path': path.encode(), 'query_string': query.encode(),
                 'headers': headers, 'client': (peer, 12345), 'server': ('127.0.0.1', 8765)}
        sent = []
        async def receive():
            return {'type': 'http.request', 'body': raw, 'more_body': False}
        async def send(message):
            sent.append(message)
        await self.app(scope, receive, send)
        return sent[0]['status'], json.loads(b''.join(item.get('body', b'') for item in sent if item['type'] == 'http.response.body'))

    async def test_create_start_and_history(self):
        payload = {'request_id': str(uuid4()), 'mode': 'simulation', 'kind': 'inspection_demo', 'parameters': {}}
        status, mission = await self.request('POST', '/api/missions', payload)
        self.assertEqual(status, 201)
        status, duplicate = await self.request('POST', '/api/missions', payload)
        self.assertEqual((status, duplicate['id']), (200, mission['id']))
        status, queued = await self.request('POST', f"/api/missions/{mission['id']}/start", {})
        self.assertEqual((status, queued['state']), (202, 'queued'))
        self.manager.advance_active()
        self.manager.advance_active()
        status, history = await self.request('GET', f"/api/missions/{mission['id']}/events")
        self.assertEqual(status, 200)
        self.assertEqual([event['state'] for event in history['events']], ['created', 'queued', 'running', 'succeeded'])
        status, rows = await self.request('GET', '/api/missions')
        self.assertEqual(rows['missions'][0]['mode'], 'simulation')

    async def test_lan_https_can_create_and_start_simulated_mission(self):
        env = {'JETINSPECT_LAN_IP': '172.30.1.82', 'JETINSPECT_LAN_CIDR': '172.30.1.0/24'}
        opts = {'origin': 'https://172.30.1.82:8765', 'host': '172.30.1.82:8765',
                'scheme': 'https', 'peer': '172.30.1.40'}
        payload = {'request_id': str(uuid4()), 'mode': 'simulation', 'kind': 'inspection_demo', 'parameters': {}}
        with patch.dict(os.environ, env):
            status, mission = await self.request('POST', '/api/missions', payload, **opts)
            self.assertEqual(status, 201)
            status, mission = await self.request('POST', f"/api/missions/{mission['id']}/start", {}, **opts)
            self.assertEqual((status, mission['state']), (202, 'queued'))

    async def test_cursor_survives_new_mission_and_rejects_invalid(self):
        for _ in range(4):
            await self.request('POST', '/api/missions', {'request_id': str(uuid4()), 'mode': 'simulation',
                                                       'kind': 'inspection_demo', 'parameters': {}})
        _, first = await self.request('GET', '/api/missions?limit=2')
        await self.request('POST', '/api/missions', {'request_id': str(uuid4()), 'mode': 'simulation',
                                                   'kind': 'inspection_demo', 'parameters': {}})
        status, second = await self.request('GET', '/api/missions?limit=2&cursor=' + first['next_cursor'])
        self.assertEqual(status, 200)
        self.assertEqual(len(second['missions']), 2)
        self.assertTrue({m['id'] for m in first['missions']}.isdisjoint(m['id'] for m in second['missions']))
        status, _ = await self.request('GET', '/api/missions?cursor=not_valid')
        self.assertEqual(status, 400)

    async def test_origin_and_real_mode_rejected(self):
        payload = {'request_id': str(uuid4()), 'mode': 'robot', 'kind': 'inspection_demo', 'parameters': {}}
        status, response = await self.request('POST', '/api/missions', payload)
        self.assertEqual((status, response['error']['code']), (403, 'mode_unavailable'))
        payload['mode'] = 'simulation'
        for origin in ('http://evil.example', None):
            status, response = await self.request('POST', '/api/missions', payload, origin)
            self.assertEqual((status, response['error']['code']), (403, 'origin_denied'))
        self.assertEqual(self.manager.list_recent(), [])

    async def test_database_failure_recovers_without_fake_success(self):
        payload = {'request_id': str(uuid4()), 'mode': 'simulation', 'kind': 'inspection_demo', 'parameters': {}}
        with patch('mission_simulator.sqlite3.connect', side_effect=sqlite3.OperationalError('private database detail')):
            status, failure = await self.request('POST', '/api/missions', payload)
        self.assertEqual((status, failure['error']['code']), (503, 'database_unavailable'))
        self.assertNotIn('private database detail', str(failure))
        status, mission = await self.request('POST', '/api/missions', payload)
        self.assertEqual((status, mission['state']), (201, 'created'))
        self.assertEqual(len(self.manager.list_recent()), 1)

    async def test_unavailable_manager_and_repeated_start(self):
        payload = {'request_id': str(uuid4()), 'mode': 'simulation', 'kind': 'inspection_demo', 'parameters': {}}
        _, mission = await self.request('POST', '/api/missions', payload)
        path = f"/api/missions/{mission['id']}/start"
        status, first = await self.request('POST', path, {})
        repeated_status, repeated = await self.request('POST', path, {})
        self.assertEqual((status, repeated_status), (202, 200))
        self.assertEqual(first['version'], repeated['version'])
        self.app.state.mission_manager = None
        unavailable, detail = await self.request('GET', '/api/missions')
        self.assertEqual((unavailable, detail['error']['code']), (503, 'manager_unavailable'))
        self.app.state.mission_manager = self.manager

    async def test_gazebo_mission_is_distinct_from_mock(self):
        payload = {'request_id': str(uuid4()), 'mode': 'gazebo', 'kind': 'navigate_demo', 'parameters': {}}
        status, mission = await self.request('POST', '/api/missions', payload)
        self.assertEqual((status, mission['mode'], mission['kind']), (201, 'gazebo', 'navigate_demo'))
        status, queued = await self.request('POST', f"/api/missions/{mission['id']}/start", {})
        self.assertEqual((status, queued['state']), (202, 'queued'))
        self.assertIsNone(self.manager.advance_active())
        self.assertEqual(self.manager.get(mission['id'])['state'], 'queued')

    async def test_pause_resume_only_for_driving_gazebo(self):
        payload = {'request_id': str(uuid4()), 'mode': 'gazebo', 'kind': 'return_to_start', 'parameters': {}}
        status, mission = await self.request('POST', '/api/missions', payload)
        self.assertEqual(status, 201)
        mid = mission['id']
        status, _ = await self.request('POST', f'/api/missions/{mid}/pause', {})
        self.assertEqual(status, 409, 'not running yet')
        with self.manager._transaction() as conn:
            conn.execute("UPDATE missions SET state='running', stage='gazebo_returning' WHERE id=?", (mid,))
        status, _ = await self.request('POST', f'/api/missions/{mid}/pause', {})
        self.assertEqual(status, 503, 'no worker')
        sent = []
        self.app.state.gazebo_worker = type('W', (), {'send_motion': lambda self, i, c: sent.append((i, c)) or True})()
        status, body = await self.request('POST', f'/api/missions/{mid}/pause', {})
        self.assertEqual((status, body['requested']), (202, 'pause'))
        status, _ = await self.request('POST', f'/api/missions/{mid}/resume', {})
        self.assertEqual(status, 409, 'resume needs a paused stage')
        with self.manager._transaction() as conn:
            conn.execute("UPDATE missions SET stage='gazebo_paused' WHERE id=?", (mid,))
        status, _ = await self.request('POST', f'/api/missions/{mid}/resume', {})
        self.assertEqual(status, 202)
        self.assertEqual(sent, [(mid, 'pause'), (mid, 'resume')])

    async def test_cancel_needs_simulator_ack(self):
        payload = {'request_id': str(uuid4()), 'mode': 'simulation', 'kind': 'inspection_demo', 'parameters': {}}
        _, mission = await self.request('POST', '/api/missions', payload)
        await self.request('POST', f"/api/missions/{mission['id']}/start", {})
        status, pending = await self.request('POST', f"/api/missions/{mission['id']}/cancel", {})
        self.assertEqual((status, pending['state']), (202, 'cancel_requested'))
        self.assertEqual(self.manager.advance_active()['state'], 'canceled')


if __name__ == '__main__':
    unittest.main()
