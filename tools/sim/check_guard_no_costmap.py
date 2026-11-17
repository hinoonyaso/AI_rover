#!/usr/bin/env python3
"""Isolated ROS integration check: missing map causes guard abort and zero command.

한글: 격리된 ROS 시험에서 비용지도 누락 시 중단과 0 속도를 확인한다.
Run only when no other domain 31 simulation is running. Publishes simulated clock/TF only.
한글: 31번 도메인의 다른 시뮬레이션이 없을 때만 실행한다. 가상 시계/TF만 발행한다.
"""
import os
import signal
import subprocess
import time


def main():
    """Start a guarded action server and verify its missing-map failure.

    한글: 가드 액션 서버를 띄우고 비용지도 누락 실패를 확인한다.
    """
    if os.environ.get('ROS_DOMAIN_ID') != '31' or os.environ.get('ROS_AUTOMATIC_DISCOVERY_RANGE') != 'LOCALHOST':
        raise SystemExit('requires isolated ROS_DOMAIN_ID=31 and LOCALHOST discovery')
    import rclpy
    from action_msgs.msg import GoalStatus
    from geometry_msgs.msg import TransformStamped, Twist
    from nav2_msgs.action import NavigateToPose
    from rclpy.action import ActionClient
    from rclpy.node import Node
    from rosgraph_msgs.msg import Clock
    from tf2_ros import TransformBroadcaster

    proc = subprocess.Popen(
        ['ros2', 'run', 'jetrover_navigation', 'precise_approach.py', '--ros-args',
         '-p', 'use_sim_time:=true', '-p', 'relocalize:=false', '-p', 'sim_guard_enabled:=true'],
        start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rclpy.init()
    node = Node('precise_guard_missing_map_test')
    clock_pub = node.create_publisher(Clock, '/clock', 10)
    broadcaster = TransformBroadcaster(node)
    client = ActionClient(node, NavigateToPose, 'precise_approach')
    commands = []
    node.create_subscription(Twist, '/cmd_vel_nav', lambda m: commands.append(m), 10)
    start = time.monotonic()

    def tick():
        ns = int((100.0 + time.monotonic() - start) * 1e9)
        clock = Clock()
        clock.clock.sec, clock.clock.nanosec = divmod(ns, 1000000000)
        clock_pub.publish(clock)
        for parent, child in (('map', 'odom'), ('odom', 'base_footprint')):
            tf = TransformStamped()
            tf.header.stamp = clock.clock
            tf.header.frame_id = parent
            tf.child_frame_id = child
            tf.transform.rotation.w = 1.0
            broadcaster.sendTransform(tf)

    node.create_timer(0.05, tick)

    def wait_until(predicate, seconds):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.05)
            if predicate():
                return True
        return False

    try:
        if not wait_until(lambda: client.server_is_ready(), 20):
            raise RuntimeError('action server did not start')
        # Let TF and the simulated clock reach the action server before sending a goal.
        # 한글: 목표 전송 전에 가상 시계와 TF가 서버에 도착할 시간을 준다.
        wait_until(lambda: time.monotonic() - start > 3.0, 5)
        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        goal.pose.pose.position.x = 0.1
        goal.pose.pose.orientation.w = 1.0
        sent = client.send_goal_async(goal)
        if not wait_until(sent.done, 10) or not sent.result().accepted:
            raise RuntimeError('goal not accepted')
        result_future = sent.result().get_result_async()
        if not wait_until(result_future.done, 10):
            raise RuntimeError('guard did not return')
        result = result_future.result()
        wait_until(lambda: len(commands) > 0, 3)
        if result.status != GoalStatus.STATUS_ABORTED or result.result.error_code != 9105:
            raise RuntimeError(f'unexpected status/code: {result.status}/{result.result.error_code}')
        if not commands or any((m.linear.x, m.linear.y, m.angular.z) != (0.0, 0.0, 0.0) for m in commands):
            raise RuntimeError('expected only zero velocity commands')
        print(f'PASS: aborted 9105; {len(commands)} zero commands; no nonzero command')
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGINT)
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=5)


if __name__ == '__main__':
    main()
