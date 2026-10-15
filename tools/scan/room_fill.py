#!/usr/bin/env python3
# 한글: (host, uv venv) 스캔 방의 빈 곳을 "보기 좋게" 메우는 보조 모델(room_lap2_fill)을 만든다 — 실제 복원이 아니라 합성이다.
#       1) 바닥: 스캔 바닥 정점 색을 위에서 1 cm 격자로 찍고 빈 칸은 가장 가까운 색으로 채운 텍스처(→ blender_textured_plane.py로 glb)
#       2) 벽(--walls, 기본 끔): SLAM 지도의 바깥 벽 칸 중 스캔 메쉬가 근처에 없는 곳에 상자 — 물건 자리에도 서서 기본에서 뺐다.
#       모든 형상은 visual만(충돌 없음), visibility_flags 2 → 시뮬레이션 LiDAR(mask 0xFFFFFFFD)는 못 본다(주행 시험 그대로).
"""Build the visual-only filler model for the scanned room (synthetic, not a reconstruction).

Usage: python3 tools/scan/room_fill.py room_visual.ply maps/<map>.yaml <model_dir> [--wall-height 1.6]
Writes <model_dir>/floor_albedo.png + floor.json (for blender_textured_plane.py -> meshes/floor.glb)
and <model_dir>/model.sdf / model.config with the wall boxes and the floor visual. Visuals carry
visibility_flags 2, which the simulated LiDAR's visibility_mask excludes, so LiDAR/Nav2 see exactly
what they saw before.
"""
import argparse
import json
import os
import sys

import numpy as np
import yaml
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..',
                                'src', 'jetrover_gazebo', 'scripts'))
from map_to_world import merge_rectangles, occupied_grid  # noqa: E402

VIS = '<visibility_flags>2</visibility_flags>'


def floor_texture(v, c, n, x0, y0, w, h, res):
    """Top-down floor colour image (row 0 = max y); empty cells take the nearest observed colour."""
    floor = (v[:, 2] < 0.03) & (n[:, 2] > 0.8)
    cols = ((v[floor, 0] - x0) / res).astype(int)
    rows = ((y0 + h - v[floor, 1]) / res).astype(int)
    W, H = int(round(w / res)), int(round(h / res))
    ok = (cols >= 0) & (cols < W) & (rows >= 0) & (rows < H)
    acc = np.zeros((H, W, 3))
    cnt = np.zeros((H, W))
    np.add.at(acc, (rows[ok], cols[ok]), c[floor][ok])
    np.add.at(cnt, (rows[ok], cols[ok]), 1)
    seen = cnt > 0
    img = np.zeros((H, W, 3))
    img[seen] = acc[seen] / cnt[seen][:, None]
    # 빈 칸 = 가장 가까운 관측 칸 색 / empty cells copy the nearest observed cell
    _, (ri, ci) = ndimage.distance_transform_edt(~seen, return_indices=True)
    img = img[ri, ci]
    img = ndimage.gaussian_filter(img, sigma=(1.5, 1.5, 0))
    return (np.clip(img, 0, 1) * 255).astype(np.uint8), seen.mean()


def main():
    import open3d as o3d
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('visual_ply')
    ap.add_argument('map_yaml')
    ap.add_argument('model_dir')
    ap.add_argument('--res', type=float, default=0.01, help='floor texture metres per pixel')
    # 벽 채움은 기본 끔(2026-10-16 사용자 확인): "스캔 점이 근처에 없음" 판단이 거칠어 물건이 있는 자리에도 벽이 섰고,
    # 10-05 지도에 맞춘 판은 보정이 아니라 없는 형상을 만드는 것 — 바닥 판만 쓴다. --walls로 켤 수는 있다.
    # Wall filling is off by default (user review): the gap test put walls where objects stand and invents geometry.
    ap.add_argument('--walls', action='store_true', help='also add wall boxes where the scan seems empty (off)')
    ap.add_argument('--wall-height', type=float, default=1.6)
    ap.add_argument('--gap-radius', type=float, default=0.10, help='no scan point this close -> wall gap')
    ap.add_argument('--name', default='room_lap2_fill')
    ap.add_argument('--samples', type=int, default=3000000, help='surface points sampled for colours')
    args = ap.parse_args()

    m = o3d.io.read_triangle_mesh(args.visual_ply)
    m.compute_vertex_normals()
    # 감량 메쉬의 정점은 듬성듬성(바닥 1 cm 칸의 5 %만 채움) → 표면에서 색 있는 점을 촘촘히 뽑아 쓴다
    # the decimated mesh's vertices are sparse (5 % of 1 cm floor cells): sample coloured surface points instead
    pts = m.sample_points_uniformly(args.samples, use_triangle_normal=True)
    v, c, n = np.asarray(pts.points), np.asarray(pts.colors), np.asarray(pts.normals)
    my = yaml.safe_load(open(args.map_yaml))
    res_m = my['resolution']
    ox, oy = my['origin'][0], my['origin'][1]
    iw, ih = Image.open(os.path.join(os.path.dirname(args.map_yaml), my['image'])).size
    x0, y0, w, h = ox, oy, iw * res_m, ih * res_m
    os.makedirs(os.path.join(args.model_dir, 'meshes'), exist_ok=True)

    img, seen = floor_texture(v, c, n, x0, y0, w, h, args.res)
    # 지도에서 "알 수 없음"(방 밖) 칸은 관측 바닥색 중앙값 한 가지로 — 가까운 색을 늘인 줄무늬가 어색했다(2026-10-16)
    # Unknown map cells (outside the room) get the median observed floor colour (nearest-fill made streaks).
    mimg = np.array(Image.open(os.path.join(os.path.dirname(args.map_yaml), my['image'])).convert('L'))
    unknown = (mimg > 50) & (mimg < 250)
    k = int(round(res_m / args.res))
    unknown = ndimage.binary_erosion(unknown.repeat(k, 0).repeat(k, 1), iterations=3)[:img.shape[0], :img.shape[1]]
    floor_obs = (v[:, 2] < 0.03) & (n[:, 2] > 0.8)
    img[unknown] = (np.median(c[floor_obs], axis=0) * 255).astype(np.uint8)
    Image.fromarray(img).save(os.path.join(args.model_dir, 'floor_albedo.png'))
    json.dump({'x0': x0, 'y0': y0, 'w': w, 'h': h, 'z': 0.0015},
              open(os.path.join(args.model_dir, 'floor.json'), 'w'))

    # 벽 틈: 점유 칸 중 스캔 점이 0.3~1.5 m 높이에서 gap_radius 안에 없는 칸 / wall gaps
    band = (v[:, 2] > 0.3) & (v[:, 2] < 1.5)
    tree = cKDTree(v[band, :2])
    occ, res2, (ox2, oy2) = occupied_grid(args.map_yaml)
    # 바깥 벽만: 점유 칸 중 2칸 안에 "알 수 없음"(방 밖) 칸이 있는 것. 방 안 장애물(가구 다리 등)에 1.6 m 벽을 세우면
    # 회색 기둥처럼 보였다(2026-10-16). Outer walls only: occupied cells within 2 cells of an unknown (outside) cell.
    mimg2 = np.array(Image.open(os.path.join(os.path.dirname(args.map_yaml), my['image'])).convert('L'))
    unknown2 = ndimage.binary_dilation((mimg2 > 50) & (mimg2 < 250), iterations=2)[::-1]   # row 0 = min y like occ
    gap = [[False] * len(row) for row in occ]
    for yy, row in enumerate(occ):
        for xx, o in enumerate(row):
            if o and unknown2[yy, xx]:
                p = (ox2 + (xx + 0.5) * res2, oy2 + (yy + 0.5) * res2)
                gap[yy][xx] = len(tree.query_ball_point(p, args.gap_radius)) == 0
    rects = merge_rectangles(gap) if args.walls else []
    # 벽 색 = 점유 칸 근처 스캔 벽 정점 색의 중앙값 / wall colour = median scan colour next to occupied cells
    occ_pts = np.array([(ox2 + (xx + 0.5) * res2, oy2 + (yy + 0.5) * res2)
                        for yy, row in enumerate(occ) for xx, o in enumerate(row) if o])
    near = cKDTree(occ_pts).query(v[band, :2])[0] < 0.1
    wc = c[band][near]
    wc = wc[wc.max(1) > 0.25]       # 어두운 가구·그림자 제외 / skip dark furniture and shadows
    wall_rgb = np.median(wc, axis=0) if len(wc) else np.array([0.75, 0.73, 0.70])
    col = '%.3f %.3f %.3f 1' % tuple(wall_rgb)

    visuals = [f'      <visual name="floor"><geometry><mesh><uri>model://{args.name}/meshes/floor.glb</uri></mesh>'
               f'</geometry>{VIS}</visual>']
    for i, (gx, gy, gx2, gy2) in enumerate(rects):
        cx, cy = ox2 + (gx + gx2 + 1) / 2 * res2, oy2 + (gy + gy2 + 1) / 2 * res2
        sx, sy = (gx2 - gx + 1) * res2, (gy2 - gy + 1) * res2
        visuals.append(
            f'      <visual name="wall_{i}"><pose>{cx:.4f} {cy:.4f} {args.wall_height / 2:.4f} 0 0 0</pose>'
            f'<geometry><box><size>{sx:.4f} {sy:.4f} {args.wall_height:.4f}</size></box></geometry>'
            f'<material><ambient>{col}</ambient><diffuse>{col}</diffuse></material>{VIS}</visual>')
    sdf = ('<?xml version="1.0"?>\n'
           '<!-- GENERATED by tools/scan/room_fill.py: visual-only filler for the scanned room (synthetic, NOT a\n'
           '     reconstruction). visibility_flags 2 = hidden from the simulated LiDAR (mask 0xFFFFFFFD).\n'
           '     한글: 스캔 방의 빈 곳을 보기 좋게 메우는 합성 형상. 충돌 없음, LiDAR에는 안 보임. -->\n'
           f'<sdf version="1.9">\n  <model name="{args.name}">\n    <static>true</static>\n    <link name="fill">\n'
           + '\n'.join(visuals) + '\n    </link>\n  </model>\n</sdf>\n')
    open(os.path.join(args.model_dir, 'model.sdf'), 'w').write(sdf)
    open(os.path.join(args.model_dir, 'model.config'), 'w').write(
        f'<?xml version="1.0"?>\n<model>\n  <name>{args.name}</name>\n  <version>0.1</version>\n'
        '  <sdf version="1.9">model.sdf</sdf>\n'
        '  <description>Visual-only filler for the scanned room: textured floor + walls where the scan has none '
        '(synthetic; hidden from the LiDAR).</description>\n</model>\n')
    n_gap = sum(sum(r) for r in gap)
    n_occ = sum(sum(r) for r in occ)
    print(f'floor texture {img.shape[1]}x{img.shape[0]} px, observed {seen * 100:.0f} % of the cells; '
          f'wall gaps {n_gap}/{n_occ} occupied cells -> {len(rects)} boxes'
          f'{"" if args.walls else " (walls off)"}, colour {col}')


if __name__ == '__main__':
    main()
