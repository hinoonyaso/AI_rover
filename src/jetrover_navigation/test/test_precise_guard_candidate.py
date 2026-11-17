# Offline candidate tests; no ROS or actuator commands.
# 한글: 오프라인 후보 단위시험이며 ROS 또는 구동 명령을 사용하지 않는다.
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from precise_guard_candidate import path_clear  # noqa: E402


def grid():
    return [0] * 100


def check(data, start=(2.5, 5.5), end=(7.5, 5.5), radius=0.4, **kwargs):
    return path_clear(data, 10, 10, 1.0, (0.0, 0.0), start, end, radius, **kwargs)


def test_empty_and_obstacle_through_middle():
    cells = grid()
    assert check(cells)
    cells[5 * 10 + 5] = 100
    assert not check(cells)


def test_near_corner_and_unknown_are_blocked():
    cells = grid()
    cells[6 * 10 + 5] = 100
    assert not check(cells)  # conservative cell radius includes the corner
    cells[6 * 10 + 5] = -1
    assert not check(cells)


def test_obstacle_away_and_rotation_in_place():
    cells = grid()
    cells[8 * 10 + 5] = 100
    assert check(cells)
    cells[5 * 10 + 5] = 100
    assert not check(cells, start=(5.5, 5.5), end=(5.5, 5.5))


def test_map_boundary_and_invalid_data_fail_closed():
    assert not check(grid(), start=(0.1, 5.0))
    assert not check(grid()[:-1])
    assert not check(grid(), radius=float('nan'))
    cells = grid()
    cells[5 * 10 + 5] = 101
    assert not check(cells)


def test_threshold_is_explicit():
    cells = grid()
    cells[5 * 10 + 5] = 75
    assert check(cells, blocked_at=100)
    assert not check(cells, blocked_at=75)
