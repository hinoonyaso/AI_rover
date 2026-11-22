"""Authenticated dashboard knowledge API. / 인증된 대시보드 지식 검색 API."""
import threading
import uuid
from pathlib import Path
from knowledge_archive import export_index
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field, StrictBool
import knowledge_exaone
from fastapi.responses import JSONResponse
from knowledge import Knowledge

router = APIRouter(prefix='/api/knowledge')
_instance = None
_guard = threading.Lock()
_answer_lock = threading.Lock()
BACKUP_DIR = Path.home() / '.local/share/jetinspect-ops/backups'


def manager():
    """Create the local store lazily. / 로컬 저장소를 필요할 때 생성한다."""
    global _instance
    with _guard:
        if _instance is None:
            _instance = Knowledge()
        return _instance


def failure(exc):
    """Return a bounded availability error. / 제한된 가용성 오류를 반환한다."""
    return JSONResponse({'error': str(exc)[:300]}, status_code=503)


@router.get('/status')
def status():
    """Report index availability. / 색인 상태를 반환한다."""
    try:
        return manager().status()
    except Exception as exc:
        return failure(exc)


@router.get('/chunks')
def chunks(offset: str | None = Query(default=None, max_length=80)):
    """Browse indexed chunks. / 색인 청크를 조회한다."""
    try:
        return manager().browse(offset)
    except Exception as exc:
        return failure(exc)


@router.get('/search')
def search(q: str = Query(min_length=2, max_length=300)):
    """Search for source passages. / 출처 문단을 검색한다."""
    try:
        return {'results': manager().search(q)}
    except Exception as exc:
        return failure(exc)


@router.get('/answer')
def answer(q: str = Query(min_length=2, max_length=300), mode: str = Query(default='evidence', pattern='^(evidence|generated)$')):
    """Generate a source-based local answer. / 출처 기반 로컬 답변을 생성한다."""
    if not _answer_lock.acquire(blocking=False):
        return JSONResponse({'error': '다른 AI 답변을 생성 중입니다'}, status_code=409)
    try:
        store = manager()
        results = store.search(q)
        return {'answer': store.answer(q, results, mode), 'mode': mode, 'results': results}
    except Exception as exc:
        return failure(exc)
    finally:
        _answer_lock.release()


@router.post('/rebuild')
def rebuild():
    """Start operator-requested indexing. / 운영자가 요청한 색인을 시작한다."""
    try:
        store = manager()
    except Exception as exc:
        return failure(exc)
    with _guard:
        if store.state['running'] or store.lock.locked() or _answer_lock.locked():
            return JSONResponse({'error': '색인 또는 질의가 진행 중입니다'}, status_code=409)
        store.state['running'] = True
    def run():
        try:
            store.rebuild()
        except Exception as exc:
            store.state['running'] = False
            store.state['error'] = str(exc)[:300]
    threading.Thread(target=run, daemon=True).start()
    return {'started': True}


@router.post('/backup')
def backup():
    """Back up the active index under the private user directory. / 활성 색인을 개인 디렉터리에 백업한다."""
    try:
        name = 'knowledge-' + uuid.uuid4().hex + '.json'
        result = export_index(manager(), BACKUP_DIR / name)
        return {'backup': name, **result}
    except Exception as exc:
        return failure(exc)


class ExaoneRequest(BaseModel):
    """Explicit external transfer request. / 외부 전송을 명시하는 요청이다."""
    q: str = Field(min_length=2, max_length=300)
    consent: StrictBool


@router.post('/answer/exaone')
def exaone_answer(request: ExaoneRequest):
    """Send only explicitly approved questions and excerpts. / 승인한 질문과 근거만 외부로 보낸다."""
    if not request.consent:
        return JSONResponse({'error': 'EXAONE 외부 전송 동의가 필요합니다.'}, status_code=400)
    if not _answer_lock.acquire(blocking=False):
        return JSONResponse({'error': '다른 AI 답변을 생성 중입니다'}, status_code=409)
    try:
        store = manager()
        rows = store.search(request.q)
        if not rows:
            return {'answer': store.answer(request.q, [], 'evidence'), 'mode': 'exaone', 'results': [], 'sent': False}
        response = knowledge_exaone.generate(request.q, rows)
        return {**response, 'mode': 'exaone', 'results': rows[:3], 'sent': True}
    except RuntimeError as exc:
        message = str(exc)
        if message not in ('EXAONE 요청이 제한됐습니다. 잠시 후 다시 시도하세요.', 'EXAONE API 키가 설정되지 않았습니다.'):
            message = 'EXAONE 답변을 생성하지 못했습니다. 서비스 상태와 요청 제한을 확인하세요.'
        return JSONResponse({'error': message}, status_code=503)
    except Exception:
        return JSONResponse({'error': 'EXAONE 답변을 생성하지 못했습니다. 서비스 상태를 확인하세요.'}, status_code=503)
    finally:
        _answer_lock.release()
