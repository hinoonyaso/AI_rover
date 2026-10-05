# 한글: 브리지 기구학이 호스트/펌웨어 수식과 일치하는지 확인하는 단위 시험.
import math

from jetrover_microros.rrc_bridge import mecanum_forward

WHEELBASE, TRACK, DIAMETER = 0.216, 0.195, 0.097


# 한글: 호스트 기준 구현(base_node.cpp mecanum_rps)을 그대로 옮긴 참조 함수.
def inverse(vx, vy, wz):
    """Copy of src/jetrover_base/src/base_node.cpp mecanum_rps (the host-side reference)."""
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
