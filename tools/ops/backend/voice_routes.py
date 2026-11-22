"""Bounded local speech recognition for authenticated dashboard users.

한글: 인증된 대시보드용 제한된 로컬 음성 인식을 제공한다.
"""
import asyncio
import io
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import wave

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from voice_intent import interpret

router = APIRouter(prefix='/api/voice')
LOCK = threading.Lock()
VOICE = Path(__file__).resolve().parents[2] / 'voice' / 'voice.py'
PYTHON = Path.home() / '.local/share/jetrover-voice/venv/bin/python'
MAX_BYTES = 320_128


class Transcript(BaseModel):
    """Bound text used for local interpretation. / 로컬 해석에 쓰는 제한된 전사 텍스트."""
    text: str = Field(max_length=300)


@router.post('/interpret')
def interpret_text(payload: Transcript):
    """Interpret text without executing actions. / 동작 없이 텍스트만 해석한다."""
    return {'transcript': payload.text, **interpret(payload.text)}


def _run_stt(raw):
    # The worker owns the lock and temporary WAV even if the client disconnects.
    # 한글: 클라이언트 연결이 끊겨도 워커가 잠금과 임시 WAV를 종료까지 소유한다.
    try:
        with tempfile.TemporaryDirectory(prefix='jetinspect-stt-') as directory:
            path = Path(directory) / 'voice.wav'
            path.write_bytes(raw)
            env = os.environ.copy(); env.pop('PYTHONPATH', None)
            return subprocess.run([str(PYTHON), str(VOICE), 'stt', str(path)], env=env,
                                  capture_output=True, text=True, timeout=120, check=True)
    finally:
        LOCK.release()


@router.post('/transcribe')
async def transcribe(request: Request):
    """Transcribe one bounded WAV in a private temporary directory.

    한글: 제한된 WAV 한 개를 개인 임시 디렉터리에서 전사한다.
    """
    if not LOCK.acquire(blocking=False):
        return JSONResponse({'error': '다른 음성을 인식 중입니다.'}, status_code=409)
    scheduled = False
    try:
        parts, size = [], 0
        async for part in request.stream():
            size += len(part)
            if size > MAX_BYTES:
                return JSONResponse({'error': '음성 길이 제한을 초과했습니다.'}, status_code=413)
            parts.append(part)
        raw = b''.join(parts)
        try:
            with wave.open(io.BytesIO(raw), 'rb') as wav:
                if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getcomptype()) != (1, 2, 16000, 'NONE'):
                    raise ValueError()
                count = wav.getnframes()
                if not 4800 <= count <= 160000 or len(wav.readframes(count)) != count * 2:
                    raise ValueError()
        except (ValueError, EOFError, wave.Error):
            return JSONResponse({'error': '16kHz 모노 PCM WAV 형식과 음성 길이를 확인하세요.'}, status_code=400)
        try:
            task = asyncio.create_task(asyncio.to_thread(_run_stt, raw))
            scheduled = True
            task.add_done_callback(lambda done: None if done.cancelled() else done.exception())
            # Shield the independently-owned worker from client cancellation.
            # 한글: 클라이언트 취소가 독립 워커에 전파되지 않게 한다.
            result = await asyncio.shield(task)
        except (OSError, subprocess.SubprocessError):
            return JSONResponse({'error': '로컬 음성 인식에 실패했습니다. 모델과 장치 상태를 확인하세요.'}, status_code=503)
        text = result.stdout.strip()
        if len(text) > 300:
            return JSONResponse({'error': '인식된 문장이 너무 깁니다.'}, status_code=400)
        return {'transcript': text, **interpret(text)}
    finally:
        if not scheduled:
            LOCK.release()
