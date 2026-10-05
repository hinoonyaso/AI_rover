#!/usr/bin/env python3
# 한글: 현재 위치에서 목표까지의 "직선" 위에 일정 간격으로 웨이포인트를 찍어 NavigateThroughPoses로 보낸다.
# 장애물을 피한 뒤 다음 웨이포인트(선 위)로 돌아오게 해서 원래 직선 경로로 복귀시킨다.
"""Drive along a straight line with Nav2, rejoining the line after avoiding obstacles.

Usage: python3 line_goal.py X Y [YAW_DEG] [--spacing 0.3]      (map frame, metres)
Needs Nav2 running and AMCL localized. Sends NavigateThroughPoses with waypoints every `spacing` m
on the segment current_pose -> goal. A plain NavigateToPose replans the shortest path from wherever
the robot ends up after an obstacle and cuts diagonally to the goal; waypoints on the line make it
come back to the line instead.
"""
import argparse
import math

from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateThroughPoses
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data  # noqa: F401  (kept for parity with other tools)
import tf2_ros


def yaw_to_quat(yaw):
    return math.sin(yaw / 2.0), math.cos(yaw / 2.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('x', type=float)
    ap.add_argument('y', type=float)
    ap.add_argument('yaw_deg', type=float, nargs='?', default=None)
    ap.add_argument('--spacing', type=float, default=0.3)
    args = ap.parse_args()

    rclpy.init()
    node = Node('line_goal')
    buf = tf2_ros.Buffer()
    tf2_ros.TransformListener(buf, node)
    # 한글: map -> base_footprint TF로 현재 위치를 얻는다.
    start = None
    for _ in range(100):
        rclpy.spin_once(node, timeout_sec=0.1)
        try:
            t = buf.lookup_transform('map', 'base_footprint', rclpy.time.Time())
            start = (t.transform.translation.x, t.transform.translation.y)
            break
        except Exception:
            pass
    if start is None:
        raise SystemExit('no map->base_footprint TF (is AMCL running?)')

    dx, dy = args.x - start[0], args.y - start[1]
    dist = math.hypot(dx, dy)
    heading = math.atan2(dy, dx)
    final_yaw = math.radians(args.yaw_deg) if args.yaw_deg is not None else heading
    n = max(1, int(math.ceil(dist / args.spacing)))
    poses = []
    for i in range(1, n + 1):
        f = i / n
        p = PoseStamped()
        p.header.frame_id = 'map'
        p.pose.position.x = start[0] + dx * f
        p.pose.position.y = start[1] + dy * f
        yaw = final_yaw if i == n else heading
        p.pose.orientation.z, p.pose.orientation.w = yaw_to_quat(yaw)
        poses.append(p)
    print('line from (%.2f, %.2f) to (%.2f, %.2f): %d waypoints, %.2f m' % (start[0], start[1], args.x, args.y, n, dist))

    client = ActionClient(node, NavigateThroughPoses, 'navigate_through_poses')
    if not client.wait_for_server(timeout_sec=10.0):
        raise SystemExit('navigate_through_poses action server not available')
    goal = NavigateThroughPoses.Goal()
    goal.poses = poses
    send = client.send_goal_async(goal, feedback_callback=lambda fb: print(
        'remaining %.2f m, recoveries %d' % (fb.feedback.distance_remaining, fb.feedback.number_of_recoveries)))
    rclpy.spin_until_future_complete(node, send)
    handle = send.result()
    if not handle.accepted:
        raise SystemExit('goal rejected')
    result = handle.get_result_async()
    try:
        rclpy.spin_until_future_complete(node, result)
        print('status', result.result().status)
    except KeyboardInterrupt:
        handle.cancel_goal_async()  # 한글: Ctrl+C면 목표를 취소해 로봇을 세운다.
        print('cancelled')


if __name__ == '__main__':
    main()
