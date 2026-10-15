#!/usr/bin/env python3
# 한글: (host, uv venv) 지도 좌표로 맞춘 스캔 메쉬(room_in_map.ply)를 Gazebo 모델 에셋으로 바꾼다 — Blender 수작업 전의 자동 1차본.
#       바닥 높이를 추정해 z=0으로 맞춘다. visual: 바닥 포함(+3 mm), 감량(100k) → 정점 색 PLY(→ Blender로 glb, 텍스처 굽기).
#       collision: 바닥 뺀 메쉬를 크게 감량(≤ 5k) → stl. 수작업 단순 형상(벽=상자 등)보다 거칠고 구멍이 있을 수 있다.
"""Turn the aligned scan mesh into Gazebo assets (automatic first version, before any Blender clean-up).

Usage: python3 tools/scan/room_assets.py room_in_map.ply <model_dir> [--floor-z 0.03] [--visual-tris 100000]
       [--collision-tris 5000] [--max-z 2.0] [--crop-map maps/<map>.yaml]
Writes <model_dir>/room_visual.ply (convert with blender_ply_to_glb.py into meshes/room_visual.glb) and
meshes/room_collision.stl (map frame, metres, z-up).
"""
import argparse
import os

import numpy as np


def drop_triangles(mesh, keep_mask_fn):
    import open3d as o3d  # noqa: F401
    v = np.asarray(mesh.vertices)
    t = np.asarray(mesh.triangles)
    keep = keep_mask_fn(v[t])          # (n, 3, 3) -> (n,) bool
    mesh.remove_triangles_by_mask(~keep)
    mesh.remove_unreferenced_vertices()
    return mesh


def main():
    import open3d as o3d
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('mesh')
    ap.add_argument('model_dir')
    ap.add_argument('--floor-z', type=float, default=0.03,
                    help='collision: drop triangles entirely below this height above the estimated floor (m)')
    ap.add_argument('--visual-lift', type=float, default=0.003,
                    help='visual: raise the (kept) scanned floor this much above the ground plane (no z-fighting)')
    ap.add_argument('--max-z', type=float, default=2.0, help='drop triangles entirely above this (m)')
    # 10만: 2048² 텍스처로 구울 때 칸이 충분히 커서 검은 얼룩이 없다(30만이면 얼룩, 2026-10-14). LiDAR-지도 거리는 같음.
    # 100k: big enough texture cells for a clean 2048^2 bake (300k left speckles); LiDAR-to-map distance unchanged.
    ap.add_argument('--visual-tris', type=int, default=100000)
    ap.add_argument('--collision-tris', type=int, default=5000)
    ap.add_argument('--crop-map', default=None,
                    help='map yaml: drop triangles outside the map image extent (+ --crop-margin)')
    ap.add_argument('--crop-margin', type=float, default=0.10)
    # 작은 구멍 메우기(2026-10-16): 이 크기(m) 이하 구멍을 기존 정점끼리 이어 막는다(새 정점 없음 → 정점 색 유지). 0이면 끔.
    # Fill small holes up to this size (m) by joining existing vertices (no new vertices, colours kept); 0 = off.
    ap.add_argument('--fill-holes', type=float, default=0.05)
    ap.add_argument('--faces', choices=('keep', 'flip', 'double'), default='keep',
                    help='triangle winding for the visual mesh (Gazebo culls back faces; '
                         'LiDAR/camera see only front faces)')
    args = ap.parse_args()

    mesh = o3d.io.read_triangle_mesh(args.mesh)
    n0 = len(mesh.triangles)
    # 작은 떠다니는 조각 제거 / remove small floating clusters
    cid, cnt, _ = mesh.cluster_connected_triangles()
    cid, cnt = np.asarray(cid), np.asarray(cnt)
    mesh.remove_triangles_by_mask(cnt[cid] < 200)
    # 바닥 높이 추정 후 z=0으로 내린다: room1 스캔 바닥은 z≈0.044 m였다(2026-10-14) — 그대로 두면 바닥 평면 위 3 cm 큐브가 묻힌다.
    # Estimate the scanned floor (upward normals near z=0) and shift it to z = 0 (room1 floor was at z ~ 0.044 m).
    mesh.compute_vertex_normals()
    v, nz = np.asarray(mesh.vertices), np.asarray(mesh.vertex_normals)[:, 2]
    floor = float(np.median(v[(nz > 0.9) & (v[:, 2] > -0.1) & (v[:, 2] < 0.15), 2]))
    mesh.translate((0.0, 0.0, -floor))
    mesh = drop_triangles(mesh, lambda tri: (tri[:, :, 2].max(1) >= -0.05)
                          & (tri[:, :, 2].min(1) <= args.max_z))
    if args.crop_map:
        import yaml
        my = yaml.safe_load(open(args.crop_map))
        from PIL import Image
        w, h = Image.open(os.path.join(os.path.dirname(args.crop_map), my['image'])).size
        x0, y0 = my['origin'][0] - args.crop_margin, my['origin'][1] - args.crop_margin
        x1 = my['origin'][0] + w * my['resolution'] + args.crop_margin
        y1 = my['origin'][1] + h * my['resolution'] + args.crop_margin
        mesh = drop_triangles(mesh, lambda tri: (tri[:, :, 0].min(1) >= x0) & (tri[:, :, 0].max(1) <= x1)
                              & (tri[:, :, 1].min(1) >= y0) & (tri[:, :, 1].max(1) <= y1))
    n1 = len(mesh.triangles)

    vis = mesh.simplify_quadric_decimation(min(args.visual_tris, n1)) if n1 > args.visual_tris else mesh
    if args.fill_holes > 0:
        n_before = len(vis.triangles)
        src_v, src_c = np.asarray(vis.vertices).copy(), np.asarray(vis.vertex_colors).copy()
        vis = o3d.t.geometry.TriangleMesh.from_legacy(vis).fill_holes(hole_size=args.fill_holes).to_legacy()
        # fill_holes는 정점 순서를 바꾸고 색을 제대로 옮기지 않는다(검은 정점 8.6 → 55.6 %, 2026-10-16) — 같은 위치의 원래 색으로 다시 입힌다.
        # fill_holes reorders vertices without carrying the colours (black 8.6 -> 55.6 %): recolour from the
        # original vertex at the same position.
        from scipy.spatial import cKDTree
        _, idx = cKDTree(src_v).query(np.asarray(vis.vertices))
        vis.vertex_colors = o3d.utility.Vector3dVector(src_c[idx])
        print(f'filled holes <= {args.fill_holes} m: +{len(vis.triangles) - n_before} triangles (colours restored)')
    if args.faces != 'keep':
        t = np.asarray(vis.triangles)
        flipped = t[:, ::-1]
        vis.triangles = o3d.utility.Vector3iVector(np.vstack([t, flipped]) if args.faces == 'double' else flipped)
    vis.translate((0.0, 0.0, args.visual_lift))
    vis.compute_vertex_normals()
    # 충돌에는 바닥을 넣지 않는다(물리는 평평한 월드 바닥 평면) / no floor in the collision mesh: physics uses the ground plane
    col = drop_triangles(o3d.geometry.TriangleMesh(mesh), lambda tri: tri[:, :, 2].max(1) >= args.floor_z)
    col = col.simplify_quadric_decimation(args.collision_tris)
    col.remove_degenerate_triangles()
    col.remove_unreferenced_vertices()
    col.compute_triangle_normals()

    d = os.path.join(args.model_dir, 'meshes')
    os.makedirs(d, exist_ok=True)
    # glb는 Blender로 만든다(blender_ply_to_glb.py) — Open3D glb는 Gazebo가 못 읽음. 여기서는 정점 색 PLY만.
    # The GLB is made by Blender (blender_ply_to_glb.py); Open3D's GLB is rejected by Gazebo.
    pv, pc = os.path.join(args.model_dir, 'room_visual.ply'), os.path.join(d, 'room_collision.stl')
    o3d.io.write_triangle_mesh(pv, vis, write_ascii=False)
    o3d.io.write_triangle_mesh(pc, col)
    v = np.asarray(vis.vertices)
    print(f'scanned floor at z = {floor:.3f} m -> shifted to 0 (visual +{args.visual_lift} m, collision without floor)')
    print(f'input {n0} tris -> cleaned {n1} -> visual {len(vis.triangles)} (colors {vis.has_vertex_colors()}), '
          f'collision {len(col.triangles)}')
    print('visual bbox min', np.round(v.min(0), 2), 'max', np.round(v.max(0), 2))
    print('sizes: %s %.1f MB, %s %.2f MB' % (pv, os.path.getsize(pv) / 1e6, pc, os.path.getsize(pc) / 1e6))


if __name__ == '__main__':
    main()
