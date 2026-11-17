"""Test-only Nav2-shaped Action server; never controls a robot.

한글: 로봇을 제어하지 않는 테스트 전용 Nav2 형식 Action 서버.
"""
import sys
import time

from fake_nav_adapter import require_isolated_environment


def main():
    """Run one isolated fake server. / 격리 가짜 서버 하나를 실행한다."""
    name, behavior = sys.argv[1:3]
    require_isolated_environment(name)
    if behavior not in ('success', 'abort', 'cancel', 'unresponsive', 'reject'):
        raise ValueError('unknown fake behavior')
    import rclpy
    from rclpy.action import ActionServer, CancelResponse, GoalResponse
    from rclpy.executors import MultiThreadedExecutor
    from rclpy.node import Node
    from nav2_msgs.action import NavigateToPose

    def accept(_request):
        return GoalResponse.REJECT if behavior == 'reject' else GoalResponse.ACCEPT

    def cancel(_request):
        return CancelResponse.REJECT if behavior == 'unresponsive' else CancelResponse.ACCEPT

    def execute(handle):
        result = NavigateToPose.Result()
        if behavior in ('cancel', 'unresponsive'):
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                if handle.is_cancel_requested:
                    handle.canceled()
                    return result
                time.sleep(.02)
        if behavior == 'abort':
            handle.abort()
            result.error_code = 1
        else:
            handle.succeed()
        return result

    rclpy.init()
    node = Node('mission_fake_navigation_server')
    server = ActionServer(node, NavigateToPose, name, execute, goal_callback=accept, cancel_callback=cancel)
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)
    print('ready', flush=True)
    try:
        executor.spin()
    finally:
        server.destroy()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
