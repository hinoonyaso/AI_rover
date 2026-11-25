#!/usr/bin/env python3
"""Record how Nav2 tries to leave a spot close to a wall (host, ROS_DOMAIN_ID=31, sim + Nav2 running).

Sets the AMCL initial pose, sends one NavigateToPose goal, and every 0.5 s logs the controller
command before collision_monitor (cmd_vel_smoothed), the command after it (cmd_vel), the
collision_monitor state (which polygon stopped the robot) and the map pose. Used for the
DirStop deadlock (troubleshooting/065): which motion does DirStop block?

  python3 tools/sim/wall_escape_probe.py --start 1.0 1.45 90 --goal 1.0 0.95 90 --seconds 90

한글: 벽 가까이에서 Nav2가 빠져나오려는 동작을 기록한다. 초기 자세를 주고 목표 하나를 보낸 뒤 0.5초마다
collision_monitor 전·후 속도 명령, 정지시킨 영역, 지도 위치를 출력한다(DirStop 교착 조사).
"""
import argparse
import math
import sys
import time


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--start', type=float, nargs=3, required=True, metavar=('X', 'Y', 'YAW_DEG'))
    ap.add_argument('--goal', type=float, nargs=3, required=True, metavar=('X', 'Y', 'YAW_DEG'))
    ap.add_argument('--seconds', type=float, default=90.0)
    args = ap.parse_args()

    import rclpy
    from rclpy.action import ActionClient
    from rclpy.node import Node
    from rclpy.parameter import Parameter
    from geometry_msgs.msg import PoseWithCovarianceStamped, Twist, TwistStamped
    from nav2_msgs.action import NavigateToPose
    from nav2_msgs.msg import CollisionMonitorState
    from tf2_ros import Buffer, TransformException, TransformListener

    rclpy.init()
    node = Node('wall_escape_probe', parameter_overrides=[Parameter('use_sim_time', value=True)])
    buffer = Buffer()
    TransformListener(buffer, node)
    latest = {'smoothed': None, 'out': None, 'state': None}

    def twist_of(msg):
        t = msg.twist if hasattr(msg, 'twist') else msg
        return (t.linear.x, t.linear.y, t.angular.z)

    def subscribe(topic, key):
        # Jazzy may publish Twist or TwistStamped depending on enable_stamped_cmd_vel.
        # 한글: 설정에 따라 Twist 또는 TwistStamped이므로 실제 형식을 보고 구독한다.
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            types = dict(node.get_topic_names_and_types()).get('/' + topic, [])
            if types:
                cls = TwistStamped if 'geometry_msgs/msg/TwistStamped' in types else Twist
                node.create_subscription(cls, topic, lambda m: latest.__setitem__(key, (time.monotonic(), twist_of(m))), 10)
                return cls.__name__
            rclpy.spin_once(node, timeout_sec=0.2)
        return None

    node.create_subscription(CollisionMonitorState, 'collision_monitor_state',
                             lambda m: latest.__setitem__('state', (time.monotonic(), m.action_type, m.polygon_name)), 10)
    initial = node.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
    pose = PoseWithCovarianceStamped()
    pose.header.frame_id = 'map'
    pose.pose.pose.position.x, pose.pose.pose.position.y = args.start[0], args.start[1]
    yaw = math.radians(args.start[2])
    pose.pose.pose.orientation.z, pose.pose.pose.orientation.w = math.sin(yaw / 2), math.cos(yaw / 2)
    pose.pose.covariance[0] = pose.pose.covariance[7] = 0.01
    pose.pose.covariance[35] = 0.01
    for _ in range(10):
        pose.header.stamp = node.get_clock().now().to_msg()
        initial.publish(pose)
        end = time.monotonic() + 0.5
        while time.monotonic() < end:
            rclpy.spin_once(node, timeout_sec=0.1)
    print('cmd_vel_smoothed type', subscribe('cmd_vel_smoothed', 'smoothed'), '| cmd_vel type', subscribe('cmd_vel', 'out'), flush=True)

    client = ActionClient(node, NavigateToPose, '/navigate_to_pose')
    if not client.wait_for_server(timeout_sec=30):
        print('navigate_to_pose unavailable')
        return 1
    goal = NavigateToPose.Goal()
    goal.pose.header.frame_id = 'map'
    goal.pose.header.stamp = node.get_clock().now().to_msg()
    goal.pose.pose.position.x, goal.pose.pose.position.y = args.goal[0], args.goal[1]
    gyaw = math.radians(args.goal[2])
    goal.pose.pose.orientation.z, goal.pose.pose.orientation.w = math.sin(gyaw / 2), math.cos(gyaw / 2)
    # bt_navigator may still be activating; retry until the goal is accepted.
    # 한글: bt_navigator가 아직 활성화 중일 수 있어 수락될 때까지 다시 보낸다.
    handle = None
    retry_until = time.monotonic() + 60
    while time.monotonic() < retry_until:
        goal.pose.header.stamp = node.get_clock().now().to_msg()
        future = client.send_goal_async(goal)
        while not future.done():
            rclpy.spin_once(node, timeout_sec=0.1)
        handle = future.result()
        if handle.accepted:
            break
        end = time.monotonic() + 3
        while time.monotonic() < end:
            rclpy.spin_once(node, timeout_sec=0.1)
    if handle is None or not handle.accepted:
        print('goal rejected for 60 s')
        return 1
    result = handle.get_result_async()
    start = time.monotonic()
    next_log = start
    print('   t   pose(x y yaw)        smoothed(vx vy wz)      out(vx vy wz)        collision', flush=True)
    while time.monotonic() - start < args.seconds and not result.done():
        rclpy.spin_once(node, timeout_sec=0.05)
        now = time.monotonic()
        if now < next_log:
            continue
        next_log = now + 0.5
        try:
            tf = buffer.lookup_transform('map', 'base_footprint', rclpy.time.Time()).transform
            q = tf.rotation
            where = f'{tf.translation.x:5.2f} {tf.translation.y:5.2f} {math.degrees(math.atan2(2*q.w*q.z, 1-2*q.z*q.z)):6.1f}'
        except TransformException:
            where = '   ?     ?      ?'

        def fmt(key):
            item = latest[key]
            if not item or now - item[0] > 1.0:
                return '        -        '
            vx, vy, wz = item[1]
            return f'{vx:+.3f} {vy:+.3f} {wz:+.2f}'
        state = latest['state']
        cm = f'{["none", "stop", "slowdown", "approach", "limit"][state[1]] if state[1] < 5 else state[1]}:{state[2]}' if state and now - state[0] < 1.0 else '-'
        print(f'{now - start:5.1f}  {where}   {fmt("smoothed")}   {fmt("out")}   {cm}', flush=True)
    if result.done():
        r = result.result()
        print(f'result status={r.status} error_code={r.result.error_code} after {time.monotonic() - start:.1f}s', flush=True)
    else:
        print('time limit; canceling', flush=True)
        cancel = handle.cancel_goal_async()
        end = time.monotonic() + 5
        while time.monotonic() < end and not cancel.done():
            rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_node()
    rclpy.try_shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())
