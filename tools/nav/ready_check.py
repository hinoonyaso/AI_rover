#!/usr/bin/env python3
# 한글: 기동 후 상태를 노드 하나로 한 번에 확인(배터리, 스캔, depth 점, odom 출처, Nav2 컨트롤러·허용 오차). ros2 CLI를 여러 번 부르지 않는다.
"""One-shot readiness report after bringup (battery, scan, depth points, odom source, Nav2 controller/tolerances)."""
import time

import rclpy
from nav_msgs.msg import Odometry
from rcl_interfaces.srv import GetParameters
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import BatteryState, LaserScan, PointCloud2


def main():
    rclpy.init()
    n = rclpy.create_node('ready_check')
    got = {}
    n.create_subscription(BatteryState, 'battery_state', lambda m: got.setdefault('batt', m.voltage), 10)
    n.create_subscription(LaserScan, 'scan', lambda m: got.setdefault('scan', len(m.ranges)), qos_profile_sensor_data)
    n.create_subscription(PointCloud2, 'depth_cam/depth/points_sparse',
                          lambda m: got.setdefault('depth', m.width * m.height), qos_profile_sensor_data)
    n.create_subscription(Odometry, 'odom_raw', lambda m: got.setdefault('odom_cov', m.twist.covariance[0]), 10)
    t0 = time.time()
    while time.time() - t0 < 4.0 and len(got) < 4:
        rclpy.spin_once(n, timeout_sec=0.1)
    names = ['FollowPath.primary_controller', 'general_goal_checker.xy_goal_tolerance', 'FollowPath.xy_goal_tolerance']
    cli = n.create_client(GetParameters, '/controller_server/get_parameters')
    params = {}
    if cli.wait_for_service(timeout_sec=3.0):
        fut = cli.call_async(GetParameters.Request(names=names))
        rclpy.spin_until_future_complete(n, fut, timeout_sec=3.0)
        if fut.result():
            for k, v in zip(names, fut.result().values):
                params[k] = v.string_value or v.double_value
    b = got.get('batt')
    print('  battery %s V%s' % ('%.2f' % b if b else '?', '  <-- CHARGE (< 10.5 V)' if b and b < 10.5 else ''))
    print('  scan %s rays, depth points %s' % (got.get('scan', 'NONE'), got.get('depth', 'NONE')))
    cov = got.get('odom_cov')
    print('  odom twist source: %s' % ('encoder' if cov is not None and cov < 0.001 else 'command' if cov else '?'))
    label = {names[0]: 'controller', names[1]: 'goal_checker xy_tol', names[2]: 'controller xy_tol'}
    print('  ' + ', '.join('%s %s' % (label[k], v) for k, v in params.items()) if params else '  controller: no answer')
    n.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
