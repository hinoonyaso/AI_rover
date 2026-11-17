"""ROS Action adapter for isolated fake-server tests only; no real navigation.

한글: 격리 가짜 서버 시험 전용 ROS Action 어댑터이며 실제 주행 기능이 아니다.
"""
import math
import os
import re
import time


_TEST_ACTION = re.compile(r'^/mission_test_[0-9a-f]{32}/navigate_to_pose$')


def require_isolated_environment(action_name):
    """Reject unisolated middleware and non-test action names before ROS init.

    한글: ROS 초기화 전에 격리되지 않은 미들웨어와 테스트 외 Action 이름을 거부한다.
    """
    if not isinstance(action_name, str) or not _TEST_ACTION.fullmatch(action_name):
        raise ValueError('a private test-only action name is required')
    if (os.environ.get('ROS_DOMAIN_ID') != '31' or
            os.environ.get('ROS_AUTOMATIC_DISCOVERY_RANGE') != 'LOCALHOST' or
            os.environ.get('RMW_IMPLEMENTATION') != 'rmw_fastrtps_cpp'):
        raise RuntimeError('requires domain 31, localhost discovery and Fast DDS')
    for name in ('ROS_STATIC_PEERS', 'ROS_DISCOVERY_SERVER', 'FASTRTPS_DEFAULT_PROFILES_FILE',
                 'FASTDDS_DEFAULT_PROFILES_FILE', 'CYCLONEDDS_URI'):
        if os.environ.get(name):
            raise RuntimeError(f'{name} must be unset in isolated tests')


def run_fake_navigation(action_name, x, y, yaw, *, available_timeout=1.0, result_timeout=2.0, cancel_timeout=1.0):
    """Run one test-only goal and report observed action outcome.

    한글: 테스트 전용 목표 하나를 수행하고 확인된 Action 결과를 반환한다.
    """
    require_isolated_environment(action_name)
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (x, y, yaw)):
        raise ValueError('finite test coordinates required')
    if not all(isinstance(v, (int, float)) and math.isfinite(v) and v > 0 for v in (available_timeout, result_timeout, cancel_timeout)):
        raise ValueError('positive finite timeouts required')

    import rclpy
    from rclpy.action import ActionClient
    from nav2_msgs.action import NavigateToPose
    from action_msgs.msg import GoalStatus

    def wait_future(node, future, timeout):
        deadline = time.monotonic() + timeout
        while not future.done() and time.monotonic() < deadline and rclpy.ok():
            rclpy.spin_once(node, timeout_sec=min(0.05, max(0.0, deadline - time.monotonic())))
        return future.done()

    rclpy.init()
    node = rclpy.create_node('mission_fake_navigation_client')
    client = ActionClient(node, NavigateToPose, action_name)
    try:
        if not client.wait_for_server(timeout_sec=available_timeout):
            return {'state': 'unavailable', 'reason': 'action_server_unavailable'}
        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = node.get_clock().now().to_msg()
        goal.pose.pose.position.x, goal.pose.pose.position.y = float(x), float(y)
        goal.pose.pose.orientation.z = math.sin(yaw / 2)
        goal.pose.pose.orientation.w = math.cos(yaw / 2)
        sent = client.send_goal_async(goal)
        if not wait_future(node, sent, available_timeout):
            # The server might accept a late goal; do not claim cancellation or retry.
            # 한글: 서버가 늦게 목표를 수락할 수 있으므로 취소 성공이나 재시도를 가정하지 않는다.
            return {'state': 'unknown', 'reason': 'goal_response_timeout'}
        handle = sent.result()
        if handle is None or not handle.accepted:
            return {'state': 'failed', 'reason': 'goal_rejected'}
        result_future = handle.get_result_async()
        timed_out = not wait_future(node, result_future, result_timeout)
        if timed_out:
            cancellation = handle.cancel_goal_async()
            wait_future(node, cancellation, cancel_timeout)
            if not wait_future(node, result_future, cancel_timeout):
                return {'state': 'unknown', 'reason': 'result_timeout_cancel_unconfirmed'}
        response = result_future.result()
        if response is None:
            return {'state': 'unknown', 'reason': 'missing_result'}
        if response.status == GoalStatus.STATUS_SUCCEEDED and response.result.error_code == 0:
            return {'state': 'succeeded', 'reason': 'confirmed_result'}
        if response.status == GoalStatus.STATUS_CANCELED:
            return {'state': 'canceled', 'reason': 'timeout_cancel_confirmed' if timed_out else 'cancel_confirmed'}
        if response.status == GoalStatus.STATUS_ABORTED or response.result.error_code != 0:
            return {'state': 'failed', 'reason': 'action_failed'}
        return {'state': 'unknown', 'reason': 'unrecognized_result'}
    finally:
        client.destroy()
        node.destroy_node()
        rclpy.shutdown()
