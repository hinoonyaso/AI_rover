#!/usr/bin/env python3
# 한글: 새 홈 자세의 기준 depth 이미지(sparse_point_cloud의 self-filter용)를 찍는다. 여러 프레임의 중앙값을 저장하고,
#       기존 파일은 덮어쓰기 전에 날짜+관절값 이름으로 백업한다. 로봇/팔은 움직이지 않는다(읽기만).
"""Capture the depth background reference for the current (home) arm pose. Read-only.

Needs camera.launch.py (+ robot.launch.py for /joint_states), the arm in the NEW home pose and
nothing in front of the robot (flat empty floor). Writes the median of --frames depth images to
src/jetrover_perception/config/depth_background_ref.npy after backing up the existing file as
depth_background_ref.<YYYYmmdd_HHMMSS>.npy. Rebuild jetrover_perception and restart
camera.launch.py afterwards, and update base.yaml arm_home_pose_rad to the same pose
(the home-pose gate reads it).

Usage: python3 tools/perception/capture_depth_reference.py [--frames 30] [--dry-run]
"""
import argparse
import os
import shutil
import time

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image, JointState

REF = os.path.expanduser(
    '~/jetrover_ws/src/jetrover_perception/config/depth_background_ref.npy')


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--frames', type=int, default=30)
    ap.add_argument('--dry-run', action='store_true', help='measure only, do not write')
    ap.add_argument('--out', default=REF, help='output .npy (default: the real-robot reference; Gazebo: '
                    'src/jetrover_gazebo/config/depth_background_ref_sim.npy)')
    args = ap.parse_args()

    rclpy.init()
    node = Node('capture_depth_reference')
    frames, joints = [], {}
    node.create_subscription(Image, '/depth_cam/depth/image_raw',
                             lambda m: frames.append(m), qos_profile_sensor_data)

    def js(m):
        for n, p in zip(m.name, m.position):
            joints[n] = p
    node.create_subscription(JointState, '/joint_states', js, 10)
    t0 = time.time()
    while len(frames) < args.frames and time.time() - t0 < 30:
        rclpy.spin_once(node, timeout_sec=0.05)
    if len(frames) < args.frames:
        raise SystemExit(f'only {len(frames)} depth frames in 30 s')
    stack = np.stack([np.frombuffer(m.data, dtype=np.uint16).reshape(m.height, m.width)
                      for m in frames[-args.frames:]])
    # Median over frames, but a pixel valid in < half the frames stays 0 (invalid).
    # 한글: 프레임 중앙값. 절반 미만 프레임에서만 값이 있는 픽셀은 0(무효)으로 둔다.
    valid_count = (stack > 0).sum(0)
    stack_f = np.where(stack > 0, stack, np.nan).astype(np.float32)
    med = np.nan_to_num(np.nanmedian(stack_f, axis=0), nan=0.0)
    ref = np.where(valid_count >= args.frames // 2, med, 0).astype(np.uint16)
    noise = np.nanstd(stack_f, axis=0)
    pose = ' '.join(f'{joints.get(f"joint{i}", float("nan")):.3f}' for i in range(1, 6))
    print(f'joints 1-5: {pose}')
    print(f'valid fraction {float((ref > 0).mean()):.3f}, depth noise median '
          f'{float(np.nanmedian(noise)):.1f} mm, p95 {float(np.nanpercentile(noise, 95)):.1f} mm '
          f'(background_margin_mm is 60)')
    if args.dry_run:
        print('dry run: nothing written')
    else:
        out = os.path.abspath(os.path.expanduser(args.out))
        if os.path.exists(out):
            backup = out.replace('.npy', time.strftime('.%Y%m%d_%H%M%S.npy'))
            shutil.copy2(out, backup)
            print(f'backed up old reference -> {backup}')
        np.save(out, ref)
        print(f'wrote {out}  ({ref.shape[1]}x{ref.shape[0]})')
        print('next: colcon build --packages-select jetrover_perception, '
              'restart camera.launch.py, '
              f'set base.yaml arm_home_pose_rad joints 1-5 = [{pose.replace(" ", ", ")}]')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
