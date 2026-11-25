#!/usr/bin/env python3
"""Height distribution of the depth obstacle points in base_footprint (read-only, real robot or sim).

Collects /depth_cam/depth/points_sparse for --seconds (the same points the costmap depth layer
receives, including the extrusion behind each face), transforms each frame with TF at its own stamp,
and counts points per height band x forward-distance band. Used to decide whether the costmap depth
min_obstacle_height (0.06 m, troubleshooting/055) can be lowered so a 5 cm object stays in the costmap
(troubleshooting/061): run once on the empty floor (every point is a false positive) and once with
the object placed in front.

  python3 tools/perception/depth_height_survey.py --seconds 20 --label empty_floor [--json out.json]

한글: 깊이 장애물 점(코스트맵이 받는 것과 같은 점)의 높이 분포를 높이 × 앞쪽 거리 구간별로 센다(읽기 전용).
빈 바닥(나온 점은 모두 오검출)과 5 cm 물체를 둔 상태를 비교해 깊이 최소 높이를 낮출 수 있는지 판단한다.
"""
import argparse
import json
import sys
import time

import numpy as np

HEIGHTS = (-1.0, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.12, 9.0)
RANGES = (0.0, 0.5, 0.7, 0.9, 1.2, 9.0)


def quat_to_rot(q):
    x, y, z, w = q.x, q.y, q.z, q.w
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def histogram(points):
    """Counts per (height band, forward band) for base_footprint points. / 높이×거리 구간별 점 수."""
    counts, _, _ = np.histogram2d(points[:, 2], points[:, 0], bins=(HEIGHTS, RANGES))
    return counts.astype(int)


def band(edges, i):
    lo, hi = edges[i], edges[i + 1]
    return f'<{hi:.2f}' if lo < -0.5 else (f'>={lo:.2f}' if hi > 5 else f'{lo:.2f}-{hi:.2f}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--seconds', type=float, default=20.0)
    ap.add_argument('--label', default='survey')
    ap.add_argument('--json', default=None, help='write counts and per-frame maxima to this file')
    args = ap.parse_args()

    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import PointCloud2
    from sensor_msgs_py import point_cloud2
    import tf2_ros

    rclpy.init()
    node = Node('depth_height_survey')
    clouds = []
    node.create_subscription(PointCloud2, '/depth_cam/depth/points_sparse', clouds.append, 10)
    buf = tf2_ros.Buffer()
    tf2_ros.TransformListener(buf, node)
    end = time.time() + args.seconds
    while time.time() < end:
        rclpy.spin_once(node, timeout_sec=0.05)
    # Let TF catch up with the last frames. / 마지막 프레임의 TF가 도착하도록 잠시 더 받는다.
    settle = time.time() + 1.0
    while time.time() < settle:
        rclpy.spin_once(node, timeout_sec=0.05)
    if not clouds:
        print('no /depth_cam/depth/points_sparse (home-pose gate closed or camera off)')
        return 1
    total = np.zeros((len(HEIGHTS) - 1, len(RANGES) - 1), dtype=int)
    frame_low_max = []   # per frame: highest point below 0.12 m within 1.2 m ahead / 프레임별 낮은 점 최고 높이
    used = skipped = 0
    for msg in clouds:
        try:
            tf = buf.lookup_transform('base_footprint', msg.header.frame_id, rclpy.time.Time.from_msg(msg.header.stamp))
        except Exception:  # noqa: BLE001 - frames without TF are skipped and counted
            skipped += 1
            continue
        raw = np.array([[p[0], p[1], p[2]] for p in point_cloud2.read_points(msg, ('x', 'y', 'z'), skip_nans=True)],
                       dtype=float).reshape(-1, 3)
        used += 1
        if not len(raw):
            frame_low_max.append(None)
            continue
        t = tf.transform.translation
        pts = raw @ quat_to_rot(tf.transform.rotation).T + np.array([t.x, t.y, t.z])
        total += histogram(pts)
        low = pts[(pts[:, 2] < 0.12) & (pts[:, 0] < 1.2)]
        frame_low_max.append(float(low[:, 2].max()) if len(low) else None)
    print(f'[{args.label}] frames {len(clouds)} used {used} skipped(no TF) {skipped}')
    header = 'height \\ ahead ' + ''.join(f'{band(RANGES, j):>11s}' for j in range(len(RANGES) - 1))
    print(header)
    for i in range(len(HEIGHTS) - 1):
        print(f'{band(HEIGHTS, i):>14s} ' + ''.join(f'{total[i, j]:11d}' for j in range(len(RANGES) - 1)))
    maxima = [m for m in frame_low_max if m is not None]
    if maxima:
        print(f'per-frame max height of points <0.12 m within 1.2 m: median {np.median(maxima):.3f}, '
              f'p95 {np.percentile(maxima, 95):.3f}, max {max(maxima):.3f} m ({len(maxima)}/{used} frames had such points)')
    else:
        print(f'no points below 0.12 m within 1.2 m in {used} frames')
    if args.json:
        with open(args.json, 'w') as f:
            json.dump({'label': args.label, 'heights': HEIGHTS, 'ranges': RANGES, 'counts': total.tolist(),
                       'frame_low_max': frame_low_max, 'frames': len(clouds), 'used': used, 'skipped': skipped}, f)
    node.destroy_node()
    rclpy.try_shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())
