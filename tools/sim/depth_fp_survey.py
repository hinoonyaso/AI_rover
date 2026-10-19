#!/usr/bin/env python3
# 한글: 깊이 장애물(sparse_point_cloud)의 오탐 조사(host). 상자·큐브를 치운 빈 방에서 로봇을 여러 자리·방향에 놓고 장애물 점이
#       몇 개 나오는지 센다(물체가 없으니 나온 점은 전부 오탐). 위치마다 점 수, 로봇 기준 범위, 높이를 출력한다.
"""False positives of the depth obstacle points in the empty simulated room (host, ROS_DOMAIN_ID=31, Nav2 optional).

  python3 tools/sim/depth_fp_survey.py [--secs 3]
Robot is teleported to a grid of positions/yaws with the box and cubes moved under the floor; the sparse cloud
(/depth_cam/depth/points_sparse, robot frame) is counted for --secs seconds per pose.
"""
import argparse
import os
import sys

import numpy as np
import rclpy
from scipy.spatial.transform import Rotation
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import avoid_trials as T  # noqa: E402

XY = ((0.6, 0.6), (1.0, 0.6), (1.4, 0.6), (0.6, 1.0), (1.0, 1.0), (1.4, 1.0), (0.7, 1.35), (1.1, 1.35))
POSES = [(x, y, yaw) for yaw in (90.0, -90.0, 0.0) for (x, y) in XY]
LOW = 0.06     # m: points lower than this above the floor are floor noise (the box is 0.11 m, walls are higher)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--secs', type=float, default=3.0)
    args = ap.parse_args()
    rclpy.init()
    node, gt = T.Runner(), T.GroundTruth()
    clouds = []
    node.create_subscription(PointCloud2, '/depth_cam/depth/points_sparse', lambda m: clouds.append(m), 5)
    try:
        node.spin(3.0)
        for c in T.CUBES + (T.BOX,):
            T.gz_set_pose(c, 0.45, 1.35, -3.0)
        print(f'{"pose x y yaw":22s} {"msgs":>4s} {"pts/msg":>8s} | robot-frame height: low(<6cm)  high   | high points: forward range   z range', flush=True)
        total_low = []
        for (x, y, yaw) in POSES:
            T.gz_set_pose('jetrover', x, y, 0.01, yaw)
            node.spin(2.0)
            clouds.clear()
            node.spin(args.secs)
            lows, highs, counts, hp = [], [], [], []
            for m in clouds:
                p = np.array([[a, b, c] for a, b, c in point_cloud2.read_points(m, field_names=('x', 'y', 'z'), skip_nans=True)])
                counts.append(len(p))
                if not len(p):
                    continue
                try:
                    tr = node.buf.lookup_transform('base_footprint', m.header.frame_id, rclpy.time.Time())
                except Exception:  # noqa: BLE001
                    continue
                q, t = tr.transform.rotation, tr.transform.translation
                rot = Rotation.from_quat([q.x, q.y, q.z, q.w]).as_matrix()
                w = p @ rot.T + np.array([t.x, t.y, t.z])
                low = w[:, 2] < LOW
                lows.append(int(low.sum()))
                highs.append(int((~low).sum()))
                if (~low).any():
                    hp.append(w[~low])
            hp = np.vstack(hp) if hp else np.zeros((0, 3))
            hr = f'x {hp[:, 0].min():5.2f}..{hp[:, 0].max():5.2f}  z {hp[:, 2].min():5.2f}..{hp[:, 2].max():5.2f}' if len(hp) else '-'
            print(f'({x:4.2f}, {y:4.2f}, {yaw:5.0f})      {len(counts):4d} {np.mean(counts) if counts else 0:8.1f} | '
                  f'{np.mean(lows) if lows else 0:22.1f} {np.mean(highs) if highs else 0:6.1f}   | {hr}', flush=True)
            total_low.append(np.mean(lows) if lows else 0)
        print(f'poses with LOW (floor-noise) points: {sum(1 for t in total_low if t > 0)} of {len(total_low)}; mean {np.mean(total_low):.1f} points/msg')
    finally:
        gt.stop()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
