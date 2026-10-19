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
