#!/usr/bin/env python3
# 한글: 시험 1회의 사람 판정(충돌 여부, 메모, 줄자 실측)을 meta.json에 기록한다. 충돌이 있으면 outcome을 fail로 내린다.
"""Usage: set_meta.py <tag> <A|B|C> <trial#> <collision y|n> [notes...]"""
import json
import sys

tag, sc, n, col = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4].lower().startswith('y')
path = 'bags/%s/trial_%s%02d/meta.json' % (tag, sc, n)
m = json.load(open(path))
m['collision'] = col
if col:
    m['outcome'] = 'fail'
m['notes'] = ' '.join(sys.argv[5:])
json.dump(m, open(path, 'w'), indent=1)
print(path, 'collision=%s outcome=%s' % (m['collision'], m['outcome']))
