#!/usr/bin/env python3
# 한글: 직전 시험 회차(Log/last_trial.json)의 충돌 여부를 확정한다. 운영 규칙(2026-10-11): 사용자가 충돌을 말하지 않으면 없음.
#       run_trial.py는 다음 회차를 시작할 때 이 함수로 이전 회차를 '없음'으로 확정한다. 세션의 마지막 회차는 끝날 때 이 명령으로 확정.
"""Confirm the collision result of the last trial (Log/last_trial.json).

Usage: confirm_last_trial.py            -> no collision (operator convention: an unreported collision means none)
       confirm_last_trial.py y [notes]  -> there was a collision (outcome becomes fail)
run_trial.py calls confirm() for the previous trial when the next trial starts; run this once at the end of a session
for the last trial. An already confirmed trial is left alone.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trial_judge as judge  # noqa: E402

LAST_TRIAL = 'Log/last_trial.json'


def confirm(collision=False, source='convention: no collision reported', notes=None, path_file=LAST_TRIAL):
    """Set collision on the last trial if still unconfirmed. Returns (meta path, meta) or (None, None)."""
    try:
        path = json.load(open(path_file))['meta']
        m = judge.migrate_legacy(json.load(open(path)))
    except (OSError, ValueError, KeyError):
        return None, None
    if m.get('collision') is not None and not collision:
        return path, m
    m = judge.set_collision(m, collision, source)
    if notes:
        m['notes'] = (m.get('notes', '') + ' ' + notes).strip()
    with open(path, 'w') as f:
        json.dump(m, f, indent=1)
    return path, m


def main():
    hit = len(sys.argv) > 1 and sys.argv[1].lower().startswith('y')
    path, m = confirm(hit, 'operator (confirm_last_trial.py)' if hit else
                      'convention: no collision reported by the end of the session',
                      ' '.join(sys.argv[2:]) or None)
    if path is None:
        sys.exit('no last trial recorded (%s)' % LAST_TRIAL)
    print('%s: collision=%s outcome=%s (%s), MVP approach %s'
          % (path, m['collision'], m['outcome'], m['outcome_reason'], m['mvp']['pass']))


if __name__ == '__main__':
    main()
