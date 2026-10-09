# 한글: 주행 시험 지표(ROS 없이 계산 — CI 단위시험 대상). straight_trial.py가 쓴다.
"""Pure metrics for tools/nav/straight_trial.py (no ROS imports, tested in CI)."""
import math


def diag_frac(cmds, max_deg=50.0, min_speed=0.03):
    """Fraction of moving commands whose direction is more than max_deg off the body's front.

    cmds: iterable of (vx, vy). Commands slower than min_speed (in-place turns, stops) are skipped.
    Direction = atan2(|vy|, vx), so pure strafing is 90 deg and reversing counts as > 90 deg.
    LateralRatioCritic test pass criterion (prd/mppi-lateral-ratio-critic-test-plan.md): < 5 %
    at max_deg 50 (critic limit 45 deg + margin). Returns nan when nothing moved.
    한글: 움직이는 명령 중 몸 정면에서 max_deg보다 옆으로 꺾인 명령의 비율(순수 옆이동 90°).
    """
    moving = [(vx, vy) for vx, vy in cmds if math.hypot(vx, vy) >= min_speed]
    if not moving:
        return float('nan')
    over = sum(1 for vx, vy in moving if math.degrees(math.atan2(abs(vy), vx)) > max_deg)
    return over / len(moving)
