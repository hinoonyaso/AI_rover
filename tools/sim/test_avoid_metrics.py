# 한글: avoid_metrics.py 단위시험(합성 궤적, ROS 없음). 실행: python3 -m pytest tools/sim/test_avoid_metrics.py
# Unit tests of the avoidance metrics on synthetic trajectories. Run: python3 -m pytest tools/sim/test_avoid_metrics.py
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import avoid_metrics as M  # noqa: E402

START, GOAL = (1.0, 0.4, math.radians(90)), (1.0, 1.4, math.radians(90))
BOX = (1.2, 1.0)             # centre; 0.33 (x) x 0.22 (y)
BOX_SIZE = (0.33, 0.22)


def test_rect_gap_disjoint_overlap_and_rotated():
    a = M.rect_corners(0, 0, 0, 0.5, 0.5)
    assert abs(M.rect_gap(a, M.rect_corners(2.0, 0, 0, 0.5, 0.5)) - 1.0) < 1e-9
    assert M.rect_gap(a, M.rect_corners(0.8, 0, 0, 0.5, 0.5)) < 0           # overlap 0.2
    assert abs(M.rect_gap(a, M.rect_corners(0.8, 0, 0, 0.5, 0.5)) + 0.2) < 1e-9
    assert M.rect_gap(a, M.rect_corners(1.0, 0, 0, 0.5, 0.5)) == 0.0         # touching
    # a 45 deg rotated square 2 m away along x: its corner points at the other square
    gap = M.rect_gap(a, M.rect_corners(2.0, 0, math.pi / 4, 0.5, 0.5))
    assert abs(gap - (2.0 - 0.5 - 0.5 * math.sqrt(2))) < 1e-9


def test_rect_gap_corner_to_corner_is_euclidean():
    a = M.rect_corners(0, 0, 0, 0.5, 0.5)
    b = M.rect_corners(2.0, 2.0, 0, 0.5, 0.5)
    assert abs(M.rect_gap(a, b) - math.hypot(1.0, 1.0)) < 1e-9


def test_lateral_left_positive():
    d, _ = M.line_frame(START, GOAL)            # heading +y
    assert abs(M.lateral((0.8, 0.9), START, d) - 0.2) < 1e-9     # 20 cm left of the +y line (x smaller)
    assert M.lateral((1.3, 0.9), START, d) < 0


def drive(offsets, speed=0.12, hz=20, stop_at=None, yaw=None):
    """Robot driving along +y from y=0.4 to 1.4 with the given lateral offset function of y."""
    t, rx, ry, ryaw = [], [], [], []
    y, k = 0.4, 0
    while y <= 1.4:
        t.append(k / hz)
        ry.append(y)
        rx.append(1.0 - offsets(y))            # left of +y travel is -x
        ryaw.append(math.radians(90) if yaw is None else yaw(y))
        if not (stop_at and stop_at[0] <= y <= stop_at[1]):
            y += speed / hz
        else:
            stop_at = (stop_at[0], stop_at[1] - 1e-9)   # still stopped; time advances
        k += 1
        if k > 100000:
            break
    n = len(t)
    return {'t': t, 'rx': rx, 'ry': ry, 'ryaw': ryaw, 'bx': [BOX[0]] * n, 'by': [BOX[1]] * n, 'byaw': [0.0] * n}


def test_summarize_clean_detour_has_positive_clearance_and_no_flips():
    # 30 cm to the left, held until the whole robot is past the box (rear edge y - 0.19 > box top 1.11 -> y > 1.30)
    gt = drive(lambda y: float(np.interp(y, [0.4, 0.7, 1.3, 1.4], [0.0, 0.3, 0.3, 0.0])))
    out = M.summarize(gt, {'t': [], 'vy': []}, [], START, GOAL, BOX_SIZE)
    assert out['min_clearance_m'] > 0.05
    assert abs(out['detour_width_m'] - 0.30) < 0.01
    assert out['box_moved_m'] == 0.0
    assert out['vy_flips_near'] == 0 and out['heading_dev_deg_near'] < 1.0
    assert out['pos_err_m'] < 0.02


def test_summarize_straight_through_box_is_contact():
    gt = drive(lambda y: -0.2)       # x = 1.2: centred on the box
    out = M.summarize(gt, {'t': [], 'vy': []}, [], START, GOAL, BOX_SIZE)
    assert out['min_clearance_m'] < 0


def test_stopped_seconds_near_the_box():
    gt = drive(lambda y: 0.25, stop_at=(0.9, 0.9001))      # waits at y 0.9 (within 1 m of the box)
    out_run = M.summarize(drive(lambda y: 0.25), {'t': [], 'vy': []}, [], START, GOAL, BOX_SIZE)
    assert out_run['stopped_s_near'] < 0.3
    gt['t'] = list(gt['t'])
    assert out_run['near_time_s'] > 3.0


def test_hesitation_vy_flips_counted_only_near_box():
    gt = drive(lambda y: 0.25)
    t = np.array(gt['t'])
    vy = np.array([0.05 if (i // 5) % 2 == 0 else -0.05 for i in range(len(t))])   # flips every 0.25 s
    out = M.summarize(gt, {'t': t, 'vy': vy}, [], START, GOAL, BOX_SIZE)
    assert out['vy_flips_near'] > 10
    assert out['vy_flips_per_s_near'] > 2.0
    assert M.vy_flips([0, 1, 2], [0.05, 0.05, 0.05]) == 0
    assert M.vy_flips([0, 1, 2], [0.05, 0.0, -0.05]) == 1          # zero in between does not hide the flip


def test_heading_deviation_zone():
    gt = drive(lambda y: 0.25, yaw=lambda y: math.radians(90 + 40) if 0.8 < y < 1.2 else math.radians(90))
    out = M.summarize(gt, {'t': [], 'vy': []}, [], START, GOAL, BOX_SIZE)
    assert abs(out['heading_dev_deg_near'] - 40.0) < 1.0


def test_plan_sides_and_flips():
    d, _ = M.line_frame(START, GOAL)

    def plan(lateral_off):       # a path along +y passing the box with the given offset from the line
        ys = np.linspace(0.4, 1.4, 30)
        return [(0.0, np.stack([1.0 - lateral_off * np.ones_like(ys), ys], axis=1))]
    left, right = plan(0.3)[0], plan(-0.3)[0]       # left of travel = smaller x ... relative to the box at x 1.2
    # passing at x 0.7 (left of the box centre line when travelling +y) / x 1.3 (right)
    seq = [left, right, left, left, right]
    sides = M.plan_sides(seq, BOX, START, d)
    assert sides == [1, -1, 1, 1, -1] and M.count_flips(sides) == 3
    # a plan that goes straight through the box centre line gives no side (hysteresis)
    straight = (0.0, np.stack([np.full(30, 1.2), np.linspace(0.4, 1.4, 30)], axis=1))
    assert M.plan_sides([straight], BOX, START, d) == []
    # a plan that stops short of the box is ignored
    short = (0.0, np.stack([np.full(10, 0.8), np.linspace(0.4, 0.6, 10)], axis=1))
    assert M.plan_sides([short], BOX, START, d) == []


def test_speed_series():
    t = np.arange(0, 2, 0.05)
    x = 0.1 * t
    s = M.speed_series(t, x, np.zeros_like(t))
    assert abs(s[-1] - 0.1) < 1e-9 and s[0] == 0.0


# ---- dynamic obstacles ----
def _line_run(stop_between=None, speed=0.1, hz=20, t_end=12.0):
    """Robot on x = 1.0 driving +y from 0.3; optionally standing still between two times."""
    t = np.arange(0.0, t_end, 1.0 / hz)
    y = np.empty_like(t)
    pos = 0.3
    for k, tk in enumerate(t):
        y[k] = pos
        if not (stop_between and stop_between[0] <= tk < stop_between[1]):
            pos += speed / hz
    return {'t': t, 'rx': np.full_like(t, 1.0), 'ry': y, 'ryaw': np.full_like(t, math.pi / 2)}


def test_point_rect_signed_inside_negative():
    sq = M.rect_corners(0, 0, 0, 0.5, 0.5)
    assert abs(M.point_rect_signed((1.0, 0.0), sq) - 0.5) < 1e-9
    assert abs(M.point_rect_signed((0.4, 0.0), sq) + 0.1) < 1e-9


def test_dynamic_crossing_person_stop_and_resume():
    gt = _line_run(stop_between=(2.0, 6.0))
    t = gt['t']
    # person crosses y = 1.0 from x 1.6 to 0.4 between t 2 and 6 s (robot waits at y 0.5)
    px = np.where(t < 2.0, 9.0, np.where(t > 6.0, 9.0, 1.6 - 0.3 * (t - 2.0)))
    obs = [{'kind': 'person', 'x': px, 'y': np.full_like(t, 1.0), 'yaw': np.full_like(t, math.pi)}]
    out = M.dynamic_summary(gt, obs, (1.0, 0.3, math.pi / 2), (1.0, 1.4, math.pi / 2))
    # robot front at y 0.666 while waiting, nearest leg surface at y 0.84 -> 0.174 m
    assert not out['dyn_contact'] and abs(out['dyn_min_gap_m'] - 0.174) < 0.01
    assert 3.5 < out['dyn_wait_s'] < 4.5
    assert out['dyn_stop_gap_m'] > 0.2
    # the person leaves the corridor (x < 1.0 - 0.23 - 0.16) at t ~5.3; the robot starts at t 6
    assert 0.5 < out['dyn_resume_delay_s'] < 0.9
    assert out['dyn_blocked_s'] > 0.5


def test_dynamic_box_contact_and_parked():
    gt = _line_run()
    t = gt['t']
    bx = np.where(t < 3.0, 9.0, 1.0)                  # box appears on the line at y 0.85 at t 3 (robot drives through it)
    obs = [{'kind': 'box', 'x': bx, 'y': np.full_like(t, 0.85), 'yaw': np.zeros_like(t)}]
    out = M.dynamic_summary(gt, obs, (1.0, 0.3, math.pi / 2), (1.0, 1.4, math.pi / 2))
    assert out['dyn_contact'] and out['dyn_min_gap_m'] < 0 and out['dyn_contact_moving']
    none = M.dynamic_summary(gt, [{'kind': 'box', 'x': np.full_like(t, 9.0), 'y': t * 0, 'yaw': t * 0}],
                             (1.0, 0.3, math.pi / 2), (1.0, 1.4, math.pi / 2))
    assert math.isnan(none['dyn_min_gap_m']) and not none['dyn_contact'] and math.isnan(none['dyn_resume_delay_s'])


def test_person_gap_counts_feet():
    # 발(사각형)이 몸 앞에 있으면 다리보다 먼저 닿는다 / a foot ahead of the legs touches before the legs do
    poly = M.rect_corners(0.0, 0.0, 0.0, 0.166, 0.13)
    # person at x 0.60 facing -x (yaw pi): legs 0.60 ahead, feet reach 0.60 - 0.18 = 0.42
    obs = {'kind': 'person', 'x': [0.60], 'y': [0.0], 'yaw': [math.pi]}
    legs = ((0.0, 0.10), (0.0, -0.10))
    no_feet = M.obstacle_gap(poly, obs, 0, legs, 0.06, (0.1, 0.1))
    with_feet = M.obstacle_gap(poly, obs, 0, legs, 0.06, (0.1, 0.1), ((0.06, 0.10, 0.12, 0.05), (0.06, -0.10, 0.12, 0.05)))
    assert abs(no_feet - (0.60 - 0.06 - 0.166)) < 1e-6
    assert abs(with_feet - (0.42 - 0.166)) < 1e-6


def test_obstacle_feet_override_default():
    # 장애물마다 발 모양(obs['feet'])이 기본값보다 우선 / per-obstacle feet win over the default
    poly = M.rect_corners(0.0, 0.0, 0.0, 0.166, 0.13)
    legs = ((0.0, 0.10), (0.0, -0.10))
    long_feet = ((0.06, 0.10, 0.12, 0.05), (0.06, -0.10, 0.12, 0.05))
    short = ((0.04, 0.10, 0.10, 0.05), (0.04, -0.10, 0.10, 0.05))
    obs = {'kind': 'person', 'x': [0.60], 'y': [0.0], 'yaw': [math.pi], 'feet': short}
    gap = M.obstacle_gap(poly, obs, 0, legs, 0.06, (0.1, 0.1), long_feet)
    assert abs(gap - (0.60 - 0.14 - 0.166)) < 1e-6
