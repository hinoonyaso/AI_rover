#!/usr/bin/env python3
# 한글: Gazebo 월드의 실제 점유 지도를 LiDAR로 만든다(host). 로봇을 격자 위 여러 자리·방향에 놓고 /scan을 받아 정답 자세로
#       월드(=map) 좌표의 점을 모은다. 정적 지도(실기 방)와 스캔한 방 메쉬가 다를 수 있어서, 시나리오 위치가 시뮬레이션에서
#       실제로 비어 있는지 확인하는 용도. 결과 Log/sim_avoid/world_scan.npy/.png (5 cm 칸, 칸당 LiDAR 반환 수).
"""LiDAR occupancy of the simulated room from ground-truth poses (host, ROS_DOMAIN_ID=31, sim running; Nav2 not needed).

  python3 tools/sim/world_scan_map.py [--x 0.3 1.8 0.25] [--y 0.3 1.9 0.25]
Writes Log/sim_avoid/world_scan.png: occupied cells (>= 2 returns) black, free grey, with 1 m grid labels and the
scenario points (A, B, box) marked. Box and cubes are moved under the floor first.
"""
import argparse
import math
import os
import sys

import cv2
import numpy as np
import rclpy
from sensor_msgs.msg import LaserScan
import tf2_ros

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import avoid_trials as T  # noqa: E402

RES = 0.05
X0, X1, Y0, Y1 = -0.5, 2.5, -0.2, 2.6


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--x', type=float, nargs=3, default=[0.3, 1.8, 0.25])
    ap.add_argument('--y', type=float, nargs=3, default=[0.3, 1.9, 0.25])
    args = ap.parse_args()
    rclpy.init()
    node, gt = T.Runner(), T.GroundTruth()
    scans = []
    node.create_subscription(LaserScan, '/scan', lambda m: scans.append(m), 5)
    nx, ny = int((X1 - X0) / RES), int((Y1 - Y0) / RES)
    hits = np.zeros((ny, nx), np.int32)
    seen = np.zeros((ny, nx), np.int32)
    try:
        node.spin(3.0)
        for c in T.CUBES + (T.BOX,):
            T.gz_set_pose(c, 0.45, 1.35, -3.0)
        for x in np.arange(args.x[0], args.x[1] + 1e-9, args.x[2]):
            for y in np.arange(args.y[0], args.y[1] + 1e-9, args.y[2]):
                for yaw in (0.0, 180.0):
                    T.gz_set_pose('jetrover', x, y, 0.01, yaw)
                    node.spin(1.5)
                    scans.clear()
                    node.spin(1.0)
                    g = gt.latest
                    if not scans or g is None:
                        continue
                    m = scans[-1]
                    try:
                        tr = node.buf.lookup_transform('base_footprint', m.header.frame_id, rclpy.time.Time())
                    except Exception:  # noqa: BLE001
                        continue
                    q, t = tr.transform.rotation, tr.transform.translation
                    ly = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
                    ang = m.angle_min + np.arange(len(m.ranges)) * m.angle_increment
                    r = np.array(m.ranges)
                    ok = np.isfinite(r) & (r > m.range_min) & (r < m.range_max - 0.05)
                    bx = t.x + r[ok] * np.cos(ang[ok] + ly)
                    by = t.y + r[ok] * np.sin(ang[ok] + ly)
                    wx = g[1] + math.cos(g[3]) * bx - math.sin(g[3]) * by
                    wy = g[2] + math.sin(g[3]) * bx + math.cos(g[3]) * by
                    ix, iy = ((wx - X0) / RES).astype(int), ((wy - Y0) / RES).astype(int)
                    good = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
                    np.add.at(hits, (iy[good], ix[good]), 1)
                    # free cells along the rays (coarse): sample every 5 cm
                    for k in np.arange(0.1, 3.0, RES):
                        sel = ok & (r > k)
                        fx = g[1] + math.cos(g[3]) * (t.x + k * np.cos(ang[sel] + ly)) - math.sin(g[3]) * (t.y + k * np.sin(ang[sel] + ly))
                        fy = g[2] + math.sin(g[3]) * (t.x + k * np.cos(ang[sel] + ly)) + math.cos(g[3]) * (t.y + k * np.sin(ang[sel] + ly))
                        jx, jy = ((fx - X0) / RES).astype(int), ((fy - Y0) / RES).astype(int)
                        gg = (jx >= 0) & (jx < nx) & (jy >= 0) & (jy < ny)
                        np.add.at(seen, (jy[gg], jx[gg]), 1)
        np.save(os.path.join(T.JSON_DIR, 'world_scan_hits.npy'), hits)
        scale = 10
        img = np.full((ny * scale, nx * scale, 3), 255, np.uint8)
        for j in range(ny):
            for i in range(nx):
                col = (0, 0, 0) if hits[j, i] >= 2 else ((225, 225, 225) if seen[j, i] > 0 else (255, 255, 255))
                img[(ny - 1 - j) * scale:(ny - j) * scale, i * scale:(i + 1) * scale] = col

        def px(x, y):
            return int((x - X0) / RES * scale), int((ny - (y - Y0) / RES) * scale)
        for gx in np.arange(math.ceil(X0), X1 + 1e-9, 0.5):
            cv2.line(img, px(gx, Y0), px(gx, Y1), (0, 0, 255) if gx % 1 == 0 else (200, 200, 255), 1)
            cv2.putText(img, f'{gx:.1f}', (px(gx, Y0)[0] + 2, img.shape[0] - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 200), 1)
        for gy in np.arange(math.ceil(Y0), Y1 + 1e-9, 0.5):
            cv2.line(img, px(X0, gy), px(X1, gy), (0, 0, 255) if gy % 1 == 0 else (200, 200, 255), 1)
            cv2.putText(img, f'{gy:.1f}', (2, px(X0, gy)[1] - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 200), 1)
        for name, (x, y) in (('A', T.A), ('B', T.B), ('box S2', T.SCENARIOS['S2']['box']), ('box S4', T.SCENARIOS['S4']['box'])):
            cv2.drawMarker(img, px(x, y), (0, 160, 0), cv2.MARKER_CROSS, 16, 2)
            cv2.putText(img, name, (px(x, y)[0] + 6, px(x, y)[1] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 130, 0), 1)
        path = os.path.join(T.JSON_DIR, 'world_scan.png')
        os.makedirs(T.JSON_DIR, exist_ok=True)
        cv2.imwrite(path, img)
        print('wrote', path, f'({nx}x{ny} cells, {int((hits >= 2).sum())} occupied)', flush=True)
    finally:
        gt.stop()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
