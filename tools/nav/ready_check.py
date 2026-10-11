#!/usr/bin/env python3
# 한글: 기동 후 "시험을 시작해도 되는가"를 종료 코드로 알려 주는 Ready Gate. 하나라도 실패하면 종료 코드 1.
#       검사: 배터리(≥10.5 V), /scan, depth 토픽, odom 출처(엔코더/명령), Nav2 컨트롤러 파라미터, 위치 초기화(map→base_footprint TF).
"""Ready gate for the real-robot trials: prints a report and exits 1 if anything required is missing.

Usage: ready_check.py [--no-loc] [--expect-goal-tol 0.10] [--min-battery 10.5]
Required: battery >= 10.5 V, /scan, depth point-cloud topic alive, base odom twist source known, Nav2 controller answers,
          localisation (TF map -> base_footprint) unless --no-loc, goal checker tolerance == --expect-goal-tol if given.
Not required: depth point count (0 points just means nothing in the lane).
"""
import argparse
import sys
import time

import rclpy
from nav_msgs.msg import Odometry
from rcl_interfaces.srv import GetParameters
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import BatteryState, LaserScan, PointCloud2
import tf2_ros


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-loc', action='store_true', help='do not require the map->base_footprint TF')
    ap.add_argument('--expect-goal-tol', type=float, default=None)
    ap.add_argument('--min-battery', type=float, default=10.5)
    args = ap.parse_args()
    rclpy.init()
    n = rclpy.create_node('ready_check')
    got = {}
    n.create_subscription(BatteryState, 'battery_state', lambda m: got.setdefault('batt', m.voltage), 10)
    n.create_subscription(LaserScan, 'scan', lambda m: got.setdefault('scan', len(m.ranges)), qos_profile_sensor_data)
    n.create_subscription(PointCloud2, 'depth_cam/depth/points_sparse',
                          lambda m: got.setdefault('depth', m.width * m.height),
                          qos_profile_sensor_data)
    n.create_subscription(Odometry, 'odom_raw', lambda m: got.setdefault('odom_cov', m.twist.covariance[0]), 10)
    tf_buf = tf2_ros.Buffer()
    tf2_ros.TransformListener(tf_buf, n)
    t0 = time.time()
    while time.time() - t0 < 5.0 and len(got) < 4:
        rclpy.spin_once(n, timeout_sec=0.1)
    names = ['FollowPath.primary_controller', 'general_goal_checker.xy_goal_tolerance', 'FollowPath.xy_goal_tolerance']
    cli = n.create_client(GetParameters, '/controller_server/get_parameters')
    params = {}
    if cli.wait_for_service(timeout_sec=3.0):
        fut = cli.call_async(GetParameters.Request(names=names))
        rclpy.spin_until_future_complete(n, fut, timeout_sec=3.0)
        if fut.result() and len(fut.result().values) == len(names):
            for k, v in zip(names, fut.result().values):
                params[k] = v.string_value or v.double_value
    loc = None
    t1 = time.time()
    while time.time() - t1 < 2.0 and loc is None:
        rclpy.spin_once(n, timeout_sec=0.1)
        try:
            loc = tf_buf.lookup_transform('map', 'base_footprint', rclpy.time.Time())
        except Exception:  # noqa: BLE001
            loc = None

    fails = []
    b = got.get('batt')
    print('  battery %s V' % ('%.2f' % b if b else '?'))
    if b is None or b < args.min_battery:
        fails.append('battery %s V < %.1f V (charge)' % ('?' if b is None else '%.2f' % b, args.min_battery))
    print('  scan %s rays, depth topic %s (points %s)'
          % (got.get('scan', 'NONE'), 'alive' if 'depth' in got else 'NONE', got.get('depth', '-')))
    if 'scan' not in got:
        fails.append('no /scan')
    if 'depth' not in got:
        fails.append('no depth point-cloud messages')
    cov = got.get('odom_cov')
    print('  odom twist source: %s' % ('encoder' if cov is not None and cov < 0.001 else 'command' if cov else '?'))
    if cov is None:
        fails.append('no /odom_raw')
    if params:
        print('  controller %s, goal_checker xy_tol %s, controller xy_tol %s' % tuple(params[k] for k in names))
        if args.expect_goal_tol is not None and abs(params[names[1]] - args.expect_goal_tol) > 1e-6:
            fails.append('goal checker tolerance %s != expected %s' % (params[names[1]], args.expect_goal_tol))
    else:
        print('  controller: no answer')
        fails.append('Nav2 controller_server does not answer')
    if loc is not None:
        tr = loc.transform.translation
        print('  localisation: map->base_footprint at (%.2f, %.2f)' % (tr.x, tr.y))
    else:
        print('  localisation: NOT READY (no map->base_footprint)')
        if not args.no_loc:
            fails.append('not localised (place the robot on the start mark; run_trial.py scan-matches the start)')
    n.destroy_node()
    rclpy.shutdown()
    if fails:
        print('NOT READY:\n  - ' + '\n  - '.join(fails))
        sys.exit(1)
    print('READY')


if __name__ == '__main__':
    main()
