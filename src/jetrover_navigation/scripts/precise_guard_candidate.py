#!/usr/bin/env python3
"""
Offline swept-disc costmap experiment; this does not control a robot.

한글: 이동 경로를 보수적인 원의 궤적으로 검사하는 오프라인 실험이며 로봇을 제어하지 않는다.
"""
import math


def path_clear(data, width, height, resolution, origin, start, end, radius, blocked_at=100):
    """
    Check a swept disc against an axis-aligned OccupancyGrid, failing closed.

    한글: 축 정렬 OccupancyGrid에서 이동하는 원을 검사하고 유효하지 않으면 차단한다.
    Unknown cells (-1), outside-map regions and invalid checked cells are blocked. A cell is
    conservatively treated as a circumscribed disc, including its boundary and corners.
    한글: 미지 셀·지도 밖·잘못된 입력은 차단하며 셀의 외접원으로 모서리도 포함한다.
    This experiment makes no claim about freshness, sensing, footprint selection or stopping.
    """
    try:
        if (not isinstance(width, int) or isinstance(width, bool) or width <= 0 or
                not isinstance(height, int) or isinstance(height, bool) or height <= 0 or
                len(data) != width * height or len(origin) != 2 or len(start) != 2 or
                len(end) != 2 or not isinstance(blocked_at, int) or not 1 <= blocked_at <= 100):
            return False
        vals = (resolution, radius, *origin, *start, *end)
        if not all(math.isfinite(v) for v in vals) or resolution <= 0 or radius <= 0:
            return False
        ox, oy = origin
        ax, ay = start
        bx, by = end
        # Reject outside-map coverage, even if the centreline remains inside.
        # 한글: 중심선이 지도 안에 있어도 원이 경계를 벗어나면 차단한다.
        if (min(ax, bx) - radius < ox or min(ay, by) - radius < oy or
                max(ax, bx) + radius > ox + width * resolution or
                max(ay, by) + radius > oy + height * resolution):
            return False
        padding = radius + resolution / math.sqrt(2.0)
        x0 = max(0, math.floor((min(ax, bx) - padding - ox) / resolution))
        x1 = min(width - 1, math.floor((max(ax, bx) + padding - ox) / resolution))
        y0 = max(0, math.floor((min(ay, by) - padding - oy) / resolution))
        y1 = min(height - 1, math.floor((max(ay, by) + padding - oy) / resolution))
        dx, dy = bx - ax, by - ay
        length_sq = dx * dx + dy * dy
        for iy in range(y0, y1 + 1):
            cy = oy + (iy + 0.5) * resolution
            for ix in range(x0, x1 + 1):
                value = data[iy * width + ix]
                if not isinstance(value, int) or value < -1 or value > 100:
                    return False
                if value != -1 and value < blocked_at:
                    continue
                cx = ox + (ix + 0.5) * resolution
                t = 0.0
                if length_sq:
                    t = max(0.0, min(1.0, ((cx - ax) * dx + (cy - ay) * dy) / length_sq))
                if math.hypot(cx - (ax + t * dx), cy - (ay + t * dy)) <= padding:
                    return False
        return True
    except (TypeError, ValueError, OverflowError, IndexError):
        return False
