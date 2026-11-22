"""Bounded operator-only recorded-video review without robot control.

운영자 전용 녹화 영상 검토. 로봇 제어와 영구 저장은 수행하지 않는다.
"""
import asyncio
import base64
import json
from pathlib import Path
import re
import tempfile
import threading

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()
MAX_VIDEO_BYTES = 8 * 1024 * 1024
MAX_IMAGE_BYTES = 5 * 1024 * 1024
REVIEW_LOCK = threading.Lock()
SCRIPT = Path(__file__).resolve().parents[2] / 'mission/inspect_stack_light_video.py'


def valid_region(value):
    """Validate a bounded pixel region before spawning the decoder.

    디코더 실행 전에 픽셀 영역과 정수 범위를 검증한다.
    """
    if not isinstance(value, str) or not re.fullmatch(r'\d{1,4},\d{1,4},\d{1,4},\d{1,4}', value):
        return False
    x, y, width, height = (int(part) for part in value.split(','))
    return x <= 1280 and y <= 720 and 4 <= width <= 1280 and 4 <= height <= 720


@router.post('/api/inspection/video-review')
async def video_review(request: Request, red: str, yellow: str, green: str):
    """Review a bounded uploaded video in an isolated short-lived subprocess.

    제한된 업로드 영상을 수명이 짧은 별도 프로세스에서 검토한다.
    """
    if not all(valid_region(value) for value in (red, yellow, green)):
        raise HTTPException(400, 'invalid_regions')
    if request.headers.get('content-type', '').split(';', 1)[0].strip().lower() != 'application/octet-stream':
        raise HTTPException(415, 'invalid_content_type')
    try:
        declared = int(request.headers.get('content-length', '0'))
    except ValueError:
        raise HTTPException(400, 'invalid_content_length') from None
    if declared < 0 or declared > MAX_VIDEO_BYTES:
        raise HTTPException(413, 'video_too_large')
    if not REVIEW_LOCK.acquire(blocking=False):
        raise HTTPException(409, 'review_busy')
    try:
        with tempfile.TemporaryDirectory(prefix='jetinspect-video-review-', dir='/tmp') as folder:
            path = Path(folder) / 'input.video'
            size = 0
            with path.open('xb') as output:
                async with asyncio.timeout(20):
                    async for chunk in request.stream():
                        size += len(chunk)
                        if size > MAX_VIDEO_BYTES:
                            raise HTTPException(413, 'video_too_large')
                        output.write(chunk)
            if size == 0:
                raise HTTPException(400, 'empty_video')
            process = await asyncio.create_subprocess_exec(
                '/usr/bin/python3', str(SCRIPT), str(path), '--red', red, '--yellow', yellow,
                '--green', green, '--evidence-dir', folder,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
            try:
                stdout, _ = await asyncio.wait_for(process.communicate(), timeout=30)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                if process.returncode is None:
                    process.kill()
                await process.communicate()
                raise
            if process.returncode != 0 or len(stdout) > 65536:
                raise HTTPException(400, 'video_review_failed')
            try:
                result = json.loads(stdout)
                paths = result.pop('evidence_images', [])
                images = []
                for filename in paths:
                    image = Path(filename)
                    if image.is_symlink() or not image.resolve().is_relative_to(Path(folder).resolve()):
                        raise ValueError('invalid image path')
                    if image.stat().st_size > MAX_IMAGE_BYTES:
                        raise ValueError('image too large')
                    images.append(base64.b64encode(image.read_bytes()).decode('ascii'))
                result['evidence_images'] = images
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                raise HTTPException(500, 'invalid_review_result') from None
            return result
    except asyncio.TimeoutError:
        raise HTTPException(504, 'video_review_timeout') from None
    finally:
        REVIEW_LOCK.release()
