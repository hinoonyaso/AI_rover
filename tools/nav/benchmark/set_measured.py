#!/usr/bin/env python3
# 한글: 줄자 실측(출발 표시 대비 앞/좌 이동 거리, 방향 변화)을 meta.json의 manual_final(지도 좌표)로 기록한다.
#       판정은 manual_final을 스캔 매칭보다 우선한다(trial_judge.py). 스캔 매칭 기록은 지우지 않고 따로 남는다.
"""Store the tape-measured final pose in meta.json as manual_final (judged before a scan match, see trial_judge.py).

Usage: set_measured.py <tag> <A|B|C> <trial#> <forward_m> <left_m> [<turn_deg, + = CCW>] [--overwrite]
Stored as manual_final (never overwritten by a scan match; a second tape entry needs --overwrite).
Measured from the start mark with the same reference point on the robot, in the START body frame
(forward = the start heading). The start pose is the nominal START of run_trial.py (the robot is placed
on the start mark and AMCL is set there). 2026-10-10 E6: the auto goal error is the robot's own belief
and sits at the goal checker tolerance (0.15 m) in every condition, so only the tape tells odometry apart.
"""
import json
import math
import sys

import trial_judge as j

START = (1.05, 0.10, 90.0)  # nominal start of run_trial.py

args = [a for a in sys.argv[1:] if a != '--overwrite']
overwrite = '--overwrite' in sys.argv
tag, sc, n = args[0], args[1], int(args[2])
fwd, left = float(args[3]), float(args[4])
turn = float(args[5]) if len(args) > 5 else 0.0
path = 'bags/%s/trial_%s%02d/meta.json' % (tag, sc, n)
m = j.migrate_legacy(json.load(open(path)))
# The tape is measured from where the robot really started: the scan-matched start (E6 v2) when recorded,
# else the nominal START (v1 runs forced AMCL there). 한글: 실제 출발 위치(스캔 매칭) 기준으로 환산.
start = m.get('auto', {}).get('amcl_start') if m.get('auto', {}).get('start_from') == 'scan_match' else None
sx, sy, syaw = start if start else START
h = math.radians(syaw)
x = sx + fwd * math.cos(h) - left * math.sin(h)
y = sy + fwd * math.sin(h) + left * math.cos(h)
yaw = syaw + turn
try:
    m = j.apply_manual(m, {'x': round(x, 4), 'y': round(y, 4), 'yaw_deg': round(yaw, 2),
                           'tape': {'forward_m': fwd, 'left_m': left, 'turn_deg': turn}}, overwrite=overwrite)
except ValueError as e:
    sys.exit(f'{path}: {e}')
json.dump(m, open(path, 'w'), indent=1)
e = m['measured_err']
print(f'{path}: manual final ({x:.3f}, {y:.3f}, {yaw:.1f} deg), error {e["pos_m"] * 100:.1f} cm / '
      f'{e["yaw_deg"]:.1f} deg -> {m["outcome"]} ({m["outcome_reason"]})')
