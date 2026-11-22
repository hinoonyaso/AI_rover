"""Export and restore a local knowledge generation without overwriting active data.

한글: 활성 데이터를 덮어쓰지 않고 로컬 지식 색인 세대를 내보내고 복원한다.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile

from qdrant_client import QdrantClient, models

FORMAT = 1
MAX_ARCHIVE_BYTES = 128 * 1024 * 1024


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def export_index(knowledge, path):
    """Write a verified active-generation archive. / 활성 색인을 검증 가능한 백업으로 저장한다."""
    from knowledge import MODEL
    if not knowledge.lock.acquire(blocking=False):
        raise RuntimeError('색인 또는 질의가 진행 중입니다')
    try:
        name = knowledge.active()
        if not name or not knowledge.client.collection_exists(name):
            raise ValueError('활성 색인이 없습니다')
        points, offset = [], None
        while True:
            page, offset = knowledge.client.scroll(name, limit=100, offset=offset, with_payload=True, with_vectors=True)
            points.extend({'id': row.id, 'payload': row.payload, 'vector': row.vector} for row in page)
            if offset is None:
                break
        if len(points) != knowledge.client.count(name, exact=True).count:
            raise RuntimeError('색인 크기가 백업 중 변경됐습니다')
        body = {'format': FORMAT, 'model': MODEL, 'collection': name, 'dimensions': 384, 'points': points}
        archive = {'data': body, 'sha256': hashlib.sha256(_canonical(body)).hexdigest()}
        raw = _canonical(archive)
        if len(raw) > MAX_ARCHIVE_BYTES:
            raise ValueError('백업 크기 제한 초과')
        path = Path(path)
        if path.exists() or path.is_symlink():
            raise FileExistsError('기존 백업을 덮어쓰지 않습니다')
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix='.knowledge-', dir=path.parent)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, 'wb') as out:
                out.write(raw); out.flush(); os.fsync(out.fileno())
            # link is atomic and fails if a concurrent process created the destination.
            # 한글: 다른 프로세스가 같은 이름을 만들면 덮어쓰지 않고 실패한다.
            os.link(tmp, path)
        finally:
            os.unlink(tmp)
        return {'collection': name, 'points': len(points), 'sha256': archive['sha256']}
    finally:
        knowledge.lock.release()


def restore_index(path, destination):
    """Restore into a new directory only. / 새 디렉터리에만 복원한다."""
    from knowledge import MODEL
    path, destination = Path(path), Path(destination)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError('유효한 백업 파일이 아닙니다')
    archive = json.loads(path.read_text(encoding='utf-8'))
    body = archive['data']
    if hashlib.sha256(_canonical(body)).hexdigest() != archive.get('sha256'):
        raise ValueError('백업 무결성 검증 실패')
    name, points = body['collection'], body['points']
    if (body.get('format') != FORMAT or body.get('model') != MODEL or body.get('dimensions') != 384 or
            not isinstance(name, str) or not name.startswith('knowledge_') or not name.replace('_', '').isalnum() or
            not isinstance(points, list)):
        raise ValueError('지원하지 않는 백업 형식')
    for point in points:
        v = point.get('vector')
        if (not isinstance(v, list) or len(v) != 384 or not isinstance(point.get('payload'), dict) or
                any(not isinstance(n, (int, float)) or isinstance(n, bool) or not math.isfinite(n) for n in v)):
            raise ValueError('유효하지 않은 벡터 또는 문단')
    # mkdir without exist_ok makes restoration non-destructive, including for symlinks.
    # 한글: 기존 경로나 심볼릭 링크에는 절대 복원하지 않는다.
    destination.mkdir(mode=0o700, parents=False, exist_ok=False)
    client = QdrantClient(path=str(destination / 'vectors'))
    try:
        client.create_collection(name, vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE))
        for i in range(0, len(points), 100):
            client.upsert(name, points=[models.PointStruct(id=p['id'], vector=p['vector'], payload=p['payload']) for p in points[i:i+100]])
        if client.count(name, exact=True).count != len(points):
            raise RuntimeError('복원된 문단 개수가 일치하지 않습니다')
        active = destination / 'active'
        active.write_text(name, encoding='utf-8'); os.chmod(active, 0o600)
    finally:
        client.close()
    return {'collection': name, 'points': len(points), 'sha256': archive['sha256']}
