"""Verify session and role boundaries. / 세션과 권한 경계를 검증한다."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from starlette.requests import Request
from starlette.responses import JSONResponse

sys.path.insert(0, str(Path(__file__).parent / 'backend'))
import access_control as auth


def request(method, path, body=None, cookie=None, origin='http://127.0.0.1:8765',
            host='127.0.0.1:8765', scheme='http', peer='127.0.0.1'):
    raw = json.dumps(body).encode() if body else b''
    headers = [(b'host', host.encode()), (b'origin', origin.encode()), (b'content-type', b'application/json')]
    if cookie:
        headers.append((b'cookie', cookie.encode()))
    scope = {'type': 'http', 'method': method, 'path': path, 'headers': headers,
             'client': (peer, 1234), 'server': ('127.0.0.1', 8765), 'scheme': scheme, 'query_string': b''}
    async def receive():
        return {'type': 'http.request', 'body': raw, 'more_body': False}
    return Request(scope, receive)


class AccessTests(unittest.IsolatedAsyncioTestCase):
    async def test_lan_https_network_host_and_origin(self):
        async def allowed(req):
            return JSONResponse({'ok': True})
        env = {'JETINSPECT_LAN_IP': '172.30.1.82', 'JETINSPECT_LAN_CIDR': '172.30.1.0/24'}
        with patch.dict(os.environ, env):
            def req(**changes):
                kwargs = {'host': '172.30.1.82:8765', 'scheme': 'https',
                          'peer': '172.30.1.40', 'origin': 'https://172.30.1.82:8765'}
                kwargs.update(changes)
                return request('POST', '/api/session/login', **kwargs)
            self.assertEqual((await auth.access_guard(req(), allowed)).status_code, 200)
            for changes in ({'peer': '172.30.2.40'}, {'host': 'evil.example:8765'},
                            {'scheme': 'http'}, {'origin': 'https://evil.example'}):
                with self.subTest(changes=changes):
                    self.assertEqual((await auth.access_guard(req(**changes), allowed)).status_code, 403)

    async def test_login_roles_origin_and_logout(self):
        salt = 'ab' * 16
        users = {role: {'role': role, 'salt': salt, 'hash': auth.password_hash('example-password', salt)}
                 for role in ('viewer', 'operator')}
        async def allowed(req):
            return JSONResponse({'ok': True})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'accounts.json'
            path.write_text(json.dumps(users))
            with patch.object(auth, 'ACCOUNTS', path):
                self.assertEqual((await auth.access_guard(request('GET', '/api/read'), allowed)).status_code, 401)
                self.assertEqual((await auth.login(request('POST', '/api/session/login', {'username': 'viewer', 'password': 'wrong'}))).status_code, 401)
                response = await auth.login(request('POST', '/api/session/login', {'username': 'viewer', 'password': 'example-password'}))
                cookie = response.headers['set-cookie'].split(';', 1)[0]
                self.assertEqual((await auth.access_guard(request('GET', '/api/read', cookie=cookie), allowed)).status_code, 200)
                self.assertEqual((await auth.access_guard(request('POST', '/api/write', cookie=cookie), allowed)).status_code, 403)
                auth.logout(request('POST', '/api/session/logout', cookie=cookie))
                self.assertEqual((await auth.access_guard(request('GET', '/api/read', cookie=cookie), allowed)).status_code, 401)
                response = await auth.login(request('POST', '/api/session/login', {'username': 'operator', 'password': 'example-password'}))
                cookie = response.headers['set-cookie'].split(';', 1)[0]
                self.assertEqual((await auth.access_guard(request('POST', '/api/write', cookie=cookie), allowed)).status_code, 200)
                self.assertEqual((await auth.access_guard(request('POST', '/api/write', cookie=cookie, origin='http://evil.example'), allowed)).status_code, 403)
                secure = await auth.login(request('POST', '/api/session/login', {'username': 'operator', 'password': 'example-password'}, scheme='https'))
                self.assertIn('Secure', secure.headers['set-cookie'])

    async def test_password_change_verifies_current_and_revokes_only_own_sessions(self):
        salt = 'ab' * 16
        users = {role: {'role': role, 'salt': salt, 'hash': auth.password_hash('old-password-123', salt)}
                 for role in ('viewer', 'operator')}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'accounts.json'
            path.write_text(json.dumps(users))
            with patch.object(auth, 'ACCOUNTS', path), patch.dict(auth.sessions, {}, clear=True), patch.dict(auth.attempts, {}, clear=True):
                login1 = await auth.login(request('POST', '/api/session/login', {'username':'viewer', 'password':'old-password-123'}))
                login2 = await auth.login(request('POST', '/api/session/login', {'username':'viewer', 'password':'old-password-123'}))
                admin = await auth.login(request('POST', '/api/session/login', {'username':'operator', 'password':'old-password-123'}))
                cookie1 = login1.headers['set-cookie'].split(';', 1)[0]
                cookie2 = login2.headers['set-cookie'].split(';', 1)[0]
                admin_cookie = admin.headers['set-cookie'].split(';', 1)[0]
                async def allowed(req): return JSONResponse({'ok': True})
                self.assertEqual((await auth.access_guard(request('POST', '/api/session/password', cookie=cookie1), allowed)).status_code, 200)
                bad = await auth.change_password(request('POST', '/api/session/password', {'current_password':'wrong', 'new_password':'new-password-123'}, cookie=cookie1))
                self.assertEqual(bad.status_code, 400)
                self.assertEqual(auth.session_role(request('GET', '/api/read', cookie=cookie1)), 'viewer')
                short = await auth.change_password(request('POST', '/api/session/password', {'current_password':'old-password-123', 'new_password':'short'}, cookie=cookie1))
                self.assertEqual(short.status_code, 400)
                success = await auth.change_password(request('POST', '/api/session/password', {'current_password':'old-password-123', 'new_password':'새로운-비밀번호-12345'}, cookie=cookie1))
                self.assertEqual(success.status_code, 200)
                self.assertIsNone(auth.session_role(request('GET', '/api/read', cookie=cookie1)))
                self.assertIsNone(auth.session_role(request('GET', '/api/read', cookie=cookie2)))
                self.assertEqual(auth.session_role(request('GET', '/api/read', cookie=admin_cookie)), 'operator')
                self.assertEqual((await auth.login(request('POST', '/api/session/login', {'username':'viewer', 'password':'old-password-123'}))).status_code, 401)
                self.assertEqual((await auth.login(request('POST', '/api/session/login', {'username':'viewer', 'password':'새로운-비밀번호-12345'}))).status_code, 200)
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)


if __name__ == '__main__':
    unittest.main()
