#!/usr/bin/env python3
# 한글: Gazebo 회피 주행 시험의 지표(정답 위치 기준). ROS 없이 순수 함수 — 단위시험 test_avoid_metrics.py.
#       입력은 Gazebo 정답 자세(로봇·상자), 컨트롤러 명령(vy), 전역 경로(/plan). prd/sim-avoidance-precision-test-plan.md의 정의.
"""Metrics of one avoidance trial from Gazebo ground truth (pure functions, no ROS).

Frames: world = map (Gazebo world coordinates). Lateral offsets are signed, left of the start->goal line positive.
  min_clearance   smallest gap (m) between the robot footprint rectangle and the box rectangle; <= 0 = contact
  box_moved       how far the box was pushed (m)
  detour_width    max |lateral offset| of the robot centre from the start->goal line
  hesitation      vy sign flips per second and stopped seconds while within 1 m of the box
  heading_dev     max |robot yaw - line yaw| within 0.8 m of the box (body kept facing forward = small)
  plan_flips      how often the global path switched sides of the box between replans
"""
import math

import numpy as np

NEAR_BOX_M = 1.0        # hesitation zone
AVOID_ZONE_M = 0.8      # heading deviation zone
STOP_SPEED = 0.01       # m/s below this = stopped
PLAN_SIDE_HYST = 0.02   # m: plan passing closer than this to the box centre line is not counted as a side


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


def rect_corners(x, y, yaw, hx, hy):
    """Corners of an oriented rectangle (half sizes hx, hy)."""
    c, s = math.cos(yaw), math.sin(yaw)
    return np.array([[x + c * dx - s * dy, y + s * dx + c * dy]
                     for dx, dy in ((hx, hy), (-hx, hy), (-hx, -hy), (hx, -hy))])


def _axes(poly):
    out = []
    for i in range(len(poly)):
        e = poly[(i + 1) % len(poly)] - poly[i]
        n = np.array([-e[1], e[0]])
        out.append(n / np.linalg.norm(n))
    return out


def _point_segment(p, a, b):
    ab = b - a
    t = float(np.clip((p - a) @ ab / (ab @ ab), 0.0, 1.0))
    return float(np.linalg.norm(p - (a + t * ab)))


def rect_gap(a, b):
    """Distance between two convex polygons (>= 0), or minus the penetration depth when they overlap."""
    best = -math.inf
    for axis in _axes(a) + _axes(b):
        pa, pb = a @ axis, b @ axis
        best = max(best, max(pa.min() - pb.max(), pb.min() - pa.max()))
    if best <= 0.0:
        return best
    d = math.inf
    for p, poly in ((a, b), (b, a)):
        for v in p:
            for i in range(len(poly)):
                d = min(d, _point_segment(v, poly[i], poly[(i + 1) % len(poly)]))
    return d


def line_frame(start, goal):
    """Unit direction of start->goal and its yaw."""
    d = np.array([goal[0] - start[0], goal[1] - start[1]], float)
    n = np.linalg.norm(d)
    return d / n, math.atan2(d[1], d[0])


def lateral(p, start, direction):
    """Signed offset of p from the start->goal line, left positive."""
    v = np.array([p[0] - start[0], p[1] - start[1]], float)
    return float(direction[0] * v[1] - direction[1] * v[0])


def speed_series(t, x, y, window=0.2):
    """Ground-truth speed (m/s) from positions over a ~window second span."""
    t, x, y = map(np.asarray, (t, x, y))
    out = np.zeros(len(t))
    j = 0
    for i in range(len(t)):
        while t[i] - t[j] > window:
            j += 1
        if t[i] > t[j]:
            out[i] = math.hypot(x[i] - x[j], y[i] - y[j]) / (t[i] - t[j])
    return out


def plan_sides(plans, box_center, start, direction):
    """Side of the box centre line each plan passes on: +1 left, -1 right (plans that do not reach the box skipped)."""
    s_b = float((np.asarray(box_center) - np.asarray(start[:2])) @ direction)
    l_b = lateral(box_center, start, direction)
    sides = []
    for _, pts in plans:
        pts = np.asarray(pts, float)
        if len(pts) < 2:
            continue
        s = (pts - np.asarray(start[:2])) @ direction
        near = np.abs(s - s_b) < 0.05
        if not near.any():
            continue
        off = np.array([lateral(p, start, direction) for p in pts[near]]).mean() - l_b
        if abs(off) >= PLAN_SIDE_HYST:
            sides.append(1 if off > 0 else -1)
    return sides


def count_flips(seq):
    """Number of changes of value in a sequence."""
    return sum(1 for a, b in zip(seq, seq[1:]) if a != b)


def vy_flips(cmd_t, cmd_vy, mask_t=None, threshold=0.01):
    """Sign changes of vy (|vy| > threshold), optionally only samples whose time passes mask_t(t)."""
    last, flips = 0, 0
    for t, vy in zip(cmd_t, cmd_vy):
        if mask_t is not None and not mask_t(t):
            continue
        s = 0 if abs(vy) < threshold else (1 if vy > 0 else -1)
        if s and last and s != last:
            flips += 1
        if s:
            last = s
    return flips


def summarize(gt, cmd, plans, start, goal, box_size, footprint_half=(0.19, 0.14), status='succeeded'):
    """Metrics dict of one trial.

    gt     dict of arrays: t, rx, ry, ryaw, bx, by, byaw (ground truth, same length, time ascending)
    cmd    dict of arrays: t, vx, vy, wz (controller command)
    plans  list of (t, Nx2 points of /plan)
    start, goal  (x, y, yaw_rad) map frame
    box_size (sx, sy) m, footprint_half (hx, hy) m
    """
    t = np.asarray(gt['t'], float)
    rx, ry, ryaw = (np.asarray(gt[k], float) for k in ('rx', 'ry', 'ryaw'))
    bx, by, byaw = (np.asarray(gt[k], float) for k in ('bx', 'by', 'byaw'))
    direction, line_yaw = line_frame(start, goal)
    box_poly = [rect_corners(bx[i], by[i], byaw[i], box_size[0] / 2, box_size[1] / 2) for i in range(len(t))]
    gaps = np.array([rect_gap(rect_corners(rx[i], ry[i], ryaw[i], *footprint_half), box_poly[i])
                     for i in range(len(t))])
    dist_box = np.hypot(rx - bx, ry - by)
    near = dist_box < NEAR_BOX_M
    near_dt = float(np.sum(np.diff(t, prepend=t[0])[near])) if len(t) else 0.0

    speed = speed_series(t, rx, ry)
    dist_goal = np.hypot(rx - goal[0], ry - goal[1])
    moving_phase = (t - t[0] > 1.0) & (dist_goal > 0.15)
    stop_s = float(np.sum(np.diff(t, prepend=t[0])[near & moving_phase & (speed < STOP_SPEED)]))

    def near_time(tt):
        i = int(np.searchsorted(t, tt))
        return bool(near[min(i, len(near) - 1)])
    flips_near = vy_flips(cmd['t'], cmd['vy'], near_time) if len(cmd['t']) else 0

    yaw_dev = np.array([abs(wrap(a - line_yaw)) for a in ryaw])
    zone = dist_box < AVOID_ZONE_M
    sides = plan_sides(plans, (bx[0], by[0]), start, direction) if plans else []
    lat = np.array([lateral((rx[i], ry[i]), start, direction) for i in range(len(t))])
    final = (rx[-1], ry[-1], ryaw[-1])
    return {
        'status': status,
        'time_s': float(t[-1] - t[0]),
        'min_clearance_m': float(gaps.min()),
        'box_moved_m': float(np.max(np.hypot(bx - bx[0], by - by[0]))),
        'detour_width_m': float(np.abs(lat).max()),
        'pos_err_m': float(math.hypot(final[0] - goal[0], final[1] - goal[1])),
        'yaw_err_deg': float(math.degrees(abs(wrap(final[2] - goal[2])))),
        'vy_flips_near': int(flips_near),
        'vy_flips_per_s_near': float(flips_near / near_dt) if near_dt > 0.5 else float('nan'),
        'stopped_s_near': stop_s,
        'near_time_s': near_dt,
        'heading_dev_deg_near': float(math.degrees(yaw_dev[zone].max())) if zone.any() else float('nan'),
        'heading_dev_deg_all': float(math.degrees(yaw_dev.max())),
        'plan_flips': int(count_flips(sides)),
        'plan_sides': ''.join('L' if s > 0 else 'R' for s in sides[:60]),
        'n_plans': len(plans),
    }


# ---- 동적 장애물 지표 (체크리스트 8.16, prd/sim-dynamic-avoidance-test-plan.md) ----
# Dynamic-obstacle metrics. Obstacles: kind 'person' (two leg circles) or 'box' (rectangle), ground-truth pose arrays.
DYN_NEAR_M = 1.0          # an obstacle counts as "near" within this gap / 이 간격 안이면 가까운 장애물
CORRIDOR_MARGIN = 0.10    # robot corridor half width = robot half width + this / 로봇 통로 반폭 = 몸 반폭 + 여유
RESUME_SPEED = 0.03       # m/s: moving again / 다시 움직임


def point_rect_signed(p, poly):
    """Distance from point p to a convex polygon, negative (minus depth) when p is inside."""
    p = np.asarray(p, float)
    d = min(_point_segment(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))
    inside = all(np.cross(poly[(i + 1) % len(poly)] - poly[i], p - poly[i]) >= 0 for i in range(len(poly)))
    return -d if inside else d


def obstacle_gap(robot_poly, obs, i, legs, leg_r, box_half, feet=()):
    """Gap (m) between the robot polygon and obstacle `obs` at sample i (person legs + feet, or box).

    feet: rectangles (cx, cy, hx, hy) in the person frame (2026-10-28, troubleshooting/056: a foot was run over in the real test).
    한글: 사람은 다리(원)와 발(사각형) 중 가장 가까운 것까지의 간격.
    """
    x, y, yaw = obs['x'][i], obs['y'][i], obs['yaw'][i]
    if obs['kind'] == 'person':
        c, s = math.cos(yaw), math.sin(yaw)
        gap = min(point_rect_signed((x + c * lx - s * ly, y + s * lx + c * ly), robot_poly) - leg_r for lx, ly in legs)
        for fx, fy, hx, hy in feet:
            gap = min(gap, rect_gap(robot_poly, rect_corners(x + c * fx - s * fy, y + s * fx + c * fy, yaw, hx, hy)))
        return gap
    return rect_gap(robot_poly, rect_corners(x, y, yaw, *obs.get('half', box_half)))


def dynamic_summary(gt, obstacles, start, goal, footprint_half=(0.166, 0.13), legs=((0.0, 0.10), (0.0, -0.10)),
                    leg_r=0.06, box_half=(0.165, 0.11), parked_x=7.0, feet=()):
    """Metrics against moving obstacles.

    gt         dict of arrays t, rx, ry, ryaw (ground truth)
    obstacles  list of dicts {kind: 'person'|'box', x, y, yaw} (arrays aligned with gt; x > parked_x = parked)
    returns    dyn_min_gap_m (nan when no obstacle in the room), dyn_contact, dyn_stop_gap_m (gap when the robot first stopped
               with an obstacle near, nan if it never did), dyn_wait_s (stopped seconds outside the start/goal zones),
               dyn_resume_delay_s (max over episodes: obstacle left the corridor ahead -> robot moving again; nan if none)
    """
    t = np.asarray(gt['t'], float)
    rx, ry, ryaw = (np.asarray(gt[k], float) for k in ('rx', 'ry', 'ryaw'))
    n = len(t)
    speed = speed_series(t, rx, ry)
    dt = np.diff(t, prepend=t[0])
    direction, _ = line_frame(start, goal)
    gaps = np.full(n, np.inf)
    blocking = np.zeros(n, bool)      # an obstacle in the robot corridor ahead / 로봇 앞 통로에 장애물
    half_w = footprint_half[1] + CORRIDOR_MARGIN
    for i in range(n):
        poly = rect_corners(rx[i], ry[i], ryaw[i], *footprint_half)
        for obs in obstacles:
            if obs['x'][i] > parked_x:
                continue
            gaps[i] = min(gaps[i], obstacle_gap(poly, obs, i, legs, leg_r, box_half, feet))
            rel = np.array([obs['x'][i] - rx[i], obs['y'][i] - ry[i]])
            ahead = float(rel @ direction)
            lat = float(direction[0] * rel[1] - direction[1] * rel[0])
            reach = leg_r + abs(legs[0][1]) if obs['kind'] == 'person' else max(obs.get('half', box_half))
            remaining = float((np.asarray(goal[:2]) - np.array([rx[i], ry[i]])) @ direction)
            if 0.0 < ahead < remaining + footprint_half[0] and abs(lat) < half_w + reach:
                blocking[i] = True
    in_room = np.isfinite(gaps)
    # 접촉 중 로봇이 움직였나(로봇 탓) / was the robot moving during contact (robot's fault vs obstacle walking into it)
    contact_moving = bool(np.any(in_room & (gaps <= 0.0) & (speed >= 0.02)))
    stopped = (speed < STOP_SPEED) & (t - t[0] > 1.0) & (np.hypot(rx - goal[0], ry - goal[1]) > 0.15)
    near = in_room & (gaps < DYN_NEAR_M)
    first_stop = np.nonzero(stopped & near)[0]
    delays = []
    i = 1
    while i < n:
        if blocking[i - 1] and not blocking[i] and speed[i] < RESUME_SPEED:
            j = i
            while j < n and speed[j] < RESUME_SPEED:
                j += 1
            if j < n:
                delays.append(t[j] - t[i])
            i = j
        i += 1
    return {
        'dyn_min_gap_m': float(gaps[in_room].min()) if in_room.any() else float('nan'),
        'dyn_contact': bool(in_room.any() and gaps[in_room].min() <= 0.0),
        'dyn_contact_moving': contact_moving,
        'dyn_stop_gap_m': float(gaps[first_stop[0]]) if len(first_stop) else float('nan'),
        'dyn_wait_s': float(np.sum(dt[stopped])),
        'dyn_resume_delay_s': float(max(delays)) if delays else float('nan'),
        'dyn_blocked_s': float(np.sum(dt[blocking])),
    }
