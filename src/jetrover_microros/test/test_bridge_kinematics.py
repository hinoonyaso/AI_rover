# 한글: 브리지 기구학이 호스트/펌웨어 수식과 일치하는지 확인하는 단위 시험.
import math

from jetrover_microros.rrc_bridge import mecanum_forward

WHEELBASE, TRACK, DIAMETER = 0.216, 0.195, 0.097


# 한글: 호스트 기준 구현(jetrover_base/src/mecanum.cpp mecanum_inverse)을 그대로 옮긴 참조 함수.
def inverse(vx, vy, wz):
    """Copy of src/jetrover_base/src/mecanum.cpp mecanum_inverse (the host-side reference)."""
    k = wz * (WHEELBASE + TRACK) / 2.0
    to_rps = 1.0 / (math.pi * DIAMETER)
    return [(vx - vy - k) * to_rps, (vx + vy - k) * to_rps, -(vx + vy + k) * to_rps, -(vx - vy + k) * to_rps]


# 한글: 역변환→정변환 왕복이 원래 속도와 일치하는지 확인한다.
def test_round_trip():
    for twist in [(0.1, 0, 0), (0, 0.1, 0), (0, 0, 0.5), (0.12, -0.07, 0.4), (-0.2, 0.2, -1.0)]:
        got = mecanum_forward(inverse(*twist), WHEELBASE, TRACK, DIAMETER)
        for a, b in zip(got, twist):
            assert abs(a - b) < 1e-9


def test_stopped():
    assert mecanum_forward([0, 0, 0, 0], WHEELBASE, TRACK, DIAMETER) == (0.0, 0.0, 0.0)


# 한글: 교차검증용 골든 벡터. jetrover_base/test/test_mecanum.cpp(C++)에 같은 표가 있다(E0).
# 두 구현이 같은 표를 만족하므로 서로 일치한다. 표를 바꾸면 양쪽을 같이 바꾼다.
# Golden vectors shared with the C++ test. Wheel order: ports 1..4, rev/s, right side negated.
GOLDEN = [
    ((0.1, 0.0, 0.0), (0.328154522, 0.328154522, -0.328154522, -0.328154522)),
    ((0.0, 0.1, 0.0), (-0.328154522, 0.328154522, -0.328154522, 0.328154522)),
    ((0.0, 0.0, 0.5), (-0.337178771, -0.337178771, -0.337178771, -0.337178771)),
    ((0.12, -0.07, 0.4), (0.353750575, -0.105665756, -0.433820278, -0.893236608)),
    ((-0.2, 0.2, -1.0), (-0.638260545, 0.674357542, 0.674357542, 1.986975630)),
]


def test_golden_inverse_reference_matches_table():
    for twist, rps in GOLDEN:
        for a, b in zip(inverse(*twist), rps):
            assert abs(a - b) < 1e-8


def test_golden_forward_matches_table():
    for twist, rps in GOLDEN:
        for a, b in zip(mecanum_forward(rps, WHEELBASE, TRACK, DIAMETER), twist):
            assert abs(a - b) < 1e-8
