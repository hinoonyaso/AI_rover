#!/usr/bin/env python3
"""Measure the resting gyro bias and (optionally) store it in base.yaml.

Keep the robot completely still, base_node running (via base.launch.py), then:

    python3 measure_gyro_bias.py [seconds] [--write path/to/base.yaml]

The node already subtracts its current `gyro_bias`, so the new bias is
current + measured mean. The current value is read from the running node.
"""
import argparse
import re
import subprocess
import sys

import rclpy

from _imu import collect

MAX_STD = 0.02  # rad/s; more than this means the robot was not still


def current_bias():
    out = subprocess.run(
        ["ros2", "param", "get", "/base_node", "gyro_bias"],
        capture_output=True, text=True, timeout=10)
    nums = re.findall(r"-?\d+\.?\d*(?:e-?\d+)?", out.stdout.split(":", 1)[-1])
    if out.returncode != 0 or len(nums) != 3:
        sys.exit(f"cannot read /base_node gyro_bias: {out.stdout.strip() or out.stderr.strip()}")
    return [float(n) for n in nums]


def write_yaml(path, bias):
    text = open(path).read()
    new_line = f"gyro_bias: [{bias[0]:.4f}, {bias[1]:.4f}, {bias[2]:.4f}]"
    new_text, n = re.subn(r"gyro_bias:\s*\[[^\]]*\]", new_line, text)
    if n != 1:
        sys.exit(f"could not find a single gyro_bias line in {path}")
    open(path, "w").write(new_text)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("seconds", nargs="?", type=float, default=10.0)
    ap.add_argument("--write", metavar="YAML", help="store the new bias in this base.yaml")
    args = ap.parse_args()

    cur = current_bias()
    stats, n = collect(args.seconds, "gyro_bias")
    rclpy.shutdown()

    print(f"{n} samples in {args.seconds:.0f}s ({n / args.seconds:.0f} Hz)")
    for name in ("gx", "gy", "gz"):
        m, s = stats[name]
        print(f"{name}: mean {m: .5f}  std {s:.5f} rad/s")

    if any(stats[k][1] > MAX_STD for k in ("gx", "gy", "gz")):
        sys.exit(f"gyro std above {MAX_STD} rad/s: robot moved during measurement, not saving")

    new = [c + stats[k][0] for c, k in zip(cur, ("gx", "gy", "gz"))]
    print(f"current gyro_bias: {[round(c, 5) for c in cur]}")
    print(f"new     gyro_bias: [{new[0]:.4f}, {new[1]:.4f}, {new[2]:.4f}]")

    if args.write:
        write_yaml(args.write, new)
        print(f"written to {args.write} (rebuild or relaunch to apply)")


if __name__ == "__main__":
    main()
