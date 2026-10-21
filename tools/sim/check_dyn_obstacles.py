#!/usr/bin/env python3
# 한글: 동적 장애물 시뮬레이션 확인(체크리스트 8.16 1.3, host, Nav2 실행 중). 로봇을 A에 세워 두고 사람(D1)과 낮은 상자(D3)를 지나가게 해서
#       ① 실제 속도(정답) ② 사람 다리가 /scan에 찍히는 비율 ③ 상자가 깊이 장애물 점에 찍히는 비율 ④ 지나간 뒤 local 코스트맵 흔적이 지워지는 시간을 잰다.
#       실행: RUNCMD="python3 tools/sim/check_dyn_obstacles.py" bash tools/sim/sim_avoid_run.sh
"""Check the dynamic-obstacle simulation with the robot standing at A (host, ROS_DOMAIN_ID=31, Nav2 + set_pose bridge running).

For D1 (person, 0.5 m/s) and D3 (low box, 0.3 m/s) crossing 0.7 m in front of the robot:
  speed     ground-truth speed of the model while it moves (target within 10 % of the commanded speed)
  scan      fraction of /scan messages with a return within 0.12 m of a leg while the person is inside the camera/LiDAR view
  depth     fraction of depth-obstacle clouds with a point on the box (+3 cm) while the box is inside the camera view
  clear     seconds until no lethal cell within 0.10 m of the in-view part of the obstacle path is left that was not lethal before
            (target <= 2 s; cells near walls flicker with LiDAR noise and are ignored)
"""
import math
import os
import sys
import time

from nav_msgs.msg import OccupancyGrid
import numpy as np
import rclpy
from sensor_msgs.msg import LaserScan, PointCloud2
from sensor_msgs_py import point_cloud2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import avoid_trials as T  # noqa: E402
import dyn_obstacles as DYN  # noqa: E402

CAM_HALF_FOV = math.radians(41.0)    # depth camera half horizontal FOV (1.4464 rad / 2)


def tf2d(node, target, source, stamp=None):
    """(c, s, tx, ty) mapping source-frame points into target, or None."""
    try:
        tr = node.buf.lookup_transform(target, source, stamp or rclpy.time.Time())
    except Exception:  # noqa: BLE001
        return None
    q = tr.transform.rotation
    yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
    return math.cos(yaw), math.sin(yaw), tr.transform.translation.x, tr.transform.translation.y


def apply(tf, xs, ys):
    c, s, tx, ty = tf
    return c * xs - s * ys + tx, s * xs + c * ys + ty


def tf3d(node, target, source, stamp=None):
    """(R 3x3, t 3) mapping source-frame points into target, or None. Needed for the optical frame (z forward, y down)."""
    try:
        tr = node.buf.lookup_transform(target, source, stamp or rclpy.time.Time())
    except Exception:  # noqa: BLE001
        return None
    q = tr.transform.rotation
    x, y, z, w = q.x, q.y, q.z, q.w
    rot = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                    [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                    [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    tt = tr.transform.translation
    return rot, np.array([tt.x, tt.y, tt.z])


def in_view(robot, p, max_range=2.5):
    """Point p within the depth camera's horizontal FOV and range from the robot pose (x, y, yaw)."""
    dx, dy = p[0] - robot[0], p[1] - robot[1]
    ang = math.atan2(dy, dx) - robot[2]
    ang = math.atan2(math.sin(ang), math.cos(ang))
    return abs(ang) < CAM_HALF_FOV and 0.25 < math.hypot(dx, dy) < max_range


def lethal_cells(grid):
    """Set of (ix, iy) with value 100 and the grid info."""
    g = np.array(grid.data, dtype=np.int16).reshape(grid.info.height, grid.info.width)
    iy, ix = np.nonzero(g >= 100)
    return set(zip(ix.tolist(), iy.tolist())), grid.info


def view_samples(path, robot, step=0.02):
    """Points every `step` m along the path that are inside the camera view from robot (x, y, yaw)."""
    out, d, total = [], 0.0, DYN.path_length(path)
    while d <= total:
        p, _ = DYN.point_along(path, d)
        if in_view(robot, p):
            out.append(p)
        d += step
    return out


def near_path_residue(node, grid, base, path, radius=0.15):
    """Lethal cells of `grid` not in `base` within `radius` of the path sample points (map frame).

    한글: 장애물이 지나간 경로 주변만 본다. 벽 근처는 LiDAR 잡음으로 칸이 늘 바뀌어서 흔적으로 세면 안 된다.
    Only around the obstacle path: wall cells flicker with LiDAR noise and are not residue.
    """
    cells, info = lethal_cells(grid)
    tf = tf2d(node, 'map', grid.header.frame_id)
    if tf is None:
        return None
    n = 0
    for ix, iy in cells - base:
        x, y = apply(tf, info.origin.position.x + (ix + 0.5) * info.resolution,
                     info.origin.position.y + (iy + 0.5) * info.resolution)
        if any(math.hypot(x - px, y - py) < radius for px, py in path):
            n += 1
    return n


def run_case(node, gt, drv, name, motion):
    """Drive one motion past the standing robot and measure. Returns a dict of results."""
    scans, clouds, costmaps = [], [], []
    subs = [node.create_subscription(LaserScan, '/scan', lambda m: scans.append(m), 10),
            node.create_subscription(PointCloud2, '/depth_cam/depth/points_sparse', lambda m: clouds.append(m), 10),
            node.create_subscription(OccupancyGrid, '/local_costmap/costmap', lambda m: costmaps.append(m), 5)]
    T.setup_leg(node, gt, 'D1', (*DYN.A, 83.0), DYN.OBJECT_0_PARK)
    drv.park_all()
    node.spin(3.0)
    base = lethal_cells(costmaps[-1])[0] if costmaps else set()
    scans.clear()
    clouds.clear()
    gt.rows.clear()
    gt.recording = True
    t0 = node.now()
    drv.begin([motion], DYN.A, DYN.B, t0)
    duration = DYN.path_length(motion.path) / motion.speed + 1.0
    while node.now() - t0 < duration:
        rclpy.spin_once(node, timeout_sec=0.02)
    drv.end()                                   # parks the model / 모델을 방 밖으로
    t_park = node.now()
    clear_s, residue_at_park = None, None
    r0 = gt.latest
    samples = view_samples(motion.path, (r0[1], r0[2], r0[3])) if r0 else []
    while node.now() - t_park < 6.0:
        rclpy.spin_once(node, timeout_sec=0.02)
        if costmaps and clear_s is None:
            res = near_path_residue(node, costmaps[-1], base, samples, radius=0.10)
            if residue_at_park is None:
                residue_at_park = res
            if res == 0:
                clear_s = node.now() - t_park
    gt.recording = False
    for s in subs:
        node.destroy_subscription(s)

    rows = np.array(gt.rows)
    col = 7 if motion.model == 'person_0' else 10       # x column of the model in the GroundTruth row
    mt, mx, my = rows[:, 0], rows[:, col], rows[:, col + 1]
    robot = (rows[0, 1], rows[0, 2], rows[0, 3])
    inside = (mx < 7.0)                                 # not parked / 방 안에 있을 때
    moving_t, moving_x, moving_y = mt[inside], mx[inside], my[inside]
    speed = float('nan')
    if len(moving_t) > 10:
        d = np.hypot(np.diff(moving_x), np.diff(moving_y))
        dt = np.diff(moving_t)
        ok = dt > 0
        speed = float(d[ok].sum() / dt[ok].sum())

    def model_at(t):
        i = int(np.clip(np.searchsorted(mt, t), 0, len(mt) - 1))
        return mx[i], my[i], rows[i, col + 2]

    seen = total = 0
    if motion.model == 'person_0':
        for m in scans:
            t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
            px, py, pyaw = model_at(t)
            if px > 7.0 or not in_view(robot, (px, py)):
                continue
            tf = tf2d(node, 'map', m.header.frame_id, rclpy.time.Time.from_msg(m.header.stamp))
            if tf is None:
                continue
            a = m.angle_min + np.arange(len(m.ranges)) * m.angle_increment
            r = np.array(m.ranges)
            ok = np.isfinite(r)
            wx, wy = apply(tf, r[ok] * np.cos(a[ok]), r[ok] * np.sin(a[ok]))
            legs = [(px + math.cos(pyaw) * lx - math.sin(pyaw) * ly, py + math.sin(pyaw) * lx + math.cos(pyaw) * ly)
                    for lx, ly in DYN.PERSON_LEGS]
            hit = any(np.any(np.hypot(wx - lx, wy - ly) < DYN.PERSON_LEG_R + 0.06) for lx, ly in legs)
            total += 1
            seen += int(hit)
    else:
        hx, hy = DYN.DYN_BOX_SIZE[0] / 2 + 0.03, DYN.DYN_BOX_SIZE[1] / 2 + 0.03
        for m in clouds:
            t = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
            bx, by, byaw = model_at(t)
            if bx > 7.0 or not in_view(robot, (bx, by)):
                continue
            tf = tf3d(node, 'map', m.header.frame_id, rclpy.time.Time.from_msg(m.header.stamp))
            if tf is None:
                continue
            pts = np.array([(p[0], p[1], p[2]) for p in point_cloud2.read_points(m, field_names=('x', 'y', 'z'), skip_nans=True)])
            total += 1
            if len(pts) == 0:
                continue
            w = pts @ tf[0].T + tf[1]
            wx, wy = w[:, 0], w[:, 1]
            c, s = math.cos(-byaw), math.sin(-byaw)
            lx, ly = c * (wx - bx) - s * (wy - by), s * (wx - bx) + c * (wy - by)
            seen += int(np.any((np.abs(lx) < hx) & (np.abs(ly) < hy)))
    return {'case': name, 'cmd_speed': motion.speed, 'gt_speed': speed,
            'speed_err_pct': abs(speed - motion.speed) / motion.speed * 100 if speed == speed else float('nan'),
            'detected': f'{seen}/{total}', 'clear_s': clear_s, 'residue_at_park': residue_at_park}


def main():
    if os.environ.get('ROS_DOMAIN_ID') != '31':
        sys.exit('export ROS_DOMAIN_ID=31 first')
    rclpy.init()
    node, gt = T.Runner(), T.GroundTruth()
    drv = DYN.ObstacleDriver(node, T.WORLD, lambda: gt.latest[1:3] if gt.latest else None)
    try:
        if not drv.ready():
            sys.exit('set_pose bridge not available')
        node.spin(3.0)
        sc = DYN.scenarios()
        for name in ('D1', 'D3'):
            r = run_case(node, gt, drv, name, sc[name]['motions'][0])
            print(f"{r['case']}: speed {r['gt_speed']:.3f} m/s (cmd {r['cmd_speed']}, err {r['speed_err_pct']:.1f} %)  "
                  f"detected {r['detected']}  path cells marked at park {r['residue_at_park']}, cleared after: "
                  f"{'%.1f s' % r['clear_s'] if r['clear_s'] is not None else 'NOT within 6 s'}", flush=True)
            time.sleep(0.5)
    finally:
        drv.end()
        gt.stop()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
