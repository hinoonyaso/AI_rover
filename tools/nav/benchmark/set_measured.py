#!/usr/bin/env python3
# 한글: 줄자 실측(출발 표시 대비 앞/좌 이동 거리, 방향 변화)을 meta.json의 measured_final(지도 좌표)로 기록한다.
#       analyze.py는 measured_final이 있으면 그것으로 목표 오차를 계산한다(AMCL/TF는 로봇 자기 추정이라 독립 정답이 아님).
"""Store the tape-measured final pose in meta.json (analyze.py prefers it over the robot's own estimate).

Usage: set_measured.py <tag> <A|B|C> <trial#> <forward_m> <left_m> [<turn_deg, + = CCW>]
Measured from the start mark with the same reference point on the robot, in the START body frame
(forward = the start heading). The start pose is the nominal START of run_trial.py (the robot is placed
on the start mark and AMCL is set there). 2026-10-10 E6: the auto goal error is the robot's own belief
and sits at the goal checker tolerance (0.15 m) in every condition, so only the tape tells odometry apart.
"""
import json
import math
import sys

START = (1.05, 0.10, 90.0)  # nominal start of run_trial.py

tag, sc, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
fwd, left = float(sys.argv[4]), float(sys.argv[5])
turn = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0
path = 'bags/%s/trial_%s%02d/meta.json' % (tag, sc, n)
m = json.load(open(path))
# The tape is measured from where the robot really started: the scan-matched start (E6 v2) when recorded,
# else the nominal START (v1 runs forced AMCL there). 한글: 실제 출발 위치(스캔 매칭) 기준으로 환산.
start = m.get('auto', {}).get('amcl_start') if m.get('auto', {}).get('start_from') == 'scan_match' else None
sx, sy, syaw = start if start else START
h = math.radians(syaw)
x = sx + fwd * math.cos(h) - left * math.sin(h)
y = sy + fwd * math.sin(h) + left * math.cos(h)
yaw = syaw + turn
m['measured_final'] = {'x': round(x, 4), 'y': round(y, 4), 'yaw_deg': round(yaw, 2),
                       'tape': {'forward_m': fwd, 'left_m': left, 'turn_deg': turn}}
g = m['goal']
err = math.hypot(x - g['x'], y - g['y'])
yaw_err = abs((yaw - g['yaw_deg'] + 180) % 360 - 180)
m['measured_err'] = {'pos_m': round(err, 4), 'yaw_deg': round(yaw_err, 2)}
# pass/fail on the measurement (test plan: <= 0.15 m, <= 0.4 rad, success, no collision)
auto = m.get('auto', {})
ok = auto.get('action_status') == 'succeeded' and auto.get('elapsed_s', 99) <= 60
ok = ok and err <= 0.15 and math.radians(yaw_err) <= 0.4 and not m.get('collision')
if sc == 'B':
    ok = ok and abs(x - START[0]) <= 0.10
if m.get('outcome') != 'invalid':
    m['outcome'] = 'success' if ok else 'fail'
json.dump(m, open(path, 'w'), indent=1)
print(f'{path}: measured final ({x:.3f}, {y:.3f}, {yaw:.1f} deg), '
      f'error {err * 100:.1f} cm / {yaw_err:.1f} deg -> {m["outcome"]}')
