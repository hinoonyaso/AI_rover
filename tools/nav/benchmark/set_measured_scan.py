#!/usr/bin/env python3
# 한글: 줄자·눈대중 각도 대신, 시험이 끝난 로봇의 /scan을 지도에 전수 매칭(scan_match_init.py --dry-run)해 최종 자세(x, y, yaw)를
#       구해 meta.json의 measured_final로 기록한다. 로봇이 정지해 있어야 하고 움직이지 않는다. 오도메트리·AMCL과 독립이다.
"""Store the scan-matched final pose in meta.json as measured_final (source 'scan_match').

Usage: set_measured_scan.py <tag> <A|B|C> <trial#>      (run right after the trial, robot standing still)
The match is a brute-force scan-to-map search around the goal (radius 0.6 m); it is rejected when the best score
is below 0.8 or the margin to a second place is under 0.05, so a wrong match can't slip in silently.
Pass/fail uses the same rules as set_measured.py (<= 0.15 m, <= 0.4 rad, B: |x - 1.05| <= 0.10, no collision).
"""
import json
import math
import re
import subprocess
import sys

START_X = 1.05

tag, sc, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
path = 'bags/%s/trial_%s%02d/meta.json' % (tag, sc, n)
m = json.load(open(path))
g = m['goal']
out = subprocess.run(
    ['ros2', 'run', 'jetrover_navigation', 'scan_match_init.py', '--dry-run', '--near', str(g['x']), str(g['y']),
     '--near-radius', '0.6'], capture_output=True, text=True, timeout=120)
cands = []
for line in (out.stdout + out.stderr).splitlines():
    r = re.search(r'#(\d+) score=([\d.]+)\s+x=([+-][\d.]+) y=([+-][\d.]+) yaw=([+-][\d.]+)deg', line)
    if r:
        cands.append(tuple(float(r.group(i)) for i in range(2, 6)))
if not cands:
    sys.exit('no scan-match candidates: ' + (out.stderr.strip().splitlines() or ['?'])[-1])
score, x, y, yaw = cands[0]
margin = score - (cands[1][0] if len(cands) > 1 else 0.0)
if score < 0.8 or margin < 0.05:
    sys.exit(f'scan match not trusted (score {score:.3f}, margin {margin:.3f}); measure by tape instead')
m['measured_final'] = {'x': round(x, 4), 'y': round(y, 4), 'yaw_deg': round(yaw, 2), 'source': 'scan_match',
                       'score': score, 'margin': round(margin, 3)}
err = math.hypot(x - g['x'], y - g['y'])
yaw_err = abs((yaw - g['yaw_deg'] + 180) % 360 - 180)
m['measured_err'] = {'pos_m': round(err, 4), 'yaw_deg': round(yaw_err, 2)}
auto = m.get('auto', {})
ok = auto.get('action_status') == 'succeeded' and auto.get('elapsed_s', 99) <= 60
ok = ok and err <= 0.15 and math.radians(yaw_err) <= 0.4 and not m.get('collision')
if sc == 'B':
    ok = ok and abs(x - START_X) <= 0.10
if m.get('outcome') != 'invalid':
    m['outcome'] = 'success' if ok else 'fail'
json.dump(m, open(path, 'w'), indent=1)
print(f'{path}: scan-matched final ({x:.3f}, {y:.3f}, {yaw:.1f} deg) score {score:.3f} margin {margin:.3f}; '
      f'error {err * 100:.1f} cm / {yaw_err:.1f} deg -> {m["outcome"]}')
