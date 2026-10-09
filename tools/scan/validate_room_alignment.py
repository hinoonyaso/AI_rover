#!/usr/bin/env python3
# 한글: 스캔 메쉬(또는 점군)의 LiDAR 높이 단면을 SLAM 지도와 2D ICP로 맞춰
#       T_map<-scan과 잔차를 구한다(host, Open3D 필요).
"""
Align a scanned room mesh / point cloud to the SLAM map (prd/gazebo-sim.md). Host only.

Usage:
  python3 tools/scan/validate_room_alignment.py room.ply maps/lap2_20261005.yaml \
      [--z 0.15 0.25] [--init X Y YAW_DEG] [--apply room_in_map.ply]
Slices the mesh at the LiDAR height band (--z, scan frame must be z-up with the floor at z=0),
runs point-to-line ICP against the occupied map cells and prints T_map<-scan (x, y, yaw) and the
residual median / 90th percentile. --apply writes the transformed mesh (rotation about z only).
Pass: median residual <= 0.05 m (PRD target). Needs open3d (pip install open3d).
"""
import argparse
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from align2d import icp2d, occupied_points  # noqa: E402


def load_points(path, n=400000):
    import open3d as o3d
    mesh = o3d.io.read_triangle_mesh(path)
    if len(mesh.triangles) > 0:
        return np.asarray(mesh.sample_points_uniformly(n).points), mesh
    pcd = o3d.io.read_point_cloud(path)
    return np.asarray(pcd.points), None


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('scan')
    ap.add_argument('map_yaml')
    ap.add_argument('--z', type=float, nargs=2, default=(0.15, 0.25))
    ap.add_argument('--init', type=float, nargs=3, default=(0.0, 0.0, 0.0),
                    metavar=('X', 'Y', 'YAW_DEG'))
    ap.add_argument('--max-dist', type=float, default=0.3)
    ap.add_argument('--apply', default=None, help='write the aligned mesh/cloud here')
    args = ap.parse_args()

    pts, mesh = load_points(args.scan)
    band = pts[(pts[:, 2] >= args.z[0]) & (pts[:, 2] <= args.z[1])][:, :2]
    if len(band) < 50:
        raise SystemExit(f'only {len(band)} points in z {args.z}: '
                         'is the scan z-up with the floor at 0?')
    # thin to ~1 cm grid / 1 cm 격자로 솎기
    band = np.unique(np.round(band / 0.01) * 0.01, axis=0)
    dst = occupied_points(args.map_yaml)
    (x, y, yaw), res = icp2d(band, dst, init=(args.init[0], args.init[1],
                                              math.radians(args.init[2])),
                             max_dist=args.max_dist)
    inl = res < args.max_dist
    print(f'T_map<-scan: x={x:+.3f} m  y={y:+.3f} m  yaw={math.degrees(yaw):+.2f} deg')
    print(f'slice points {len(band)}, inliers {inl.mean() * 100:.0f}%, residual median '
          f'{np.median(res[inl]) * 100:.1f} cm, p90 {np.percentile(res[inl], 90) * 100:.1f} cm')
    ok = np.median(res[inl]) <= 0.05
    print('PASS' if ok else 'FAIL (median > 5 cm): try --init or check scale/up axis')
    if args.apply:
        import open3d as o3d
        tf = np.eye(4)
        tf[:2, :2] = [[math.cos(yaw), -math.sin(yaw)], [math.sin(yaw), math.cos(yaw)]]
        tf[0, 3], tf[1, 3] = x, y
        if mesh is not None:
            o3d.io.write_triangle_mesh(args.apply, mesh.transform(tf))
        else:
            pcd = o3d.io.read_point_cloud(args.scan).transform(tf)
            o3d.io.write_point_cloud(args.apply, pcd)
        print(f'wrote {args.apply}')


if __name__ == '__main__':
    main()
