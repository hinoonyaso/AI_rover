# 한글: 2D 점(메쉬의 LiDAR 높이 단면)을 점유 지도에 맞추는 ICP(순수 numpy/scipy, 단위시험 대상).
"""2D rigid ICP of slice points to occupancy-map cells (pure numpy/scipy, unit-tested)."""
import math

import numpy as np
from scipy.spatial import cKDTree
import yaml


def occupied_points(map_yaml):
    """Return occupied cell centres (N,2) in the map frame from a ROS map .yaml (+ .pgm)."""
    import os
    meta = yaml.safe_load(open(map_yaml))
    with open(os.path.join(os.path.dirname(map_yaml), meta['image']), 'rb') as f:
        data = f.read()
    parts, i = [], 0
    while len(parts) < 4:
        while data[i:i + 1].isspace():
            i += 1
        if data[i:i + 1] == b'#':
            while data[i:i + 1] not in (b'\n', b''):
                i += 1
            continue
        j = i
        while not data[j:j + 1].isspace():
            j += 1
        parts.append(data[i:j])
        i = j
    w, h, maxval = int(parts[1]), int(parts[2]), int(parts[3])
    img = np.frombuffer(data[i + 1:i + 1 + w * h], dtype=np.uint8).reshape(h, w) / maxval
    p = img if int(meta.get('negate', 0)) else 1.0 - img
    rows, cols = np.nonzero(p > float(meta.get('occupied_thresh', 0.65)))
    res = float(meta['resolution'])
    ox, oy = float(meta['origin'][0]), float(meta['origin'][1])
    x = ox + (cols + 0.5) * res
    y = oy + (h - rows - 0.5) * res
    return np.stack([x, y], 1)


def transform(pts, x, y, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return pts @ np.array([[c, s], [-s, c]]) + np.array([x, y])


def _normals(dst, tree, k=6):
    """Return unit normals of the target points (PCA of k nearest neighbours)."""
    _, idx = tree.query(dst, k=k)
    nb = dst[idx] - dst[idx].mean(1, keepdims=True)
    cov = np.einsum('nki,nkj->nij', nb, nb)
    _, vec = np.linalg.eigh(cov)
    return vec[:, :, 0]  # eigenvector of the smallest eigenvalue = normal


def icp2d(src, dst, init=(0.0, 0.0, 0.0), iters=80, max_dist=0.3, tol=1e-7):
    """Point-to-line ICP: align src (N,2) to dst (M,2). Returns (x, y, yaw), point residuals.

    Point-to-line (distance along the target normal) instead of point-to-point: with walls sampled
    every map cell (5 cm) point-to-point ICP slides into local minima along the walls.
    한글: 점-선 ICP. 5 cm 칸으로 찍힌 벽에서 점-점 ICP는 벽 방향으로 미끄러진 국소 최소에 걸린다.
    """
    tree = cKDTree(dst)
    normals = _normals(dst, tree)
    x, y, yaw = init
    for _ in range(iters):
        cur = transform(src, x, y, yaw)
        d, idx = tree.query(cur)
        m = d < max_dist
        if m.sum() < 3:
            break
        a, b, n = cur[m], dst[idx[m]], normals[idx[m]]
        # linearised: n . (a + dth * perp(a) + t - b) = 0, perp(a) = (-ay, ax)
        jac = np.stack([n[:, 0] * -a[:, 1] + n[:, 1] * a[:, 0], n[:, 0], n[:, 1]], 1)
        rhs = -np.einsum('ij,ij->i', n, a - b)
        dth, dx, dy = np.linalg.lstsq(jac, rhs, rcond=None)[0]
        c, s_ = math.cos(dth), math.sin(dth)
        rot = np.array([[c, -s_], [s_, c]])
        t_new = rot @ np.array([x, y]) + np.array([dx, dy])
        x, y, yaw = t_new[0], t_new[1], yaw + dth
        if abs(dth) + abs(dx) + abs(dy) < tol:
            break
    d, _ = tree.query(transform(src, x, y, yaw))
    return (x, y, math.atan2(math.sin(yaw), math.cos(yaw))), d
