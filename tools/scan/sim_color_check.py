#!/usr/bin/env python3
# 한글: (host, 시뮬레이션 실행 중) 팔을 스캔 자세 B로 두고 RTF·카메라 FPS·GPU 메모리를 잰 뒤 제자리에서 90°씩 돌며 카메라 4장을 저장한다.
#       스캔 방 메쉬의 색이 시뮬레이션 RGB 카메라에 보이는지 확인용. arm_hold.py는 미리 멈춰야 한다(host_sim_check.sh color).
"""Colour check in a running simulation: arm at scan pose B, RTF / camera FPS / GPU memory, 4 views 90 deg apart.

Usage: python3 tools/scan/sim_color_check.py <out_dir>   (stop arm_hold.py first; host_sim_check.sh ... color does)
"""
import subprocess
import sys
import time

import numpy as np
import rclpy
from geometry_msgs.msg import Twist
from PIL import Image as P
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import Image
from std_msgs.msg import Float64MultiArray

# 스캔 자세 B (tools/scan/README.md), 순서 joint1..5, r_joint / scan pose B
SCAN_POSE_B = [0.0042, -0.15, 0.30, 1.5, 0.0168, -0.0209]


def main():
    out = sys.argv[1]
    rclpy.init()
    n = rclpy.create_node('color_check')
    st = {'img': None, 'n': 0, 'clock': None}

    def on_img(m):
        st['img'] = m
        st['n'] += 1

    n.create_subscription(Image, '/depth_cam/color/image_raw', on_img, 10)
    n.create_subscription(Clock, '/clock', lambda m: st.update(clock=m.clock.sec + m.clock.nanosec * 1e-9), 10)
    arm = n.create_publisher(Float64MultiArray, '/arm_position_controller/commands', 10)
    cmd = n.create_publisher(Twist, '/cmd_vel', 10)

    def spin(sec, f=None):
        t0 = time.monotonic()
        while time.monotonic() - t0 < sec:
            if f:
                f()
            rclpy.spin_once(n, timeout_sec=0.05)

    spin(4.0, lambda: arm.publish(Float64MultiArray(data=SCAN_POSE_B)))
    while st['clock'] is None or st['img'] is None:
        rclpy.spin_once(n, timeout_sec=0.1)
    c0, n0, t0 = st['clock'], st['n'], time.monotonic()
    spin(10.0)
    dt = time.monotonic() - t0
    print('rtf %.2f, camera %.1f fps (wall clock)' % ((st['clock'] - c0) / dt, (st['n'] - n0) / dt))
    g = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu', '--format=csv,noheader'],
                       capture_output=True, text=True).stdout.strip()
    print('gpu memory, util:', g)
    for k in range(4):
        im = st['img']
        a = np.frombuffer(im.data, np.uint8).reshape(im.height, im.width, -1)[:, :, :3]
        sat = (a.max(2).astype(int) - a.min(2)).mean()
        P.fromarray(a).save(f'{out}/view{k}.png')
        print(f'view{k}: mean {a.mean():.1f}, std {a.std():.1f}, saturation {sat:.1f}')
        tw = Twist()
        tw.angular.z = 0.3
        spin(5.24, lambda: cmd.publish(tw))   # 약 90° / about 90 deg
        spin(2.0, lambda: cmd.publish(Twist()))
    rclpy.shutdown()


if __name__ == '__main__':
    main()
