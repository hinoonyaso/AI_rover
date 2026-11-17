"""Local dashboard sessions and role checks. / 로컬 대시보드 세션 및 권한 검사."""
import hashlib
import hmac
import json
import os
import tempfile
import secrets
import threading
import time
from pathlib import Path

from fastapi import Request
from fastapi.responses import JSONResponse
from network_access import request_allowed, same_origin

ROOT = Path.home() / '.local/share/jetinspect-ops'
ACCOUNTS = ROOT / 'auth/accounts.json'
sessions = {}
attempts = {}
lock = threading.Lock()


def password_hash(password, salt):
    """Derive a password verifier. / 비밀번호 검증값을 계산한다."""
    return hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 600_000).hex()


def session_role(request):
    """Return the unexpired role for this session. / 유효한 세션의 권한을 반환한다."""
    token = request.cookies.get('jetinspect_session', '')
    with lock:
        entry = sessions.get(token)
        if not entry or entry[1] <= time.monotonic():
            sessions.pop(token, None)
            return None
        return entry[0]


async def access_guard(request, call_next):
    """Enforce loopback, authentication, and operator-only writes.

    한글: 루프백 접속, 로그인 및 운영자 전용 쓰기를 강제한다.
    """
    if not request_allowed(request):
        return JSONResponse({'error': 'connection_denied'}, status_code=403)
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        if not same_origin(request):
            return JSONResponse({'error': 'origin_denied'}, status_code=403)
    path = request.url.path
    if path.startswith('/api/') and path not in ('/api/session/login', '/api/session'):
        role = session_role(request)
        if not role:
            return JSONResponse({'error': 'login_required'}, status_code=401)
        if request.method not in ('GET', 'HEAD', 'OPTIONS') and path not in ('/api/session/logout', '/api/session/password') and role != 'operator':
            return JSONResponse({'error': 'operator_required'}, status_code=403)
    return await call_next(request)


async def login(request: Request):
    """Authenticate a bounded local request. / 크기가 제한된 로컬 로그인 요청을 인증한다."""
    now = time.monotonic()
    peer = request.client.host if request.client else ''
    with lock:
        for address in list(attempts):
            attempts[address] = [t for t in attempts[address] if now - t < 60]
            if not attempts[address]:
                del attempts[address]
        if len(attempts) >= 512 and peer not in attempts:
            return JSONResponse({'error': 'try_later'}, status_code=429)
        history = attempts.setdefault(peer, [])
        if len(history) >= 10:
            return JSONResponse({'error': 'try_later'}, status_code=429)
        history.append(now)
    try:
        body = b''
        async for chunk in request.stream():
            body += chunk
            if len(body) > 4096:
                raise ValueError()
        data = json.loads(body)
        user, password = data['username'], data['password']
        if not isinstance(user, str) or not isinstance(password, str) or len(password) > 256:
            raise ValueError()
        # Serialize login with password changes to prevent issuing a stale session.
        # 한글: 이전 비밀번호 확인과 세션 발급 사이의 변경 경쟁을 막는다.
        with lock:
            account = json.loads(ACCOUNTS.read_text()).get(user, {})
            verifier = password_hash(password, account.get('salt', '00' * 16))
            valid = hmac.compare_digest(verifier, account.get('hash', '')) and account.get('role') in ('viewer', 'operator')
            if not valid:
                raise ValueError()
            token = secrets.token_urlsafe(32)
            attempts.pop(peer, None)
            sessions[token] = (account['role'], time.monotonic() + 8 * 3600, user)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return JSONResponse({'error': 'invalid_credentials'}, status_code=401)
    response = JSONResponse({'role': account['role']})
    response.set_cookie('jetinspect_session', token, httponly=True, secure=request.url.scheme == 'https',
                        samesite='strict', max_age=8*3600, path='/')
    return response


def logout(request: Request):
    """Revoke the current session. / 현재 세션을 무효화한다."""
    with lock:
        sessions.pop(request.cookies.get('jetinspect_session', ''), None)
    response = JSONResponse({'ok': True})
    response.delete_cookie('jetinspect_session', path='/')
    return response


async def change_password(request: Request):
    """Change only the authenticated account and revoke its sessions.

    한글: 인증된 계정의 비밀번호만 바꾸고 해당 계정의 세션을 종료한다.
    """
    try:
        body = b''
        async for chunk in request.stream():
            body += chunk
            if len(body) > 4096:
                raise ValueError()
        data = json.loads(body)
        current, new = data['current_password'], data['new_password']
        if not isinstance(current, str) or not isinstance(new, str) or len(current) > 256 or not 12 <= len(new) <= 256:
            raise ValueError()
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return JSONResponse({'error': 'invalid_password'}, status_code=400)
    token = request.cookies.get('jetinspect_session', '')
    peer = request.client.host if request.client else ''
    with lock:
        entry = sessions.get(token)
        if not entry or len(entry) < 3 or entry[1] <= time.monotonic():
            sessions.pop(token, None)
            return JSONResponse({'error': 'login_required'}, status_code=401)
        now = time.monotonic()
        history = [stamp for stamp in attempts.get(peer, []) if now - stamp < 60]
        if len(history) >= 10:
            return JSONResponse({'error': 'try_later'}, status_code=429)
        attempts[peer] = history + [now]
        username = entry[2]
        try:
            accounts = json.loads(ACCOUNTS.read_text())
            account = accounts[username]
            verifier = password_hash(current, account['salt'])
            if not hmac.compare_digest(verifier, account['hash']):
                return JSONResponse({'error': 'invalid_current_password'}, status_code=400)
            if current == new:
                return JSONResponse({'error': 'password_unchanged'}, status_code=400)
            salt = secrets.token_hex(16)
            accounts[username] = {**account, 'salt': salt, 'hash': password_hash(new, salt)}
            # Use a private, unique temporary file and replace the account file atomically.
            # 한글: 사용자 전용 임시 파일을 사용해 계정 파일을 원자적으로 교체한다.
            fd, temporary = tempfile.mkstemp(prefix='.accounts-', dir=ACCOUNTS.parent)
            try:
                with os.fdopen(fd, 'w') as output:
                    json.dump(accounts, output)
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, ACCOUNTS)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
            for key, value in list(sessions.items()):
                if len(value) >= 3 and value[2] == username:
                    sessions.pop(key, None)
            attempts.pop(peer, None)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            return JSONResponse({'error': 'password_update_failed'}, status_code=503)
    response = JSONResponse({'ok': True})
    response.delete_cookie('jetinspect_session', path='/')
    return response
