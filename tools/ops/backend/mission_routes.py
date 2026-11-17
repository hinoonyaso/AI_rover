"""HTTP interface for simulation only. / 모의 임무 전용 HTTP 인터페이스."""
import json
import os
import sqlite3
import pymysql
from uuid import UUID

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from mission_contract import ContractError
from page_cursor import decode_cursor, encode_cursor
from network_access import request_allowed, same_origin

router = APIRouter(prefix='/api/missions')


def response_error(code, status):
    """Return a stable error without internal details. / 내부 정보 없는 오류를 반환한다."""
    return JSONResponse({'error': {'code': code, 'message': code}}, status_code=status)


def manager(request):
    """Obtain the owned simulation manager. / 소유 중인 모의 관리자를 가져온다."""
    result = getattr(request.app.state, 'mission_manager', None)
    if result is None:
        raise ContractError('manager_unavailable')
    return result


def require_origin(request):
    """Restrict writes to same-origin loopback browser requests.

    한글: 쓰기는 동일 출처의 루프백 브라우저 요청으로 제한한다.
    """
    port = getattr(request.app.state, 'mission_allowed_port', 8765)
    host = request.headers.get('host', '').lower()
    permitted = request_allowed(request) if os.environ.get('JETINSPECT_LAN_IP') else (
        request.url.scheme == 'http' and host in (f'127.0.0.1:{port}', f'localhost:{port}'))
    if not permitted or not same_origin(request):
        raise ContractError('origin_denied')
    if request.headers.get('content-type', '').split(';', 1)[0].strip().lower() != 'application/json':
        raise ContractError('invalid_request')


def serialize(row):
    """Decode structured mission fields. / 임무 JSON 필드를 디코딩한다."""
    output = dict(row)
    for field in ('parameters', 'result'):
        if output.get(field) is not None:
            output[field] = json.loads(output[field])
    return output


def valid_id(value):
    """Check canonical mission IDs. / 표준 형식의 임무 ID를 검증한다."""
    try:
        if str(UUID(value)) != value:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise ContractError('invalid_request_id') from None
    return value


async def payload(request):
    """Read a bounded JSON request. / 크기가 제한된 JSON 요청을 읽는다."""
    require_origin(request)
    body = await request.body()
    if len(body) > 4096:
        raise ContractError('invalid_request')
    try:
        return json.loads(body)
    except (ValueError, UnicodeError):
        raise ContractError('invalid_request') from None


def handle(error):
    """Map expected failures to public responses. / 예상 오류를 공개 응답으로 변환한다."""
    if isinstance(error, (sqlite3.Error, pymysql.Error)):
        return response_error('database_unavailable', 503)
    code = error.code
    status = {'mode_unavailable': 403, 'origin_denied': 403, 'mission_not_found': 404,
              'idempotency_conflict': 409, 'invalid_transition': 409, 'mission_busy': 409,
              'manager_unavailable': 503}.get(code, 400)
    return response_error(code, status)


@router.get('')
def list_missions(request: Request, offset: int = Query(default=0, ge=0, le=100000),
                  limit: int = Query(default=50, ge=1, le=100), cursor: str | None = Query(default=None, max_length=256)):
    """List recent simulated missions. / 최근 모의 임무 목록을 조회한다."""
    try:
        try:
            key = decode_cursor(cursor) if cursor else None
        except ValueError:
            raise ContractError('invalid_request') from None
        rows = manager(request).list_recent(limit=limit + 1, offset=offset, before=key)
        page = rows[:limit]
        next_cursor = encode_cursor([page[-1]['created_at'], page[-1]['id']]) if len(rows) > limit and page else None
        return {'missions': [serialize(row) for row in page], 'next_cursor': next_cursor,
                'next_offset': offset + limit if len(rows) > limit else None}
    except (ContractError, sqlite3.Error, pymysql.Error) as exc:
        return handle(exc)


@router.post('')
async def create_mission(request: Request):
    """Create an idempotent mock mission. / 중복을 방지하며 모의 임무를 생성한다."""
    try:
        data = await payload(request)
        row, created = manager(request).create(data)
        return JSONResponse(serialize(row), status_code=201 if created else 200)
    except (ContractError, sqlite3.Error, pymysql.Error) as exc:
        return handle(exc)


@router.get('/{mission_id}')
def get_mission(mission_id: str, request: Request):
    """Read a mock mission. / 모의 임무를 조회한다."""
    try:
        return serialize(manager(request).get(valid_id(mission_id)))
    except (ContractError, sqlite3.Error, pymysql.Error) as exc:
        return handle(exc)


@router.get('/{mission_id}/events')
def mission_events(mission_id: str, request: Request):
    """Read mock mission events. / 모의 임무 이력을 조회한다."""
    try:
        return {'events': manager(request).events(valid_id(mission_id))}
    except (ContractError, sqlite3.Error, pymysql.Error) as exc:
        return handle(exc)


@router.post('/{mission_id}/{command}')
async def mission_command(mission_id: str, command: str, request: Request):
    """Start or cancel a simulated mission. / 모의 임무의 시작 또는 취소를 요청한다."""
    try:
        if command not in ('start', 'cancel'):
            return response_error('not_found', 404)
        if await payload(request) != {}:
            raise ContractError('invalid_request')
        service = manager(request)
        mission_id = valid_id(mission_id)
        row, changed = service.start(mission_id, include_changed=True) if command == 'start' else service.cancel(mission_id, include_changed=True)
        accepted = changed and (command == 'start' or row['state'] == 'cancel_requested')
        return JSONResponse(serialize(row), status_code=202 if accepted else 200)
    except (ContractError, sqlite3.Error, pymysql.Error) as exc:
        return handle(exc)
