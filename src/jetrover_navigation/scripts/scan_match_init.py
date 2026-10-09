#!/usr/bin/env python3
# 한글: RViz 2D Pose Estimate 대신 AMCL 초기 위치를 잡는다. 지금 /scan을 /map에 전수 탐색으로 맞춰 가장 잘 맞는
#       (x, y, yaw)를 찾고, 확신이 충분하면(일치도, 2등 후보와의 차이) /initialpose로 보낸다. 로봇은 움직이지 않는다.
#       localization.launch.py가 시작 시 자동 실행(auto_localize:=false로 끔).
#       수동: ros2 run jetrover_navigation scan_match_init.py
"""Brute-force scan-to-map match for the AMCL initial pose (no RViz needed).

Run automatically by localization.launch.py (and so nav2.launch.py), or by hand:
    ros2 run jetrover_navigation scan_match_init.py [--dry-run]

Publishes only when the best pose is confident: it beats the best pose at a different place
(> 0.3 m away) by >= --min-margin with score >= --min-score, or by >= --strong-margin with
score >= --strong-score (a near-perfect match with a decent lead). Otherwise it leaves AMCL
alone and says so -- symmetric/cluttered rooms can match in several poses.
The robot must be standing still while this runs (about 5-10 s).
"""
import argparse
import math
import time

from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import OccupancyGrid
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, qos_profile_sensor_data, QoSProfile
from scipy.ndimage import distance_transform_edt
from sensor_msgs.msg import LaserScan
import tf2_ros

SIGMA = 0.05  # m, hit tolerance / 맞음으로 보는 거리 폭


def quat_yaw(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def spin_until(node, cond, timeout):
    t0 = time.time()
    while not cond() and time.time() - t0 < timeout:
        rclpy.spin_once(node, timeout_sec=0.1)
    return cond()


def match(m, scan, tf, xy_step, yaw_step, near=None, near_radius=0.5):
    """Return refined candidates [(score, x, y, yaw)], best first, at distinct places."""
    # Scan points in base_footprint / 스캔 점을 base_footprint 기준으로
    r = np.array(scan.ranges)
    a = scan.angle_min + np.arange(len(r)) * scan.angle_increment
    ok = np.isfinite(r) & (r > scan.range_min) & (r < scan.range_max)
    r, a = r[ok], a[ok]
    ly = quat_yaw(tf.transform.rotation)
    lx, lyy = tf.transform.translation.x, tf.transform.translation.y
    pts = np.stack([lx + r * np.cos(a + ly), lyy + r * np.sin(a + ly)], 1)[::2]

    res = m.info.resolution
    ox, oy = m.info.origin.position.x, m.info.origin.position.y
    grid = np.array(m.data, dtype=np.int16).reshape(m.info.height, m.info.width)
    dist = distance_transform_edt(grid < 65) * res  # distance to nearest occupied cell
    h, w = grid.shape

    def score(x, y, yaws):
        c, s = np.cos(yaws)[:, None], np.sin(yaws)[:, None]
        wx = x + c * pts[:, 0] - s * pts[:, 1]
        wy = y + s * pts[:, 0] + c * pts[:, 1]
        ix = ((wx - ox) / res).astype(int)
        iy = ((wy - oy) / res).astype(int)
        inside = (ix >= 0) & (ix < w) & (iy >= 0) & (iy < h)
        d = np.full(ix.shape, 1.0)
        d[inside] = dist[iy[inside], ix[inside]]
        return np.exp(-d * d / (2 * SIGMA * SIGMA)).mean(1)

    # Coarse search over known-free cells / 빈 칸에서만 전수 탐색
    stride = max(1, int(round(xy_step / res)))
    fy, fx = np.nonzero(grid[::stride, ::stride] == 0)
    yaws = np.radians(np.arange(-180, 180, yaw_step))
    results = []
    cx_all, cy_all = ox + (fx * stride + 0.5) * res, oy + (fy * stride + 0.5) * res
    if near is not None:  # only search around a known rough pose / 대략 아는 위치 근처만 탐색
        keep = np.hypot(cx_all - near[0], cy_all - near[1]) <= near_radius
        cx_all, cy_all = cx_all[keep], cy_all[keep]
    for x, y in zip(cx_all, cy_all):
        sc = score(x, y, yaws)
        k = int(sc.argmax())
        results.append((sc[k], x, y, yaws[k]))
    results.sort(reverse=True)

    # Refine the top few distinct places / 상위 후보를 촘촘히 다듬기
    refined = []
    for s0, x0, y0, yaw0 in results[:30]:
        if any(math.hypot(x0 - rx, y0 - ry) < 0.3 for _, rx, ry, _ in refined):
            continue
        best = (s0, x0, y0, yaw0)
        fine_yaws = yaw0 + np.radians(np.arange(-4, 4.01, 0.5))
        for dx in np.arange(-0.1, 0.101, 0.025):
            for dy in np.arange(-0.1, 0.101, 0.025):
                sc = score(x0 + dx, y0 + dy, fine_yaws)
                k = int(sc.argmax())
                if sc[k] > best[0]:
                    best = (sc[k], x0 + dx, y0 + dy, fine_yaws[k])
        refined.append(best)
        if len(refined) == 4:
            break
    refined.sort(reverse=True)
    return refined


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--dry-run', action='store_true', help='only print candidates')
    ap.add_argument('--yaw-step', type=float, default=2.0, help='coarse yaw step deg')
    ap.add_argument('--xy-step', type=float, default=0.1, help='coarse xy step m')
    ap.add_argument('--min-score', type=float, default=0.80, help='best score needed to publish')
    ap.add_argument('--min-margin', type=float, default=0.10,
                    help='best minus runner-up (other place) needed to publish')
    # 2026-10-07: 0.974 vs 0.883 (margin 0.091) at one end of the test lane was refused by the
    # first rule alone. 한글: 1등 0.974/2등 0.883이 거부돼서, 거의 완벽한 일치는 차이 0.05로도 허용.
    ap.add_argument('--strong-score', type=float, default=0.95)
    ap.add_argument('--strong-margin', type=float, default=0.05)
    ap.add_argument('--near', type=float, nargs=2, metavar=('X', 'Y'),
                    help='search only within --near-radius of this map point (e.g. where the robot '
                         'was last), when the room alone is ambiguous')
    ap.add_argument('--near-radius', type=float, default=0.5)
    ap.add_argument('--wait', type=float, default=90.0,
                    help='max s to wait for /map, /scan, TF and AMCL')
    args, _ = ap.parse_known_args()  # ignore --ros-args added by launch

    rclpy.init()
    node = Node('scan_match_init')
    log = node.get_logger()
    data = {}
    node.create_subscription(
        OccupancyGrid, '/map', lambda m: data.__setitem__('map', m),
        QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL))
    node.create_subscription(
        LaserScan, '/scan', lambda m: data.__setitem__('scan', m), qos_profile_sensor_data)
    buf = tf2_ros.Buffer()
    tf2_ros.TransformListener(buf, node)
    pub = node.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
    amcl = {}
    node.create_subscription(PoseWithCovarianceStamped, '/amcl_pose',
                             lambda m: amcl.__setitem__('pose', m), 10)
    try:
        if not spin_until(node, lambda: 'map' in data and 'scan' in data, args.wait):
            log.error('no /map or /scan -- not localizing')
            return
        tf = {}

        def have_tf():
            try:
                tf['t'] = buf.lookup_transform(
                    'base_footprint', data['scan'].header.frame_id, rclpy.time.Time())
                return True
            except Exception:  # noqa: BLE001
                return False
        if not spin_until(node, have_tf, args.wait):
            log.error('no TF base_footprint -> scan frame -- not localizing')
            return

        t0 = time.time()
        cands = match(data['map'], data['scan'], tf['t'], args.xy_step, args.yaw_step,
                      args.near, args.near_radius)
        for i, (s, x, y, yaw) in enumerate(cands):
            log.info(f'#{i + 1} score={s:.3f}  x={x:+.3f} y={y:+.3f} '
                     f'yaw={math.degrees(yaw):+.1f}deg')
        best = cands[0]
        margin = best[0] - (cands[1][0] if len(cands) > 1 else 0.0)
        log.info(f'match took {time.time() - t0:.1f} s, score {best[0]:.3f}, margin {margin:.3f}')
        confident = ((best[0] >= args.min_score and margin >= args.min_margin) or
                     (best[0] >= args.strong_score and margin >= args.strong_margin))
        if not confident:
            log.warn(f'NOT confident (need score >= {args.min_score} & margin >= '
                     f'{args.min_margin}, or score >= {args.strong_score} & margin >= '
                     f'{args.strong_margin}) -- AMCL left as is; set the pose in RViz or '
                     'rerun after moving the robot to a less ambiguous spot')
            return
        if args.dry_run:
            return

        # AMCL must be active to receive it / AMCL이 구독(active)할 때까지 대기
        if not spin_until(node, lambda: pub.get_subscription_count() > 0, args.wait):
            log.error('AMCL is not subscribed to /initialpose -- not published')
            return
        _, x, y, yaw = best
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.pose.pose.position.x, msg.pose.pose.position.y = float(x), float(y)
        msg.pose.pose.orientation.z = math.sin(yaw / 2)
        msg.pose.pose.orientation.w = math.cos(yaw / 2)
        cov = [0.0] * 36
        cov[0] = cov[7] = 0.05 ** 2
        cov[35] = math.radians(3) ** 2
        msg.pose.covariance = cov
        amcl.clear()
        pub.publish(msg)
        log.info(f'published /initialpose ({x:.2f}, {y:.2f}, {math.degrees(yaw):.0f}deg)')
        # Check AMCL took it / AMCL이 받아들였는지 확인
        if spin_until(node, lambda: 'pose' in amcl, 5.0):
            p = amcl['pose'].pose.pose
            err = math.hypot(p.position.x - x, p.position.y - y)
            yaw_deg = math.degrees(quat_yaw(p.orientation))
            log.info(f'AMCL now ({p.position.x:.2f}, {p.position.y:.2f}, {yaw_deg:.0f}deg), '
                     f'{err * 100:.1f} cm from match')
        else:
            log.warn('no /amcl_pose within 5 s after publishing')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
