#!/usr/bin/env python3
"""Evaluate labeled video cases separately by source.

정답이 표시된 영상 사례를 출처별로 분리해 평가한다.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path

from inspect_stack_light_video import inspect_video

COLORS = ('red', 'yellow', 'green')
STATES = {'on', 'off', 'blinking', 'unknown'}
SOURCES = {'synthetic', 'gazebo', 'real'}


def evaluate(manifest_path):
    """Compare predictions with labels without combining real and synthetic data.

    실제 영상과 합성 영상을 합산하지 않고 예측을 정답과 비교한다.
    """
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if not isinstance(manifest, dict) or not isinstance(manifest.get('cases'), list):
        raise ValueError('cases 배열이 필요합니다')
    cases = manifest['cases']
    if not 0 < len(cases) <= 1000:
        raise ValueError('사례는 1~1000개여야 합니다')
    summary = defaultdict(lambda: {'cases': 0, 'labels': 0, 'matches': 0,
                                   'unknown_predictions': 0, 'errors': 0})
    results = []
    identifiers = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError('각 사례는 객체여야 합니다')
        ident, source, path = case.get('id'), case.get('source'), case.get('video')
        expected, regions = case.get('expected'), case.get('regions')
        if (not isinstance(ident, str) or not ident or ident in identifiers or
                source not in SOURCES or not isinstance(path, str) or not path or
                not isinstance(expected, dict) or set(expected) != set(COLORS) or
                any(not isinstance(v, str) or v not in STATES for v in expected.values()) or
                not isinstance(regions, dict) or set(regions) != set(COLORS)):
            raise ValueError('사례의 id, source, video, expected 또는 regions가 올바르지 않습니다')
        identifiers.add(ident)
        # Convert JSON arrays only after validating every coordinate and size.
        # 한글: 모든 좌표와 크기를 검증한 뒤 JSON 배열을 튜플로 변환한다.
        parsed = {}
        for name in COLORS:
            value = regions[name]
            if (not isinstance(value, list) or len(value) != 4 or
                    any(type(v) is not int for v in value) or
                    min(value[:2]) < 0 or min(value[2:]) < 4):
                raise ValueError('regions는 색상별 픽셀 좌표 4개여야 합니다')
            parsed[name] = tuple(value)
        group = summary[source]
        group['cases'] += 1
        try:
            observation = inspect_video(manifest_path.parent / path, parsed)
        except ValueError as exc:
            group['errors'] += 1
            results.append({'id': ident, 'source': source, 'error': str(exc)})
            continue
        predicted = {name: observation['states'][name]['state'] for name in COLORS}
        group['labels'] += len(COLORS)
        group['matches'] += sum(predicted[name] == expected[name] for name in COLORS)
        group['unknown_predictions'] += sum(predicted[name] == 'unknown' for name in COLORS)
        results.append({'id': ident, 'source': source, 'expected': expected,
                        'predicted': predicted, 'observation': observation})
    return {'summary_by_source': dict(summary), 'cases': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(args.manifest)
    except (OSError, ValueError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
