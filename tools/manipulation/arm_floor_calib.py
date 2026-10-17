#!/usr/bin/env python3
# 한글: 팔 관절 영점 점검 — 팔을 바닥을 보는 자세 여러 개로 옮기고, 각 자세에서 깊이 영상의 바닥 평면으로
#       카메라 높이·아래로 숙인 각도를 잰다(TF와 무관한 측정). URDF 모델과 비교해 관절 2·3·4 영점 오차를
#       최소제곱으로 구한다. 설정 파일은 바꾸지 않고 숫자만 출력한다. 팔이 움직인다(MoveIt 필요).
"""Arm joint zero-offset check from the floor plane seen by the depth camera. THE ARM MOVES.

Needs move_group (mode:=real), the bridge and the camera running. Usage:
  python3 tools/manipulation/arm_floor_calib.py [--scale 0.3] [--out calib.json]
Per pose: floor plane (RANSAC) in the camera frame gives camera height and pitch, independent of TF.
Fit: offsets d2, d3, d4 (rad) so that the URDF forward kinematics of q + d reproduces them.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import types

import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'sim'))
import moveit_t7 as T  # noqa: E402
from arm_ik import fk, load_chain  # noqa: E402

# (joint2, joint3, joint4) — 바닥이 보이고 손끝이 바닥에서 10 cm 이상 떠 있는 자세 / floor in view, tip >= 10 cm up
POSES = {
    'look_floor': (-0.35, 1.60, 1.60),
    'home': (-0.6618, 1.6629, 1.45),
    'p_a': (-0.30, 1.45, 1.60),
    'p_b': (0.15, 1.30, 1.30),
    'p_c': (0.00, 1.15, 1.60),
    'p_d': (-0.15, 1.60, 1.15),
    'p_e': (0.15, 1.60, 1.15),
}


def urdf_path():
    from ament_index_python.packages import get_package_share_directory
    xacro = os.path.join(get_package_share_directory('jetrover_description'), 'urdf', 'jetrover.xacro')
    out = tempfile.NamedTemporaryFile(suffix='.urdf', delete=False).name
    with open(out, 'w') as f:
        f.write(subprocess.run(['xacro', xacro], capture_output=True, text=True, check=True).stdout)
    return out


def fit_floor(dep, k):
    """RANSAC plane in the camera frame -> (height m, pitch deg, inlier ratio). 한글: 바닥 평면 맞춤."""
    fx, cx, fy, cy = k[0], k[2], k[4], k[5]
    vs, us = np.mgrid[0:dep.shape[0]:4, 0:dep.shape[1]:4]
    z = dep[::4, ::4]
    ok = (z > 0.1) & (z < 1.0)
    pts = np.stack([(us - cx) * z / fx, (vs - cy) * z / fy, z], -1)[ok]
    rng = np.random.default_rng(0)
    best = None
    for _ in range(400):
        s = pts[rng.choice(len(pts), 3, replace=False)]
        nn = np.cross(s[1] - s[0], s[2] - s[0])
        if np.linalg.norm(nn) < 1e-9:
            continue
        nn /= np.linalg.norm(nn)
        inl = np.abs(pts @ nn - nn @ s[0]) < 0.01
        if best is None or inl.sum() > best.sum():
            best = inl
    q = pts[best]
    c = q.mean(0)
    n = np.linalg.svd(q - c)[2][2]
    return abs(n @ c), np.degrees(np.arcsin(abs(n[2]))), best.sum() / len(pts)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--scale', type=float, default=0.3)
    ap.add_argument('--out', default='')
    args = ap.parse_args()

    from cv_bridge import CvBridge
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import CameraInfo, Image
    from tf2_ros import Buffer, TransformListener

    rig = T.Rig(types.SimpleNamespace(scale=args.scale, tol=0.05, settle=1.5, temp_stop=None))
    if not rig.move.wait_for_server(timeout_sec=15):
        sys.exit('move_action not available')
    br, frames, info = CvBridge(), [], {}
    rig.n.create_subscription(Image, 'depth_cam/depth/image_raw',
                              lambda m: frames.append(br.imgmsg_to_cv2(m, 'passthrough').copy()),
                              qos_profile_sensor_data)
    rig.n.create_subscription(CameraInfo, 'depth_cam/color/camera_info',
                              lambda m: info.__setitem__('k', list(m.k)), qos_profile_sensor_data)
    buf = Buffer()
    TransformListener(buf, rig.n)
    chain = load_chain(urdf_path(), 'depth_cam_link')

    def model(q5, d):
        t = fk(chain, np.array([q5[0], q5[1] + d[0], q5[2] + d[1], q5[3] + d[2], q5[4]]))
        return t[2, 3], np.degrees(np.arcsin(-t[2, 0]))     # camera height, pitch down

    rows = []
    for name, (j2, j3, j4) in POSES.items():
        goal = {'joint1': 0.0, 'joint2': j2, 'joint3': j3, 'joint4': j4, 'joint5': 0.0}
        if not rig.go(name, 'arm', goal):
            print(f'FAIL moving to {name}: stop', flush=True)
            break
        q = [rig.js.get(j, float('nan')) for j in T.ARM]
        frames.clear()
        t0 = time.monotonic()
        while len(frames) < 15 and time.monotonic() - t0 < 10:
            rig.spin(0.1)
        if len(frames) < 8 or 'k' not in info:
            print(f'{name}: no depth frames, skipped', flush=True)
            continue
        dep = np.median(np.array(frames[-15:]).astype(float), axis=0) / 1000.0
        h, pitch, ratio = fit_floor(dep, info['k'])
        mh, mp = model(q, (0, 0, 0))
        rows.append({'pose': name, 'q': q, 'h': h, 'pitch': pitch, 'inlier': ratio})
        print(f'  {name:10s} measured h {h:.3f} pitch {pitch:5.1f} (floor inliers {ratio:.0%}) | '
              f'model h {mh:.3f} pitch {mp:5.1f} | diff h {1000 * (h - mh):+.0f} mm pitch {pitch - mp:+.1f} deg',
              flush=True)
    rig.go('look_floor', 'arm', {'joint1': 0.0, 'joint2': -0.35, 'joint3': 1.60, 'joint4': 1.60,
                                 'joint5': 0.0})
    good = [r for r in rows if r['inlier'] > 0.5]
    print(f'{len(good)} usable poses of {len(rows)}', flush=True)
    if len(good) < 4:
        sys.exit('too few usable poses to fit')

    def resid(d, use):
        out = []
        for r in use:
            mh, mp = model(r['q'], d)
            out += [(r['h'] - mh) / 0.01, (r['pitch'] - mp) / 1.0]   # 1 cm and 1 deg weigh the same
        return out

    def solve(use):
        return least_squares(resid, np.zeros(3), args=(use,), bounds=([-0.2] * 3, [0.2] * 3))
    full = solve(good)
    rad = ' '.join(f'{x:+.4f}' for x in full.x)
    deg = ' '.join(f'{np.degrees(x):+.2f}' for x in full.x)
    print(f'offsets d2 d3 d4 (rad): {rad} = (deg) {deg}', flush=True)
    for r in good:
        mh, mp = model(r['q'], full.x)
        print(f'  after fit {r["pose"]:10s} diff h {1000 * (r["h"] - mh):+.0f} mm pitch {r["pitch"] - mp:+.2f} deg')
    print('leave-one-out offsets (deg):', flush=True)
    for i, r in enumerate(good):
        s = solve(good[:i] + good[i + 1:])
        print(f'  without {r["pose"]:10s} ' + ' '.join(f'{np.degrees(x):+.2f}' for x in s.x), flush=True)
    if args.out:
        with open(args.out, 'w') as f:
            json.dump({'rows': rows, 'offsets_rad': full.x.tolist()}, f, indent=1)


if __name__ == '__main__':
    main()
