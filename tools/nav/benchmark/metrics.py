# 한글: Nav2 baseline 지표 계산(순수 파이썬, ROS/numpy 불필요 -> 어디서나 단위시험 가능).
"""Pure-python metric functions for the Nav2 baseline benchmark (no ROS / numpy needed)."""
import math
import statistics


def yaw_from_quat(z, w):
    """Yaw of a planar quaternion (x=y=0)."""
    return 2.0 * math.atan2(z, w)


def compose2d(a, b):
    """Planar transform composition a*b; a, b = (x, y, yaw) e.g. map->odom * odom->base."""
    ax, ay, ath = a
    bx, by, bth = b
    c, s = math.cos(ath), math.sin(ath)
    return (ax + c * bx - s * by, ay + s * bx + c * by, angle_diff(ath + bth, 0.0))


def angle_diff(a, b):
    """Smallest signed difference a-b in (-pi, pi]."""
    d = (a - b + math.pi) % (2.0 * math.pi) - math.pi
    return math.pi if d == -math.pi else d


def point_to_segment(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    seg2 = dx * dx + dy * dy
    if seg2 == 0.0:
        return math.hypot(p[0] - ax, p[1] - ay)
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / seg2))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def cross_track_errors(plan_xy, poses_xy):
    """Distance of every pose to the planned polyline [m]."""
    if len(plan_xy) < 2:
        return []
    return [min(point_to_segment(p, plan_xy[i], plan_xy[i + 1]) for i in range(len(plan_xy) - 1))
            for p in poses_xy]


def rms(values):
    return math.sqrt(sum(v * v for v in values) / len(values)) if values else float('nan')


def path_length(xy):
    return sum(math.hypot(xy[i + 1][0] - xy[i][0], xy[i + 1][1] - xy[i][1])
               for i in range(len(xy) - 1))


def goal_errors(final_xy, final_yaw, goal_xy, goal_yaw):
    """(position error [m], |yaw error| [rad])."""
    return (math.hypot(final_xy[0] - goal_xy[0], final_xy[1] - goal_xy[1]),
            abs(angle_diff(final_yaw, goal_yaw)))


def moving_interval(stamps, speeds, threshold=0.01):
    """(t_start, t_end) of the first/last sample with |speed| > threshold, or None."""
    idx = [i for i, s in enumerate(speeds) if abs(s) > threshold]
    return (stamps[idx[0]], stamps[idx[-1]]) if idx else None


def summarize(trials):
    """Aggregate per-trial dicts. Keys: success(bool), collision(bool), pos_err_cm, yaw_err_deg,
    cte_rms_cm, time_s, recoveries. Missing/None values are skipped."""
    def vals(key):
        return [t[key] for t in trials if t.get(key) is not None]

    def stat(key):
        v = vals(key)
        if not v:
            return None
        return {'mean': statistics.fmean(v), 'median': statistics.median(v),
                'std': statistics.pstdev(v) if len(v) > 1 else 0.0, 'max': max(v), 'n': len(v)}

    n = len(trials)
    return {
        'n': n,
        'success_rate': sum(1 for t in trials if t.get('success')) / n if n else None,
        'collision_rate': sum(1 for t in trials if t.get('collision')) / n if n else None,
        'pos_err_cm': stat('pos_err_cm'),
        'yaw_err_deg': stat('yaw_err_deg'),
        'cte_rms_cm': stat('cte_rms_cm'),
        'time_s': stat('time_s'),
        'recoveries': stat('recoveries'),
    }
