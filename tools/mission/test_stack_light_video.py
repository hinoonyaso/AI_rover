"""Exercise recorded-video sampling and unknown-on-insufficient evidence.

녹화 영상 표본화 및 근거가 부족할 때 판정 유보를 검증한다.
"""
import cv2
import numpy as np
import pytest

from inspect_stack_light_video import inspect_video

REGIONS = {'red': (0, 0, 16, 16), 'yellow': (16, 0, 16, 16), 'green': (32, 0, 16, 16)}


def make_video(path, seconds):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'MJPG'), 10, (48, 16))
    assert writer.isOpened()
    for _ in range(seconds * 10):
        hsv = np.zeros((16, 48, 3), dtype=np.uint8)
        for i, (hue, value) in enumerate(((0, 220), (27, 40), (60, 220))):
            hsv[:, i * 16:(i + 1) * 16] = (hue, 255, value)
        writer.write(cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR))
    writer.release()


def test_video_samples_are_classified_without_robot(tmp_path):
    video = tmp_path / 'lights.avi'
    make_video(video, 4)
    result = inspect_video(video, REGIONS)
    assert result['source'] == 'recorded_video'
    assert not result['real_world_validated']
    assert result['frames_sampled'] >= 5
    assert [result['states'][name]['state'] for name in REGIONS] == ['on', 'off', 'on']


def test_short_video_is_unknown(tmp_path):
    video = tmp_path / 'short.avi'
    make_video(video, 1)
    result = inspect_video(video, REGIONS)
    assert all(item['state'] == 'unknown' for item in result['states'].values())


def test_missing_file_and_invalid_interval(tmp_path):
    with pytest.raises(ValueError, match='열 수 없습니다'):
        inspect_video(tmp_path / 'missing.avi', REGIONS)
    with pytest.raises(ValueError, match='간격'):
        inspect_video(tmp_path / 'missing.avi', REGIONS, interval=0.8)


def test_excessive_sample_budget_is_rejected(tmp_path):
    with pytest.raises(ValueError, match='최대 40개'):
        inspect_video(tmp_path / 'missing.avi', REGIONS, duration=18, interval=0.3)


def test_evaluation_keeps_real_and_synthetic_separate(tmp_path):
    import json
    from evaluate_stack_light_videos import evaluate

    video = tmp_path / 'lights.avi'
    make_video(video, 4)
    cases = []
    for source in ('synthetic', 'real'):
        cases.append({'id': source, 'source': source, 'video': video.name,
                      'regions': {name: list(value) for name, value in REGIONS.items()},
                      'expected': {'red': 'on', 'yellow': 'off', 'green': 'on'}})
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'cases': cases}))
    result = evaluate(manifest)
    assert result['summary_by_source']['synthetic']['matches'] == 3
    assert result['summary_by_source']['real']['labels'] == 3
    assert len(result['cases']) == 2


def test_evaluation_reports_unreadable_case(tmp_path):
    import json
    from evaluate_stack_light_videos import evaluate

    case = {'id': 'missing', 'source': 'gazebo', 'video': 'missing.avi',
            'regions': {name: list(value) for name, value in REGIONS.items()},
            'expected': {'red': 'on', 'yellow': 'off', 'green': 'on'}}
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'cases': [case]}))
    result = evaluate(manifest)
    assert result['summary_by_source']['gazebo']['errors'] == 1
    assert result['summary_by_source']['gazebo']['labels'] == 0


def test_evidence_images_are_optional_and_do_not_overwrite(tmp_path):
    video = tmp_path / 'lights.avi'
    make_video(video, 4)
    existing = tmp_path / 'first.png'
    existing.write_bytes(b'preserve')
    result = inspect_video(video, REGIONS, evidence_dir=tmp_path)
    images = result['evidence_images']
    assert len(images) == 2
    assert all(cv2.imread(path) is not None for path in images)
    assert existing.read_bytes() == b'preserve'
    assert 'evidence_images' not in inspect_video(video, REGIONS)
