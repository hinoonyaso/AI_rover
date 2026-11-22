"""Exercise bounded video review and authorization with a synthetic clip.

합성 영상으로 영상 검토 API의 제한과 인증을 확인한다.
"""
import base64
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from fastapi import FastAPI
import httpx

sys.path.insert(0, str(Path(__file__).parent / 'backend'))
import access_control as auth
from inspection_video_routes import router

QUERY = '?red=0,0,16,16&yellow=16,0,16,16&green=32,0,16,16'
ORIGIN = 'http://127.0.0.1:8765'


class InspectionVideoTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir='/tmp')
        self.app = FastAPI()
        self.app.middleware('http')(auth.access_guard)
        self.app.include_router(router)
        self.transport = httpx.ASGITransport(app=self.app, client=('127.0.0.1', 12345))
        self.client = httpx.AsyncClient(transport=self.transport, base_url=ORIGIN)
        self.env = patch.dict(os.environ, {'JETINSPECT_LAN_IP': '', 'JETINSPECT_LAN_CIDR': ''})
        self.env.start()
        with auth.lock:
            auth.sessions['inspection-test-operator'] = ('operator', time.monotonic() + 120, 'test')
            auth.sessions['inspection-test-viewer'] = ('viewer', time.monotonic() + 120, 'test')

    async def asyncTearDown(self):
        await self.client.aclose()
        with auth.lock:
            auth.sessions.pop('inspection-test-operator', None)
            auth.sessions.pop('inspection-test-viewer', None)
        self.env.stop()
        self.tmp.cleanup()

    async def post(self, body, cookie=None, query=QUERY, origin=ORIGIN, **headers):
        h = {'Origin': origin, 'Content-Type': 'application/octet-stream', **headers}
        if cookie:
            h['Cookie'] = 'jetinspect_session=' + cookie
        return await self.client.post('/api/inspection/video-review' + query, content=body, headers=h)

    async def test_authorization_and_input_limits(self):
        self.assertEqual((await self.post(b'x')).status_code, 401)
        self.assertEqual((await self.post(b'x', 'inspection-test-viewer')).status_code, 403)
        self.assertEqual((await self.post(b'x', 'inspection-test-operator', origin='http://other')).status_code, 403)
        self.assertEqual((await self.post(b'x', 'inspection-test-operator', query='?red=x&yellow=0,0,4,4&green=0,0,4,4')).status_code, 400)
        self.assertEqual((await self.post(b'x', 'inspection-test-operator', **{'Content-Length': str(9 * 1024 * 1024)})).status_code, 413)
        self.assertEqual((await self.post(b'not a video', 'inspection-test-operator')).status_code, 400)

    async def test_synthetic_video_returns_observation_and_evidence(self):
        video = Path(self.tmp.name) / 'clip.avi'
        code = '''import cv2,numpy as np,sys
w=cv2.VideoWriter(sys.argv[1],cv2.VideoWriter_fourcc(*"MJPG"),10,(48,16))
assert w.isOpened()
for _ in range(40):
 h=np.zeros((16,48,3),dtype=np.uint8)
 for i,(color,val) in enumerate(((0,220),(27,40),(60,220))): h[:,i*16:(i+1)*16]=(color,255,val)
 w.write(cv2.cvtColor(h,cv2.COLOR_HSV2BGR))
w.release()
'''
        subprocess.run(['/usr/bin/python3', '-c', code, str(video)], check=True, timeout=10)
        response = await self.post(video.read_bytes(), 'inspection-test-operator')
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertFalse(result['real_world_validated'])
        self.assertEqual([result['states'][key]['state'] for key in ('red', 'yellow', 'green')], ['on', 'off', 'on'])
        self.assertEqual(len(result['evidence_images']), 2)
        self.assertTrue(base64.b64decode(result['evidence_images'][0]).startswith(b'\x89PNG'))
        self.assertNotIn('/tmp/', response.text)


if __name__ == '__main__':
    unittest.main()
