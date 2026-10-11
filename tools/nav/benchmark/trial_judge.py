#!/usr/bin/env python3
# 한글: Nav2 시험 1회의 판정 규칙(순수 함수, 단위시험 test_trial_judge.py). meta.json에는 자세를 출처별로 따로 둔다:
#   auto.amcl_final = Nav2/AMCL 추정(TF), scan_final = 정지 후 LiDAR 스캔-지도 매칭 추정, manual_final = 줄자 등 사람 측정.
#   판정은 manual_final > 신뢰 기준을 넘은 scan_final 순으로 쓰고, 둘 다 없으면 'unmeasured'(판정 보류).
#   스캔 매칭은 AMCL과 같은 LiDAR·지도를 쓰므로 독립 정답이 아니다(지도 오차를 공유) — 출처를 반드시 남긴다.
"""Pass/fail rules for one Nav2 benchmark trial (pure, unit-tested in test_trial_judge.py).

Poses are kept per source in meta.json and never overwrite each other:
  auto.amcl_final  Nav2/AMCL estimate (TF map->base_footprint)
  scan_final       scan-to-map match after the robot stopped (same LiDAR + map as AMCL: NOT independent truth)
  manual_final     tape/protractor measurement by a person
The judged pose is manual_final, else a trusted scan_final, else none ('unmeasured').

Outcome, in order of precedence:
  invalid            the last global plan ended > PLAN_CUT_M from the goal (goal area blocked)
  safety_error       the goal cancel was not acknowledged or the robot could not be confirmed stopped (auto.safety_error)
  fail               collision is True
  abort              Nav2 did not report success (aborted / canceled / timeout / interrupted / rejected)
  unmeasured         no manual pose and no trusted scan match (measurement failure, kept apart from Nav2 failure)
  fail               errors outside the test plan limits
  pending_collision  everything passes but the collision check is not confirmed yet (collision is None)
  success
A scan match is only taken once the robot was confirmed standing still (auto.stopped_before_measure); otherwise
scan_final.status is 'not_stopped' and the trial stays 'unmeasured' unless a manual (tape) pose is entered later.

Separately, meta['mvp'] is the MVP approach check (docs/PLAN_ARM_TO_MVP.md: Nav2 gets within +-10 cm, the camera
does the rest): Nav2 succeeded, robot stopped, collision False, judged position error <= MVP_POS_TOL_M and yaw within
YAW_TOL_RAD. pass is None while anything is still unknown (no pose, collision unconfirmed, stop unknown).
"""
import math
import re

POS_TOL_M = 0.15            # prd/nav2-baseline-test-plan.md pass limits
YAW_TOL_RAD = 0.4
LINE_TOL_M = 0.10           # scenario B: back on the x = START_X line
TIME_LIMIT_S = 60.0
START_X = 1.05
PLAN_CUT_M = 0.10           # run_trial.py: plan end farther than this from the goal -> invalid
MVP_POS_TOL_M = 0.10        # MVP approach: Nav2 within +-10 cm, camera re-detection does the rest (2026-10-11)

# Same confidence rule as jetrover_navigation/scripts/scan_match_init.py (--min-score 0.80 --min-margin 0.10,
# --strong-score 0.95 --strong-margin 0.05). Keep both in sync. 한글: 초기화와 같은 신뢰 기준.
MIN_SCORE, MIN_MARGIN = 0.80, 0.10
STRONG_SCORE, STRONG_MARGIN = 0.95, 0.05

NAV_OK = 'succeeded'
CAND_RE = re.compile(r'#(\d+) score=([\d.]+)\s+x=([+-][\d.]+) y=([+-][\d.]+) yaw=([+-][\d.]+)deg')


def scan_trusted(score, margin):
    return (score >= MIN_SCORE and margin >= MIN_MARGIN) or (score >= STRONG_SCORE and margin >= STRONG_MARGIN)


def parse_candidates(text):
    """scan_match_init.py --dry-run log -> [(score, x, y, yaw_deg)] in rank order."""
    out = []
    for line in text.splitlines():
        r = CAND_RE.search(line)
        if r:
            out.append((int(r.group(1)),) + tuple(float(r.group(i)) for i in range(2, 6)))
    out.sort()
    return [c[1:] for c in out]


def scan_result_from_text(text):
    """Turn a dry-run log into a scan result dict (status ok / no_candidates)."""
    cands = parse_candidates(text)
    if not cands:
        return {'status': 'no_candidates'}
    score, x, y, yaw = cands[0]
    margin = score - (cands[1][0] if len(cands) > 1 else 0.0)
    return {'status': 'ok', 'x': round(x, 4), 'y': round(y, 4), 'yaw_deg': round(yaw, 2),
            'score': round(score, 3), 'margin': round(margin, 3), 'trusted': scan_trusted(score, margin)}


def wrap_deg(d):
    return (d + 180.0) % 360.0 - 180.0


def errors(pose, goal):
    pos = math.hypot(pose['x'] - goal['x'], pose['y'] - goal['y'])
    yaw = abs(wrap_deg(pose['yaw_deg'] - goal['yaw_deg']))
    return {'pos_m': round(pos, 4), 'yaw_deg': round(yaw, 2)}


def judged_pose(meta):
    """(pose, source) used for pass/fail, or (None, None)."""
    if meta.get('manual_final'):
        return meta['manual_final'], 'manual'
    s = meta.get('scan_final')
    if s and s.get('status') == 'ok' and s.get('trusted'):
        return s, 'scan_match'
    return None, None


def judge(meta):
    """Return (outcome, reason). Does not modify meta."""
    auto = meta.get('auto', {})
    if auto.get('invalid_plan_cut_short'):
        return 'invalid', 'plan ended %.2f m from the goal' % (auto.get('last_plan_end_to_goal_m') or 0.0)
    if auto.get('safety_error'):
        return 'safety_error', auto['safety_error']
    if meta.get('collision') is True:
        return 'fail', 'collision'
    status = auto.get('action_status')
    if status != NAV_OK:
        return 'abort', 'nav2 %s' % status
    pose, src = judged_pose(meta)
    if pose is None:
        s = meta.get('scan_final') or meta.get('scan_attempt') or {}
        if s.get('status') == 'ok':
            why = 'scan match below the trust rule (score %.3f, margin %.3f)' % (s['score'], s['margin'])
        else:
            why = 'scan match %s' % (s.get('status') or 'not run')
        return 'unmeasured', 'no manual pose; ' + why
    e = errors(pose, meta['goal'])
    why = []
    if auto.get('elapsed_s', 0.0) > TIME_LIMIT_S:
        why.append('time %.1f s' % auto['elapsed_s'])
    if e['pos_m'] > POS_TOL_M:
        why.append('pos %.1f cm' % (e['pos_m'] * 100))
    if math.radians(e['yaw_deg']) > YAW_TOL_RAD:
        why.append('yaw %.1f deg' % e['yaw_deg'])
    if meta.get('scenario') == 'B' and abs(pose['x'] - START_X) > LINE_TOL_M:
        why.append('line %.1f cm' % (abs(pose['x'] - START_X) * 100))
    if why:
        return 'fail', '%s: %s' % (src, ', '.join(why))
    if meta.get('collision') is None:
        return 'pending_collision', '%s: within limits, collision not confirmed' % src
    return 'success', src


ODOM_MAX_AGE_S = 0.5        # an /odom message older than this is not evidence that the robot stands still
STOP_V_MPS, STOP_W_RPS = 0.01, 0.02


def stop_state(odom_samples, now, hold=1.0, max_age=ODOM_MAX_AGE_S):
    """Pure stop check from [(t_monotonic, speed m/s, |wz| rad/s)] samples (newest last).
    Returns (stopped, reason): True only if the newest sample is fresh AND every sample of the last `hold` s
    (with at least one older than hold/2 so a single reading is not enough) is below the stop limits.
    A silent /odom (no new message for max_age s) is 'odom_stale', never 'stopped'.
    """
    if not odom_samples:
        return False, 'no_odom'
    if now - odom_samples[-1][0] > max_age:
        return False, 'odom_stale'
    window = [s for s in odom_samples if now - s[0] <= hold]
    if not window or now - window[0][0] < hold * 0.5:
        return False, 'window_too_short'
    if any(s[1] >= STOP_V_MPS or s[2] >= STOP_W_RPS for s in window):
        return False, 'moving'
    return True, 'stopped'


def mvp_check(meta):
    """MVP approach check, separate from the test-plan outcome. pass None = not decidable yet."""
    auto = meta.get('auto', {})
    err = meta.get('measured_err')
    checks = {
        'nav2_succeeded': auto.get('action_status') == NAV_OK and not auto.get('invalid_plan_cut_short'),
        'stopped': (None if auto.get('stopped_before_measure') is None
                    else bool(auto['stopped_before_measure']) and not auto.get('safety_error')),
        'no_collision': None if meta.get('collision') is None else not meta['collision'],
        'pos_within_10cm': None if err is None else err['pos_m'] <= MVP_POS_TOL_M,
        'yaw_within_tol': None if err is None else math.radians(err['yaw_deg']) <= YAW_TOL_RAD,
    }
    if any(v is False for v in checks.values()):
        ok = False
    elif any(v is None for v in checks.values()):
        ok = None
    else:
        ok = True
    return dict(checks, **{'pass': ok, 'pos_tol_m': MVP_POS_TOL_M})


def rejudge(meta):
    """Recompute outcome and the derived measured_final/measured_err (kept for analyze.py)."""
    pose, src = judged_pose(meta)
    if pose is not None:
        meta['measured_final'] = {'x': pose['x'], 'y': pose['y'], 'yaw_deg': pose['yaw_deg'], 'source': src}
        meta['measured_err'] = errors(pose, meta['goal'])
    else:
        meta['measured_final'] = None
        meta['measured_err'] = None
    meta['outcome'], meta['outcome_reason'] = judge(meta)
    meta['mvp'] = mvp_check(meta)
    return meta


def apply_scan(meta, result):
    """Store a scan-match attempt. A failed/untrusted attempt never replaces an earlier good scan_final."""
    meta['scan_attempt'] = {k: result.get(k) for k in ('status', 'score', 'margin', 'trusted')}
    prev = meta.get('scan_final')
    good_prev = prev and prev.get('status') == 'ok' and prev.get('trusted')
    if result.get('status') == 'ok' and (result.get('trusted') or not good_prev):
        meta['scan_final'] = result
    elif not prev:
        meta['scan_final'] = result
    return rejudge(meta)


def apply_manual(meta, pose, overwrite=False):
    """Store a manual (tape) pose; refuses to replace an existing one unless overwrite."""
    if meta.get('manual_final') and not overwrite:
        raise ValueError('manual_final already set (use overwrite)')
    meta['manual_final'] = pose
    return rejudge(meta)


def set_collision(meta, collision, source):
    meta['collision'] = collision
    meta['collision_source'] = source
    return rejudge(meta)


def migrate_legacy(meta):
    """Pre-2026-10-11 meta: measured_final (tape or scan) / scan_measured_final -> manual_final / scan_final."""
    if 'manual_final' in meta or 'scan_final' in meta:
        return meta
    old = meta.get('measured_final')
    extra = meta.get('scan_measured_final')
    if old:
        if old.get('source') == 'scan_match':
            meta['scan_final'] = {'status': 'ok', 'x': old['x'], 'y': old['y'], 'yaw_deg': old['yaw_deg'],
                                  'score': old['score'], 'margin': old['margin'],
                                  'trusted': scan_trusted(old['score'], old['margin'])}
        else:
            meta['manual_final'] = {k: old[k] for k in ('x', 'y', 'yaw_deg', 'tape') if k in old}
    if extra and 'scan_final' not in meta:
        meta['scan_final'] = {'status': 'ok', 'x': extra['x'], 'y': extra['y'], 'yaw_deg': extra['yaw_deg'],
                              'score': extra['score'], 'margin': extra['margin'],
                              'trusted': scan_trusted(extra['score'], extra['margin'])}
    tape = meta.get('tape_measured_final')
    if tape and 'manual_final' not in meta:
        meta['tape_measured_final_superseded'] = tape  # B02 E6 v2: tape replaced by scan at the time, kept aside
    meta.pop('scan_measured_final', None)
    meta.pop('scan_measured_err', None)
    meta['outcome_legacy'] = meta.get('outcome')
    return rejudge(meta)
