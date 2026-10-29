# 한글: dyn_obstacles.py 움직임 계산 단위시험(ROS 없음). 실행: python3 -m pytest tools/sim/test_dyn_obstacles.py
# Unit tests of the dynamic-obstacle motion maths (no ROS).
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dyn_obstacles as D  # noqa: E402


def test_point_along_polyline_and_end():
    path = [(0.0, 0.0), (1.0, 0.0), (1.0, 2.0)]
    assert D.path_length(path) == 3.0
    assert D.point_along(path, 0.5) == ((0.5, 0.0), False)
    p, done = D.point_along(path, 2.0)
    assert math.isclose(p[0], 1.0) and math.isclose(p[1], 1.0) and not done
    assert D.point_along(path, 3.5) == ((1.0, 2.0), True)
    assert D.point_along(path, -1.0) == ((0.0, 0.0), False)


def test_motion_pose_speed_and_parking():
    m = D.Motion('person_0', [(1.5, 1.0), (0.5, 1.0)], 0.5, after_s=0.0)
    assert D.motion_pose(m, 10.0) is None              # not triggered yet
    m.started_at = 10.0
    x, y = D.motion_pose(m, 11.0)
    assert math.isclose(x, 1.0) and math.isclose(y, 1.0)   # 0.5 m/s for 1 s
    assert D.motion_pose(m, 12.5) is None                 # path ended -> parked
    m.park_at_end = False
    assert D.motion_pose(m, 12.5) == (0.5, 1.0)


def test_appear_motion_stays():
    m = D.Motion('dyn_box', [(1.0, 0.85)], 0.0, robot_progress_m=0.05, park_at_end=False)
    m.started_at = 3.0
    assert D.motion_pose(m, 100.0) == (1.0, 0.85)


def test_progress_and_triggers():
    start, goal = (1.0, 0.3), (1.0, 1.3)
    assert math.isclose(D.progress((1.2, 0.8), start, goal), 0.5)
    m = D.Motion('dyn_box', [(1.0, 0.85)], 0.0, robot_progress_m=0.05)
    assert not D.triggered(m, 5.0, 0.04)
    assert D.triggered(m, 0.0, 0.05)
    assert not D.triggered(m, 0.0, None)
    t = D.Motion('person_0', [(0, 0), (1, 0)], 0.5, after_s=1.0)
    assert not D.triggered(t, 0.9, None) and D.triggered(t, 1.0, None)


def test_scenarios_cross_the_robot_line():
    sc = D.scenarios()
    assert set(sc) == {'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D12', 'D13', 'N50', 'N60'}
    gl, gr = (m.path[0] for m in sc['N50']['motions'])
    assert abs((gr[0] - gl[0]) - D.GATE_SIZE[0] - 0.50) < 1e-9      # gap between the inner wall ends = 0.50
    for name in ('D1', 'D3'):
        m = sc[name]['motions'][0]
        xs = [p[0] for p in m.path]
        assert min(xs) < 1.0 < max(xs), name           # crosses x = 1.0 (the A-B line)
    assert sc['D1']['motions'][0] is not D.scenarios()['D1']['motions'][0]   # fresh objects each call


def test_pause_at_waypoint():
    m = D.Motion('person_0', [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)], 0.5, pause_at=1, pause_s=4.0)
    m.started_at = 0.0
    assert D.motion_pose(m, 1.0) == (0.5, 0.0)
    assert D.motion_pose(m, 2.0) == (1.0, 0.0)          # arrives at the waypoint
    assert D.motion_pose(m, 5.5) == (1.0, 0.0)          # still standing (2 + 4 = 6 s)
    x, _ = D.motion_pose(m, 7.0)
    assert abs(x - 1.5) < 1e-9                          # walking again


def test_beside_scenarios_feet_point_into_the_lane():
    # D8~D10: 사람이 경로선(x 약 1.01) 왼쪽에서 경로를 보고(+x) 서 있음, 발끝이 선에서 0.17/0.12/0.07 m
    # person left of the line facing it; toe tips 0.17 / 0.12 / 0.07 m from the line
    sc = D.scenarios()
    for name, off, toe in (('D8', 0.35, 0.17), ('D9', 0.30, 0.12), ('D10', 0.25, 0.07)):
        m = sc[name]['motions'][0]
        (x, y), = m.path
        assert m.speed == 0.0 and not m.park_at_end and m.yaw_deg == 0.0
        assert abs((1.01 - x) - off) < 1e-9, name
        tip = max(fx + hx for fx, fy, hx, hy in D.PERSON_FEET)
        assert abs((1.01 - (x + tip)) - toe) < 1e-9, name


def test_short_feet_scenarios_reproduce_the_accident():
    # D11/D12: person_1 발끝이 다리 표면에서 8 cm(옛 필터 반경 10 cm 안), 선에서 0.10/0.08 m
    # person_1 toes 8 cm past the leg surface (inside the old 10 cm filter radius), 0.10 / 0.08 m from the line
    tip = max(fx + hx for fx, fy, hx, hy in D.PERSON_SHORT_FEET)
    assert abs(tip - D.PERSON_LEG_R - 0.08) < 1e-9
    assert D.FEET['person_1'] == D.PERSON_SHORT_FEET and 'person_1' in D.PARK
    sc = D.scenarios()
    for name, toe in (('D11', 0.10), ('D12', 0.08)):
        m = sc[name]['motions'][0]
        (x, y), = m.path
        assert m.model == 'person_1' and m.speed == 0.0 and not m.park_at_end
        assert abs((1.01 - (x + tip)) - toe) < 1e-9, name
