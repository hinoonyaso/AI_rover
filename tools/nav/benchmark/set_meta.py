#!/usr/bin/env python3
# 한글: 시험 1회의 사람 판정(충돌 여부, 메모)을 meta.json에 기록하고 판정을 다시 계산한다(trial_judge.py).
#       충돌 미확인(None)은 성공으로 치지 않는다(pending_collision). 운영 규칙: 다음 회차를 시작하면 이전 회차는 충돌 없음으로 확정.
"""Usage: set_meta.py <tag> <A|B|C> <trial#> <collision y|n> [notes...]"""
import json
import sys

import trial_judge as j

tag, sc, n, col = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4].lower().startswith('y')
path = 'bags/%s/trial_%s%02d/meta.json' % (tag, sc, n)
m = j.migrate_legacy(json.load(open(path)))
m = j.set_collision(m, col, 'operator (set_meta.py)')
if len(sys.argv) > 5:
    m['notes'] = ' '.join(sys.argv[5:])
json.dump(m, open(path, 'w'), indent=1)
print(path, 'collision=%s outcome=%s (%s)' % (m['collision'], m['outcome'], m['outcome_reason']))
