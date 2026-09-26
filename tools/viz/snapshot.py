#!/usr/bin/env python3
"""Save a top-down PNG of what the robot sees (for SSH sessions without RViz).

Usage: python3 snapshot.py [--frame odom|map] [--out FILE] [--seconds 3] [--radius 3.0]
Draws, in the fixed frame: /scan points, the /map occupancy grid (if it is being published), the TF
frames of the robot (base_link, lidar_frame, imu_link), a rough robot outline and the heading.
Needs the robot launch (and robot_state_publisher) running. Open the PNG in VS Code to view it.
The outline is the placeholder 0.30 x 0.20 m box from the URDF, not a measured footprint.
"""
import argparse
import math
import os
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import rclpy  # noqa: E402
from nav_msgs.msg import OccupancyGrid  # noqa: E402
from rclpy.duration import Duration  # noqa: E402
from rclpy.node import Node  # noqa: E402
from rclpy.qos import DurabilityPolicy, QoSProfile, qos_profile_sensor_data, ReliabilityPolicy  # noqa: E402
from sensor_msgs.msg import LaserScan  # noqa: E402
from tf2_ros import Buffer, TransformListener  # noqa: E402


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--frame', default='odom', help='fixed frame to draw in (odom or map)')
    ap.add_argument('--out', default=os.path.expanduser('~/jetrover_ws/tools/viz/out/snapshot.png'))
    ap.add_argument('--seconds', type=float, default=3.0, help='how long to collect data')
    ap.add_argument('--radius', type=float, default=3.0, help='half width of the view (m)')
    args = ap.parse_args()

    rclpy.init()
    n = Node('snapshot')
    buf = Buffer()
    TransformListener(buf, n)
    scans, grids = [], []
    n.create_subscription(LaserScan, 'scan', scans.append, qos_profile_sensor_data)
    n.create_subscription(
        OccupancyGrid, 'map', grids.append,
        QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                   durability=DurabilityPolicy.TRANSIENT_LOCAL))
    end = time.monotonic() + args.seconds
    while time.monotonic() < end:
        rclpy.spin_once(n, timeout_sec=0.05)
    if not scans:
        raise SystemExit('no /scan: is the robot launch running?')

    def tf(target, source):
        return buf.lookup_transform(target, source, rclpy.time.Time(), Duration(seconds=2.0))

    scan = scans[-1]
    try:
        t = tf(args.frame, scan.header.frame_id).transform
    except Exception as exc:  # noqa: BLE001 - LookupException, ExtrapolationException, ...
        if args.frame == 'map':
            print("'map' frame not found: SLAM is not running "
                  '(ros2 launch jetrover_navigation slam.launch.py). Drawing in odom instead.')
            args.frame = 'odom'
            t = tf(args.frame, scan.header.frame_id).transform
        else:
            raise SystemExit(f'TF lookup failed ({args.frame} <- {scan.header.frame_id}): {exc}')
    yaw = yaw_of(t.rotation)
    pts = []
    for i, r in enumerate(scan.ranges):
        if math.isfinite(r) and scan.range_min <= r <= scan.range_max:
            a = scan.angle_min + i * scan.angle_increment + yaw
            pts.append((t.translation.x + r * math.cos(a), t.translation.y + r * math.sin(a), r))
    pts = np.array(pts)

    base = tf(args.frame, 'base_link').transform
    bx, by, byaw = base.translation.x, base.translation.y, yaw_of(base.rotation)

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_facecolor('#202020')
    if grids:
        g = grids[-1]
        w, h = g.info.width, g.info.height
        data = np.array(g.data, dtype=np.int8).reshape(h, w)
        img = np.full((h, w), 0.5)
        img[data == 0] = 1.0
        img[data > 50] = 0.0
        ox, oy, res = g.info.origin.position.x, g.info.origin.position.y, g.info.resolution
        ax.imshow(img, cmap='gray', origin='lower', vmin=0, vmax=1, alpha=0.9,
                  extent=(ox, ox + w * res, oy, oy + h * res))
    if len(pts):
        sc = ax.scatter(pts[:, 0], pts[:, 1], c=pts[:, 2], s=6, cmap='plasma', zorder=3)
        fig.colorbar(sc, ax=ax, shrink=0.7, label='range (m)')
    # rough robot outline (placeholder 0.30 x 0.20 m box, centred on base_link)
    c, s = math.cos(byaw), math.sin(byaw)
    corners = np.array([(-0.15, -0.10), (0.15, -0.10), (0.15, 0.10), (-0.15, 0.10), (-0.15, -0.10)])
    world = np.array([(bx + c * x - s * y, by + s * x + c * y) for x, y in corners])
    ax.plot(world[:, 0], world[:, 1], color='cyan', lw=1.5, zorder=4)
    ax.arrow(bx, by, 0.25 * c, 0.25 * s, head_width=0.05, color='lime', zorder=5)
    for name in ('lidar_frame', 'imu_link'):
        try:
            f = tf(args.frame, name).transform.translation
            ax.plot(f.x, f.y, 'x', color='white', zorder=5)
            ax.annotate(name, (f.x, f.y), color='white', fontsize=7, xytext=(4, 4),
                        textcoords='offset points')
        except Exception:  # noqa: BLE001 - frame may not exist
            pass
    ax.set_xlim(bx - args.radius, bx + args.radius)
    ax.set_ylim(by - args.radius, by + args.radius)
    ax.set_aspect('equal')
    ax.grid(True, color='#444444', lw=0.4)
    ax.set_xlabel(f'x in {args.frame} (m)')
    ax.set_ylabel(f'y in {args.frame} (m)')
    ax.set_title(f'{time.strftime("%H:%M:%S")}  scan {len(pts)} pts'
                 f'{"  + /map" if grids else ""}  robot yaw {math.degrees(byaw):+.0f} deg')
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fig.savefig(args.out, dpi=110, bbox_inches='tight', facecolor='#202020')
    print(f'saved {args.out}  ({len(pts)} scan points, map={"yes" if grids else "no"})')
    rclpy.shutdown()


if __name__ == '__main__':
    main()
