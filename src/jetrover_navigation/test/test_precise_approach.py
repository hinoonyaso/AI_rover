# 한글: 정밀 접근 제어식의 단위시험(ROS 없이). Unit tests of the precise approach law (no ROS).
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
from precise_approach import (  # noqa: E402, I100
    approach_command, body_error, scan_match_published, wrap)

V_MAX, W_MAX = 0.06, 0.25


def test_zero_inside_tolerances():
    assert approach_command(0.01, 0.01, math.radians(1.0)) == (0.0, 0.0, 0.0)


def test_speed_is_capped_and_never_above_v_max():
    for d in (0.05, 0.1, 0.2, 0.3):
        vx, vy, _ = approach_command(d, 0.0, 0.0)
        assert 0.0 < vx <= V_MAX + 1e-12 and vy == 0.0


def test_floor_speed_keeps_moving_for_small_errors():
    vx, vy, _ = approach_command(0.03, 0.0, 0.0)
    assert vx >= 0.025 - 1e-12      # above the 2 cm tolerance: not slower than v_min
    vx, vy, _ = approach_command(0.021, 0.0, 0.0)
    assert 0.0 < vx <= 0.021 / 0.5 + 1e-12


def test_never_overshoots_in_half_a_second():
    for d in (0.025, 0.03, 0.05):
        vx, _, _ = approach_command(d, 0.0, 0.0)
        assert vx * 0.5 <= d + 1e-12


def test_direction_follows_the_error_in_the_body_frame():
    vx, vy, wz = approach_command(0.1, -0.1, math.radians(-30))
    assert vx > 0 and vy < 0 and wz < 0
    assert abs(math.hypot(vx, vy) - V_MAX) < 1e-9
    assert abs(vx + vy) < 1e-9          # 45 deg diagonal


def test_yaw_is_capped_and_has_a_floor():
    assert abs(approach_command(0.0, 0.0, math.radians(120))[2]) <= W_MAX + 1e-12
    assert abs(approach_command(0.0, 0.0, math.radians(3.0))[2]) >= 0.08 - 1e-12


def test_body_error_rotates_into_the_robot_frame():
    # robot at the origin facing +y; goal 0.1 ahead (= +y in the map), 0.05 to its left (= -x)
    ex, ey, eyaw = body_error((0.0, 0.0, math.pi / 2), (-0.05, 0.1, math.pi / 2 + 0.2))
    assert abs(ex - 0.1) < 1e-9 and abs(ey - 0.05) < 1e-9 and abs(eyaw - 0.2) < 1e-9
    assert abs(wrap(2 * math.pi + 0.1) - 0.1) < 1e-9


def test_converges_in_a_simulated_loop():
    x, y, yaw = 0.0, 0.0, 0.0
    goal = (0.12, -0.08, math.radians(25))
    dt = 0.05
    for _ in range(int(20 / dt)):
        ex, ey, eyaw = body_error((x, y, yaw), goal)
        vx, vy, wz = approach_command(ex, ey, eyaw)
        c, s = math.cos(yaw), math.sin(yaw)
        x += (c * vx - s * vy) * dt
        y += (s * vx + c * vy) * dt
        yaw += wz * dt
    ex, ey, eyaw = body_error((x, y, yaw), goal)
    assert math.hypot(ex, ey) < 0.02 and abs(eyaw) < math.radians(2.0)


def test_scan_match_published_parses_the_initialpose_line():
    log = '[INFO] [scan_match_init]: published /initialpose (1.10, 0.22, 107deg)\n...'
    ok, pose = scan_match_published(log)
    assert ok and pose == (1.10, 0.22, 107.0)
    ok, pose = scan_match_published('[WARN] not confident (score 0.71)')
    assert not ok and pose is None
