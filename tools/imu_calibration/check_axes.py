#!/usr/bin/env python3
# 한글: IMU 축이 base_node 규약(x 앞, y 왼쪽, z 위)을 따르는지 3자세(평평/왼쪽 위/앞쪽 아래)로 확인한다. base_node가 떠 있어야 한다.
"""Check that /imu/data_raw follows the base_node convention (x forward, y left, z up).

base_node must be running. The script asks for three poses and averages the
accelerometer for a few seconds in each. Expected (REP-103, gravity 9.8 m/s^2):

    flat                 z ~ +9.8
    left side up (90)    y ~ +9.8
    nose down    (90)    x ~ -9.8

A pose does not have to be exact: the expected axis must be above 7 m/s^2
(sign included) and the other two axes must stay below 4 m/s^2 in magnitude.
"""
import sys

import rclpy

from _imu import collect

POSES = [
    ("flat, on its wheels", "az", +1, "z"),
    ("left side UP (right side down), about 90 deg", "ay", +1, "y"),
    ("nose DOWN (rear up), about 90 deg", "ax", -1, "x"),
]
MIN_MAIN = 7.0
MAX_OTHER = 4.0


def main():
    seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0
    failed = 0
    for title, axis, sign, label in POSES:
        input(f"\nPose: {title}. Hold still, then press Enter... ")
        stats, _ = collect(seconds, "check_axes")
        a = {k: stats[k][0] for k in ("ax", "ay", "az")}
        main_ok = sign * a[axis] > MIN_MAIN
        others_ok = all(abs(v) < MAX_OTHER for k, v in a.items() if k != axis)
        ok = main_ok and others_ok
        failed += not ok
        print(f"  ax={a['ax']:+.2f} ay={a['ay']:+.2f} az={a['az']:+.2f}  "
              f"expected {label} {'+' if sign > 0 else '-'}9.8 -> {'PASS' if ok else 'FAIL'}")
    rclpy.shutdown()
    print("\nAll axes OK." if not failed else f"\n{failed} pose(s) failed: check the axis mapping in base_node.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
