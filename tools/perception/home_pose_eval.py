#!/usr/bin/env python3
# 한글: 팔 홈(주행) 자세 후보를 평가한다 — 지금 팔 자세에서 depth 카메라가 바닥을 어디서부터 어디까지 보는지,
#       로봇 자기 몸이 얼마나 보이는지, LiDAR가 얼마나 가려지는지를 재서 표(CSV)로 남긴다. 로봇/팔은 움직이지 않는다(읽기만).
#       checklist 8.13.5 (감지거리 0.18~0.51 m -> 목표 0.2~1.0 m).
"""Evaluate the current arm pose as a driving ("home") pose for depth obstacles. Read-only.

Needs: robot.launch.py (base_node -> /joint_states, URDF TF, LiDAR) + camera.launch.py running,
the arm already in the candidate pose, and NOTHING in front of the robot (flat floor, >= 1.5 m).

Usage: python3 tools/perception/home_pose_eval.py <label> [--seconds 3] [--png]
Appends one row to Log/home_pose_eval.csv and prints it. Metrics (base_footprint frame):
  joints            joint1..5 [rad] actually read from /joint_states
  cam_h / cam_pitch camera height [m] and optical-axis angle below horizontal [deg]
  valid             fraction of depth pixels with a reading
  floor_near/far    5th / 95th percentile forward distance x of floor points (|z| < 3 cm) [m]
  lane_cover        fraction of 5 cm bins between 0.20 m and 1.00 m ahead that contain floor points
                    inside the robot's width (|y| < 0.25) -- gaps = blind spots on the driving lane
  width_0.5/1.0     visible floor width at 0.5 m / 1.0 m ahead [m]
  self_frac         fraction of pixels that land inside the robot footprint (+5 cm) below 0.25 m
                    (own wheels/chassis in view; some is fine -- the background ref removes it)
  scan_valid        fraction of /scan beams with a valid range (arm occludes the rest)
Floor = the plane z=0 of base_footprint; points 3..25 cm high count as 'low' (obstacle band)
and should be ~0 on an empty floor (otherwise the TF/URDF or the pose reading is off).
"""
import argparse
import csv
import os
import sys
import time

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CameraInfo, Image, JointState, LaserScan
import tf2_ros

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from floor_metrics import FOOT_X, FOOT_Y, floor_metrics  # noqa: E402

JOINTS = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5']


def quat_to_rot(q):
    x, y, z, w = q.x, q.y, q.z, q.w
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


class Collector(Node):
    def __init__(self):
        super().__init__('home_pose_eval')
        self.depths, self.scans, self.info, self.joints = [], [], None, {}
        self.create_subscription(Image, '/depth_cam/depth/image_raw',
                                 lambda m: self.depths.append(m), qos_profile_sensor_data)
        self.create_subscription(CameraInfo, '/depth_cam/depth/camera_info',
                                 lambda m: setattr(self, 'info', m), qos_profile_sensor_data)
        self.create_subscription(LaserScan, '/scan', lambda m: self.scans.append(m),
                                 qos_profile_sensor_data)
        self.create_subscription(JointState, '/joint_states', self._js, 10)
        self.buf = tf2_ros.Buffer()
        self.tfl = tf2_ros.TransformListener(self.buf, self)

    def _js(self, m):
        for n, p in zip(m.name, m.position):
            self.joints[n] = p


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('label', help='name of this candidate, e.g. current_home, j4_1.40')
    ap.add_argument('--seconds', type=float, default=3.0)
    ap.add_argument('--png', action='store_true', help='save a top-down floor coverage plot')
    args = ap.parse_args()

    rclpy.init()
    node = Collector()
    t0 = time.time()
    while time.time() - t0 < args.seconds or not node.depths or node.info is None:
        rclpy.spin_once(node, timeout_sec=0.05)
        if time.time() - t0 > args.seconds + 10:
            raise SystemExit('no depth image / camera_info (camera.launch.py running?)')
    frame = node.depths[-1].header.frame_id
    try:
        tf = node.buf.lookup_transform('base_footprint', frame, rclpy.time.Time())
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f'no TF base_footprint <- {frame}: {e}')

    # Median of the collected frames (denoise) / 여러 프레임 중앙값
    d = np.median(np.stack([np.frombuffer(m.data, dtype=np.uint16).reshape(m.height, m.width)
                            for m in node.depths[-15:]]), axis=0)
    k = node.info.k
    R = quat_to_rot(tf.transform.rotation)
    t = np.array([tf.transform.translation.x, tf.transform.translation.y,
                  tf.transform.translation.z])
    m = floor_metrics(d, k[0], k[4], k[2], k[5], R, t)
    floor, low, pb, in_body = m['floor'], m['low'], m['pb'], m['in_body']

    scan_valid = float('nan')
    if node.scans:
        r = np.array(node.scans[-1].ranges)
        sc = node.scans[-1]
        scan_valid = float((np.isfinite(r) & (r > sc.range_min) & (r < sc.range_max)).mean())

    row = {
        'time': time.strftime('%Y%m%d_%H%M%S'), 'label': args.label,
        'joints': ' '.join(f'{node.joints.get(j, float("nan")):.3f}' for j in JOINTS),
        'cam_h_m': round(float(t[2]), 3), 'cam_pitch_deg': round(m['cam_pitch'], 1),
        'valid': round(m['valid'], 3),
        'floor_near_m': None if m['near'] is None else round(m['near'], 2),
        'floor_far_m': None if m['far'] is None else round(m['far'], 2),
        'lane_cover': round(m['lane_cover'], 2),
        'width_0.5_m': round(m['w05'], 2), 'width_1.0_m': round(m['w10'], 2),
        'self_frac': round(m['self_frac'], 3),
        'low_frac': round(m['low_frac'], 4),
        'scan_valid': round(scan_valid, 3),
    }
    for kk, v in row.items():
        print(f'  {kk:14s} {v}')
    if row['low_frac'] > 0.01:
        print('  WARNING: >1% of points 3-25 cm high on an "empty" floor -- something in view, or '
              'TF/URDF/joint reading off / 빈 바닥인데 낮은 점이 많음: 물체가 있거나 TF가 어긋남')
    os.makedirs('Log', exist_ok=True)
    path = 'Log/home_pose_eval.csv'
    new = not os.path.exists(path)
    with open(path, 'a', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(row))
        if new:
            wr.writeheader()
        wr.writerow(row)
    print(f'appended to {path}')

    if args.png:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(11, 5))
        sub = floor[::7]
        ax[0].scatter(sub[:, 1], sub[:, 0], s=1, c='tab:blue', label='floor')
        if len(low):
            ax[0].scatter(low[::3, 1], low[::3, 0], s=2, c='tab:red', label='3-25 cm')
        body = pb[in_body][::5]
        ax[0].scatter(body[:, 1], body[:, 0], s=1, c='tab:gray', label='self')
        ax[0].add_patch(plt.Rectangle((-FOOT_Y, -FOOT_X), 2 * FOOT_Y, 2 * FOOT_X, fill=False))
        for x0 in (0.2, 0.5, 1.0):
            ax[0].axhline(x0, ls=':', c='k', lw=0.6)
        ax[0].set_xlim(1.0, -1.0)
        ax[0].set_ylim(-0.4, 1.6)
        ax[0].set_aspect('equal')
        ax[0].set_xlabel('y (left +) [m]')
        ax[0].set_ylabel('x forward [m]')
        ax[0].legend(loc='upper right', fontsize=7)
        ax[0].set_title(f'{args.label}: near {row["floor_near_m"]} far {row["floor_far_m"]} '
                        f'lane {row["lane_cover"]}')
        ax[1].imshow(np.where(d > 0, d, np.nan), cmap='viridis')
        ax[1].set_title(f'depth (mm), valid {row["valid"]}')
        out = f'tools/viz/out/home_pose_{args.label}.png'
        plt.tight_layout()
        plt.savefig(out, dpi=80)
        print(f'saved {out}')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
