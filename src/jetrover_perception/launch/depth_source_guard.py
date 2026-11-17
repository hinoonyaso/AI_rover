"""Validate corrected-depth background provenance before activating a safety input.

한글: 안전 입력 활성화 전 보정 깊이 기준 영상의 출처를 확인한다.
"""
import hashlib
import json
from pathlib import Path


def validate_corrected_background(background, calibration):
    """Require metadata to bind the background bytes to the active calibration.

    한글: 기준 영상과 활성 보정 파일의 해시가 메타데이터와 일치해야 한다.
    """
    image,active=Path(background),Path(calibration)
    metadata=image.with_suffix(image.suffix+'.json')
    for item in (image,active,metadata):
        if item.is_symlink() or not item.is_file():raise ValueError('corrected background, metadata or calibration missing')
    if image.stat().st_size>10_000_000 or active.stat().st_size>65536 or metadata.stat().st_size>65536:raise ValueError('corrected background input too large')
    value=json.loads(metadata.read_text())
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    if value.get('background_sha256')!=digest(image) or value.get('calibration_sha256')!=digest(active) or value.get('source_topic')!='/depth_cam/depth_corrected/image_raw':
        raise ValueError('corrected background does not match active calibration')
    return str(image)
