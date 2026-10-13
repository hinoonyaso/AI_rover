#!/usr/bin/env python3
# 한글: (host, uv venv) rtabmap-export 결과(노드별 RGB/depth + 최적화된 카메라 포즈)를 Open3D TSDF로 합쳐 방 메쉬를 만든다.
#       결과 좌표: RTAB-Map map 프레임(z-up, base_footprint 바닥 = z 0, 미터). 지도 정합은 validate_room_alignment.py가 한다.
"""Fuse an rtabmap-export directory into a TSDF mesh (host only, needs open3d).

Usage:
  rtabmap-export --images_id --poses_camera --output_dir <exp> rtabmap.db
  python3 tools/scan/tsdf_from_rtabmap.py <exp> room.ply [--voxel 0.01] [--trunc 0.04] [--max-depth 3.0]
<exp> must hold rtabmap_camera_poses.txt (#timestamp x y z qx qy qz qw id, optical frame),
rtabmap_rgb/<id>.jpg, rtabmap_depth/<id>.png (uint16 mm) and rtabmap_calib/<id>.yaml.
"""
import argparse
import os
import re

import numpy as np


def read_poses(path):
    poses = []
    for line in open(path):
        if line.startswith('#') or not line.strip():
            continue
        t, x, y, z, qx, qy, qz, qw, i = line.split()[:9]
        poses.append((int(i), np.array([float(v) for v in (x, y, z, qx, qy, qz, qw)])))
    return poses


def pose_matrix(p):
    x, y, z, qx, qy, qz, qw = p
    r = np.array([
        [1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
        [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
        [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)]])
    m = np.eye(4)
    m[:3, :3] = r
    m[:3, 3] = (x, y, z)
    return m


def read_k(path):
    # OpenCV YAML(%YAML:1.0)은 pyyaml로 못 읽으므로 camera_matrix data만 정규식으로 뽑는다.
    # OpenCV-style YAML is not plain YAML: pull camera_matrix data with a regex.
    txt = open(path).read()
    block = re.search(r'camera_matrix:.*?data:\s*\[(.*?)\]', txt, re.S).group(1)
    k = [float(v) for v in block.replace('\n', ' ').split(',')]
    w = int(re.search(r'image_width:\s*(\d+)', txt).group(1))
    h = int(re.search(r'image_height:\s*(\d+)', txt).group(1))
    return w, h, k[0], k[4], k[2], k[5]


def main():
    import open3d as o3d
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('export_dir')
    ap.add_argument('out_ply')
    ap.add_argument('--voxel', type=float, default=0.01)
    ap.add_argument('--trunc', type=float, default=0.04)
    ap.add_argument('--max-depth', type=float, default=3.0,
                    help='ignore depth beyond this (m); far depth is noisy')
    # 스캔 자세에서 그리퍼/팔이 화면 아래에 걸리면 제자리 회전 때 별 모양 허상이 생긴다(2026-10-14 room1) — 가까운 depth 제거.
    # The gripper/arm in view leaves a star-shaped ghost around in-place rotations: drop near depth.
    ap.add_argument('--min-depth', type=float, default=0.25, help='ignore depth closer than this (m)')
    args = ap.parse_args()

    e = args.export_dir
    poses = read_poses(os.path.join(e, 'rtabmap_camera_poses.txt'))
    vol = o3d.pipelines.integration.ScalableTSDFVolume(
        voxel_length=args.voxel, sdf_trunc=args.trunc,
        color_type=o3d.pipelines.integration.TSDFVolumeColorType.RGB8)
    used = skipped = 0
    for i, p in poses:
        rgb = os.path.join(e, 'rtabmap_rgb', f'{i}.jpg')
        dep = os.path.join(e, 'rtabmap_depth', f'{i}.png')
        cal = os.path.join(e, 'rtabmap_calib', f'{i}.yaml')
        if not (os.path.exists(rgb) and os.path.exists(dep) and os.path.exists(cal)):
            skipped += 1
            continue
        w, h, fx, fy, cx, cy = read_k(cal)
        intr = o3d.camera.PinholeCameraIntrinsic(w, h, fx, fy, cx, cy)
        d = np.asarray(o3d.io.read_image(dep)).copy()
        d[d < args.min_depth * 1000.0] = 0
        rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
            o3d.io.read_image(rgb), o3d.geometry.Image(d), depth_scale=1000.0,
            depth_trunc=args.max_depth, convert_rgb_to_intensity=False)
        # integrate()는 extrinsic = world->camera를 받는다 / Open3D wants world->camera.
        vol.integrate(rgbd, intr, np.linalg.inv(pose_matrix(p)))
        used += 1
    mesh = vol.extract_triangle_mesh()
    mesh.compute_vertex_normals()
    o3d.io.write_triangle_mesh(args.out_ply, mesh)
    v = np.asarray(mesh.vertices)
    print(f'frames used {used}, skipped {skipped}; mesh {len(v)} vertices, {len(mesh.triangles)} triangles')
    if len(v):
        print('bbox min', np.round(v.min(0), 2), 'max', np.round(v.max(0), 2),
              'floor z (1st percentile) %.3f' % np.percentile(v[:, 2], 1))


if __name__ == '__main__':
    main()
