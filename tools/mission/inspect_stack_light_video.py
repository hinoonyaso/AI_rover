#!/usr/bin/env python3
"""Classify explicit regions in a recorded video without running ROS.

녹화 영상의 지정 영역을 ROS나 로봇 구동 없이 판정한다. 실제 설비용 임계값은 미검증이다.
"""
import argparse
import json
import math
from pathlib import Path
import sys
import tempfile

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src/jetrover_perception/scripts'))
from stack_light import classify  # noqa: E402


def region(value):
    """Parse x,y,width,height in pixels. / 픽셀 단위 x,y,너비,높이를 읽는다."""
    try:
        values = tuple(int(part) for part in value.split(','))
    except ValueError as exc:
        raise argparse.ArgumentTypeError('영역은 x,y,너비,높이 정수 네 개여야 합니다') from exc
    if len(values) != 4 or min(values[:2]) < 0 or min(values[2:]) < 4:
        raise argparse.ArgumentTypeError('영역의 시작 좌표는 0 이상, 너비와 높이는 4 이상이어야 합니다')
    return values


def inspect_video(path, regions, start=0.0, duration=3.0, interval=0.5, evidence_dir=None):
    """Sample a bounded video window and return states with evidence metadata.

    제한된 영상 구간을 표본화해 색상별 상태와 근거 정보를 반환한다.
    """
    if not all(math.isfinite(v) for v in (start, duration, interval)):
        raise ValueError('시간은 유한한 숫자여야 합니다')
    if start < 0 or not 0 < duration <= 18 or not 0.3 <= interval <= 0.6:
        raise ValueError('시작은 0 이상, 길이는 최대 18초, 간격은 0.3~0.6초여야 합니다')
    if duration / interval > 39:
        raise ValueError('표본은 최대 40개까지 허용됩니다')
    cap = cv2.VideoCapture(str(path))
    try:
        if not cap.isOpened():
            raise ValueError('동영상 파일을 열 수 없습니다')
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        if not math.isfinite(fps) or not 0 < fps <= 120:
            raise ValueError('동영상 프레임 속도를 확인할 수 없습니다')
        width, height = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        if (not all(math.isfinite(v) for v in (width, height)) or
                not 0 < width <= 1280 or not 0 < height <= 720):
            raise ValueError('동영상 크기는 최대 1280×720이어야 합니다')
        # Use frame timestamps, not wall time, to detect gaps and blinking in recorded video.
        # 한글: 실제 대기 시간이 아닌 동영상 시각으로 표본 간격과 깜빡임을 판정한다.
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(start * fps))
        index = int(start * fps)
        next_sample = start
        frames = []
        while index / fps <= start + duration:
            ok, bgr = cap.read()
            if not ok:
                break
            timestamp = index / fps
            if timestamp + 1e-9 >= next_sample:
                frames.append((timestamp, cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)))
                next_sample += interval
            index += 1
        states = classify(frames, regions, frames[-1][0] if frames else 0.0)
        result = {'source': 'recorded_video', 'real_world_validated': False,
                  'frames_sampled': len(frames),
                  'observed_duration_s': round(frames[-1][0] - frames[0][0], 3) if len(frames) > 1 else 0.0,
                  'states': states}
        if evidence_dir is not None and frames:
            parent = Path(evidence_dir)
            if not parent.is_dir():
                raise ValueError('근거 이미지 저장 폴더가 없습니다')
            # A new directory avoids overwriting existing user photographs.
            # 한글: 새 폴더에만 저장하여 기존 사용자 이미지를 덮어쓰지 않는다.
            output = Path(tempfile.mkdtemp(prefix='stack-light-', dir=parent))
            files = []
            for label, (_, rgb) in (('first', frames[0]), ('last', frames[-1])):
                image = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
                for name, color in (('red', (0, 0, 255)), ('yellow', (0, 255, 255)), ('green', (0, 255, 0))):
                    x, y, width, height = regions[name]
                    cv2.rectangle(image, (x, y), (x + width - 1, y + height - 1), color, 1)
                target = output / (label + '.png')
                if not cv2.imwrite(str(target), image):
                    raise ValueError('근거 이미지를 저장하지 못했습니다')
                files.append(str(target))
            result['evidence_images'] = files
        return result
    finally:
        cap.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video', type=Path)
    for name in ('red', 'yellow', 'green'):
        parser.add_argument('--' + name, required=True, type=region, metavar='X,Y,W,H')
    parser.add_argument('--start', type=float, default=0.0)
    parser.add_argument('--duration', type=float, default=3.0)
    parser.add_argument('--interval', type=float, default=0.5)
    parser.add_argument('--evidence-dir', type=Path, help='첫/마지막 표본을 새 하위 폴더에 저장')
    args = parser.parse_args()
    try:
        result = inspect_video(args.video, {n: getattr(args, n) for n in ('red', 'yellow', 'green')},
                               args.start, args.duration, args.interval, args.evidence_dir)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
