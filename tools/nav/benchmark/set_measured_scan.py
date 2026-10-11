#!/usr/bin/env python3
# 한글: 시험이 끝나 정지한 로봇의 /scan을 지도에 전수 매칭(scan_match_init.py --dry-run)해 scan_final로 기록한다.
#       로봇은 움직이지 않는다. 스캔 매칭은 AMCL과 같은 LiDAR·지도를 쓰므로 독립 정답이 아니다(출처를 따로 남김).
#       신뢰 기준은 초기화와 같다(trial_judge.scan_trusted). 실패·시간 초과·신뢰 미달이면 이전의 좋은 기록을 덮지 않는다.
"""Scan-match the stopped robot and store it as scan_final in meta.json (see trial_judge.py).

Usage: set_measured_scan.py <tag> <A|B|C> <trial#>      (robot standing still; run_trial.py does this itself)
The match searches around the goal (radius 0.6 m). Trust rule = scan_match_init.py's (score/margin), an untrusted or
failed attempt is recorded in scan_attempt and never replaces an earlier trusted scan_final or a manual (tape) pose.
"""
import json
import subprocess
import sys

import trial_judge as j


def run_scan(goal_x, goal_y, radius=0.6, timeout=120):
    """Run the dry-run matcher; returns a scan result dict (status ok / no_candidates / timeout / error)."""
    try:
        out = subprocess.run(
            ['ros2', 'run', 'jetrover_navigation', 'scan_match_init.py', '--dry-run', '--near', str(goal_x),
             str(goal_y), '--near-radius', str(radius)], capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {'status': 'timeout'}
    except OSError as e:
        return {'status': 'error', 'error': str(e)[:120]}
    return j.scan_result_from_text(out.stdout + out.stderr)


def main():
    tag, sc, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
    path = 'bags/%s/trial_%s%02d/meta.json' % (tag, sc, n)
    m = j.migrate_legacy(json.load(open(path)))
    r = run_scan(m['goal']['x'], m['goal']['y'])
    m = j.apply_scan(m, r)
    json.dump(m, open(path, 'w'), indent=1)
    if r.get('status') == 'ok':
        print(f"{path}: scan match ({r['x']:.3f}, {r['y']:.3f}, {r['yaw_deg']:.1f} deg) score {r['score']:.3f} "
              f"margin {r['margin']:.3f} {'trusted' if r['trusted'] else 'NOT trusted'} -> {m['outcome']} "
              f"({m['outcome_reason']})")
    else:
        print(f"{path}: scan match {r.get('status')} -> {m['outcome']} ({m['outcome_reason']})")


if __name__ == '__main__':
    main()
