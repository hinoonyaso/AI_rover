"""Run one navigation trial in a local Gazebo simulation only.

한글: 로컬 Gazebo 시뮬레이션에서만 주행 시험 한 회를 실행한다.
"""
import json
import hashlib
import math
import select
import subprocess
import os
import sys
import time
from pathlib import Path


def require_simulation():
    """Validate ROS isolation before initializing ROS. / ROS 초기화 전 격리 조건을 검증한다."""
    if (os.environ.get('ROS_DOMAIN_ID') != '31' or
            os.environ.get('RMW_IMPLEMENTATION') != 'rmw_fastrtps_cpp'):
        raise RuntimeError('requires isolated domain 31 and Fast DDS')
    for name in ('ROS_STATIC_PEERS', 'ROS_DISCOVERY_SERVER', 'FASTDDS_DEFAULT_PROFILES_FILE',
                 'CYCLONEDDS_URI', 'FASTDDS_BUILTIN_TRANSPORTS', 'ROS_LOCALHOST_ONLY'):
        if os.environ.get(name):
            raise RuntimeError(f'{name} must be unset')
    discovery = os.environ.get('ROS_AUTOMATIC_DISCOVERY_RANGE')
    profile = os.environ.get('FASTRTPS_DEFAULT_PROFILES_FILE')
    if discovery == 'LOCALHOST' and not profile:
        return
    # Only the verified loopback-only profile may replace localhost discovery.
    # 한글: localhost 검색을 대체할 때는 검증된 루프백 전용 프로필만 허용한다.
    expected = Path(__file__).resolve().with_name('fastdds-loopback.xml')
    try:
        valid = (discovery == 'SUBNET' and os.environ.get('GZ_IP') == '127.0.0.1' and
                 profile and Path(profile).resolve(strict=True) == expected and
                 hashlib.sha256(expected.read_bytes()).hexdigest() ==
                 '1b5d742f8a890be37c4cf93f0acdccc3c5ef3027efd4b481b46de562efe82714')
    except OSError:
        valid = False
    if not valid:
        raise RuntimeError('requires localhost discovery or the verified loopback UDP profile')


def verify_gazebo_pose(resume=False):
    """Require the fixed simulated start pose before initializing AMCL.

    한글: AMCL 초기화 전 고정된 Gazebo 시작 자세를 확인한다.
    """
    try:
        completed = subprocess.run(['gz', 'topic', '-e', '-t', '/world/jetrover_room/dynamic_pose/info',
                                    '--json-output', '-n', '1'], capture_output=True, text=True, timeout=15, check=True)
        data = json.loads(completed.stdout)
        robot = next(item for item in data['pose'] if item.get('name') == 'jetrover')
        pos, quat = robot['position'], robot['orientation']
        x, y, z, w = float(pos['x']), float(pos['y']), float(quat.get('z', 0)), float(quat['w'])
        yaw = math.atan2(2 * w * z, 1 - 2 * z * z)
        if not all(math.isfinite(value) for value in (x, y, yaw)):
            raise ValueError('invalid pose')
        if resume:
            valid = math.hypot(x - 1.0, y - 1.45) < .40
        else:
            valid = math.hypot(x - 1.02, y - .37) < .15 and abs(math.atan2(math.sin(yaw - 1.45), math.cos(yaw - 1.45))) < .35
        if not valid:
            raise RuntimeError('gazebo_start_pose_mismatch')
    except RuntimeError:
        raise
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, StopIteration):
        raise RuntimeError('gazebo_pose_unavailable') from None


def main():
    """Verify simulated hardware and send one known simulation goal.

    한글: 시뮬레이션 하드웨어 확인 후 알려진 시뮬레이션 목표 한 개를 전송한다.
    """
    require_simulation()
    if (any(arg not in ('--resume', '--managed', '--inspect', '--prepare-only', '--return') for arg in sys.argv[1:]) or
            len(set(sys.argv[1:])) != len(sys.argv[1:]) or
            ('--prepare-only' in sys.argv and len(sys.argv) != 2) or
            ('--inspect' in sys.argv and '--return' in sys.argv)):
        raise ValueError('unsupported or duplicate option')
    resume = '--resume' in sys.argv[1:]
    managed = '--managed' in sys.argv[1:]
    def read_command():
        # Supervisor commands, one per line: cancel / pause / resume. EOF counts as cancel.
        # 한글: 감독자 명령(한 줄에 하나): cancel / pause / resume. 입력이 닫히면 취소로 본다.
        if not managed or not select.select([sys.stdin], [], [], 0)[0]:
            return None
        line = sys.stdin.readline()
        command = line.strip()
        return 'cancel' if not line or command not in ('pause', 'resume') else command

    def stop_requested():
        # Before or after driving only cancellation matters; pause/resume are ignored.
        # 한글: 주행 전후에는 취소만 의미가 있고 일시정지·재개는 무시한다.
        return read_command() == 'cancel'
    def emit(state, reason, colors=None, diagnostics=None):
        print('MISSION_RESULT ' + json.dumps({'state': state, 'reason': reason, 'colors': colors,
                                               'diagnostics': diagnostics}), flush=True)
    import rclpy
    from rclpy.action import ActionClient
    from rclpy.parameter import Parameter
    from rclpy.node import Node
    from controller_manager_msgs.srv import ListHardwareComponents
    from rcl_interfaces.srv import GetParameters
    from geometry_msgs.msg import PoseWithCovarianceStamped
    from nav2_msgs.action import NavigateToPose
    from action_msgs.msg import GoalStatus
    from tf2_ros import Buffer, TransformListener, TransformException

    rclpy.init()
    node = Node('isolated_gazebo_mission_trial', parameter_overrides=[Parameter('use_sim_time', value=True)])
    active = {'handle': None, 'result': None}  # current Nav2 goal / 현재 Nav2 목표
    try:
        def wait(future, seconds):
            deadline = time.monotonic() + seconds
            while not future.done() and time.monotonic() < deadline and rclpy.ok():
                rclpy.spin_once(node, timeout_sec=0.1)
            return future.done()

        hardware = node.create_client(ListHardwareComponents, '/controller_manager/list_hardware_components')
        if not hardware.wait_for_service(timeout_sec=10):
            raise RuntimeError('simulated controller manager unavailable')
        future = hardware.call_async(ListHardwareComponents.Request())
        if not wait(future, 10) or future.result() is None:
            raise RuntimeError('cannot verify simulated hardware')
        components = future.result().component
        if len(components) != 1 or components[0].name != 'GazeboSimSystem' or components[0].state.label != 'active':
            raise RuntimeError('unexpected or inactive hardware component')
        if any(name == 'base_node' for name in node.get_node_names()):
            raise RuntimeError('physical base node present in test domain')
        params = node.create_client(GetParameters, '/bt_navigator/get_parameters')
        if not params.wait_for_service(timeout_sec=10):
            raise RuntimeError('navigator parameter service unavailable')
        request = GetParameters.Request()
        request.names = ['use_sim_time']
        future = params.call_async(request)
        if not wait(future, 10) or future.result() is None or not future.result().values[0].bool_value:
            raise RuntimeError('Nav2 is not using simulation time')
        start_clock = node.get_clock().now().nanoseconds
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and node.get_clock().now().nanoseconds <= start_clock:
            rclpy.spin_once(node, timeout_sec=0.1)
        if node.get_clock().now().nanoseconds <= start_clock:
            raise RuntimeError('simulation clock not advancing')
        print('verified: domain 31, localhost, GazeboSimSystem, Nav2 simulation time, advancing clock', flush=True)
        verify_gazebo_pose(resume)

        # Known Gazebo spawn pose; the earlier automatic scan match was not confident.
        # 한글: Gazebo의 알려진 시작 자세이며 자동 스캔 매칭은 신뢰도 기준을 통과하지 못했다.
        initial = node.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
        pose = PoseWithCovarianceStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = node.get_clock().now().to_msg()
        pose.pose.pose.position.x = 1.02
        pose.pose.pose.position.y = 0.37
        pose.pose.pose.orientation.z = math.sin(1.45 / 2)
        pose.pose.pose.orientation.w = math.cos(1.45 / 2)
        pose.pose.covariance[0] = pose.pose.covariance[7] = 0.01
        pose.pose.covariance[35] = 0.02
        deadline = time.monotonic() + 15
        while initial.get_subscription_count() == 0 and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=.1)
        if initial.get_subscription_count() == 0:
            raise RuntimeError('simulation AMCL initial-pose subscriber unavailable')
        # Wait for AMCL's map transform instead of sending a goal against an old pose.
        # 한글: 오래된 위치로 목표를 보내지 않도록 AMCL의 지도 변환을 기다린다.
        buffer = Buffer()
        listener = TransformListener(buffer, node)
        deadline = time.monotonic() + 40
        localized = False
        next_pose = 0.0
        while time.monotonic() < deadline:
            if not resume and time.monotonic() >= next_pose:
                pose.header.stamp = node.get_clock().now().to_msg()
                initial.publish(pose)
                next_pose = time.monotonic() + 1
            rclpy.spin_once(node, timeout_sec=.2)
            try:
                position = buffer.lookup_transform('map', 'base_footprint', rclpy.time.Time()).transform.translation
                expected_x, expected_y = (1.0, 1.45) if resume else (1.02, .37)
                if math.hypot(position.x - expected_x, position.y - expected_y) < (.30 if resume else .20):
                    localized = True
                    break
            except TransformException:
                pass
        if not localized:
            raise RuntimeError('simulation localization did not reach the expected starting pose')
        print(f'simulation localization: x={position.x:.2f} y={position.y:.2f}', flush=True)
        if '--prepare-only' in sys.argv:
            print('simulation preparation complete; no navigation goal sent', flush=True)
            return
        if stop_requested():
            emit('canceled', 'canceled_before_goal')
            return
        client = ActionClient(node, NavigateToPose, '/navigate_to_pose')
        if not client.wait_for_server(timeout_sec=15):
            raise RuntimeError('nav2_action_unavailable')
        if stop_requested():
            emit('canceled', 'canceled_before_goal')
            return
        legs = [(1.0, 1.45, math.pi / 2, 'gazebo_navigation')]
        if '--return' in sys.argv:
            # Out to the demo point, then back to the spawn pose (start point).
            # 한글: 시범 지점까지 갔다가 시작 지점(출발점)으로 돌아온다.
            legs.append((1.02, 0.37, 1.45, 'gazebo_returning'))
        def send(x, y, yaw):
            goal = NavigateToPose.Goal()
            goal.pose.header.frame_id = 'map'
            goal.pose.header.stamp = node.get_clock().now().to_msg()
            goal.pose.pose.position.x = x
            goal.pose.pose.position.y = y
            goal.pose.pose.orientation.z = math.sin(yaw / 2)
            goal.pose.pose.orientation.w = math.cos(yaw / 2)
            print(f'simulation goal: map x={x:.2f} y={y:.2f} yaw={yaw:.3f} rad', flush=True)
            future = client.send_goal_async(goal)
            if not wait(future, 15) or future.result() is None or not future.result().accepted:
                raise RuntimeError('simulated goal not accepted')
            active['handle'] = future.result()
            active['result'] = active['handle'].get_result_async()

        def cancel_active():
            if active['handle'] is not None and active['result'] is not None and not active['result'].done():
                wait(active['handle'].cancel_goal_async(), 5)
                wait(active['result'], 5)
            if active['result'] is None or not active['result'].done() or active['result'].result() is None:
                raise RuntimeError('simulation result or cancellation unconfirmed')

        def drive(x, y, yaw, stage):
            """Drive one leg; return (outcome, reason). Pausing cancels the goal but keeps it.

            한글: 한 구간을 주행한다. 일시정지는 목표를 취소하되 기억했다가 재개 시 다시 보낸다.
            """
            print('MISSION_STAGE ' + stage, flush=True)
            send(x, y, yaw)
            # Leg time is counted in simulation time: on a loaded Jetson Gazebo runs slower than
            # real time and wall-clock limits failed legs that were still progressing (2026-11-22).
            # 한글: 구간 시간은 시뮬레이션 시간으로 센다. 부하가 큰 Jetson에서는 Gazebo가 실시간보다 느려
            # 벽시계 제한이 진행 중인 주행을 실패로 만들었다(2026-11-22). 벽시계 10분은 안전 상한.
            def sim_now():
                return node.get_clock().now().nanoseconds / 1e9
            active_time, last, paused_at = 0.0, sim_now(), None
            wall_start = time.monotonic()
            next_report = 10
            occupied_retry = True
            while True:
                rclpy.spin_once(node, timeout_sec=.2)
                now = time.monotonic()
                sim = sim_now()
                if paused_at is None:
                    active_time += max(0.0, sim - last)
                last = sim
                command = read_command()
                if command == 'cancel':
                    print('simulation cancellation requested', flush=True)
                    if paused_at is None:
                        cancel_active()
                    return 'canceled', 'cancel_confirmed'
                if command == 'pause' and paused_at is None:
                    cancel_active()
                    paused_at = now
                    print('MISSION_STAGE gazebo_paused', flush=True)
                    continue
                if command == 'resume' and paused_at is not None:
                    paused_at = None
                    print('MISSION_STAGE ' + stage, flush=True)
                    send(x, y, yaw)
                    continue
                if paused_at is not None:
                    if now - paused_at > 120:
                        # A long pause ends the mission instead of resuming unexpectedly later.
                        # 한글: 오래 멈춘 임무는 나중에 갑자기 재개하지 않고 종료한다.
                        return 'canceled', 'pause_timeout'
                    continue
                if active_time >= next_report:
                    print(f'simulation running: {active_time:.0f} s', flush=True)
                    next_report += 10
                if active['result'].done():
                    result = active['result'].result()
                    print(f'action status={result.status} error_code={result.result.error_code} active={active_time:.1f}s', flush=True)
                    if result.status == GoalStatus.STATUS_SUCCEEDED and result.result.error_code == 0:
                        return 'succeeded', 'nav2_succeeded'
                    if (result.status == GoalStatus.STATUS_ABORTED and result.result.error_code == 205
                            and occupied_retry and active_time < 5):
                        # START_OCCUPIED right after sending: the costmap had not cleared the start
                        # area yet. Retry once. 한글: 시작 직후 START_OCCUPIED는 비용지도가 아직 정리되지
                        # 않은 경우라 한 번만 다시 보낸다.
                        occupied_retry = False
                        print('start reported occupied; retrying once in 3 s', flush=True)
                        deadline = time.monotonic() + 3
                        while time.monotonic() < deadline:
                            rclpy.spin_once(node, timeout_sec=.2)
                        send(x, y, yaw)
                        continue
                    if result.status == GoalStatus.STATUS_ABORTED:
                        return 'failed', 'nav2_aborted'
                    if result.status == GoalStatus.STATUS_CANCELED:
                        return 'failed', 'timeout_cancel_confirmed'
                    return 'interrupted', 'nav2_result_unknown'
                if active_time > (180 if managed else 90) or now - wall_start > 600:
                    print('simulation timed out; requesting cancel', flush=True)
                    cancel_active()
                    return 'failed', 'timeout_cancel_confirmed'

        outcome, reason = 'succeeded', 'nav2_succeeded'
        for x, y, yaw, stage in legs:
            outcome, reason = drive(x, y, yaw, stage)
            if outcome != 'succeeded':
                break
        if outcome == 'succeeded' and '--inspect' in sys.argv:
            from stack_light_observer import observe
            print('MISSION_STAGE gazebo_inspection', flush=True)
            observation = observe(node, stop_requested)
            if observation['status'] == 'observed':
                emit('succeeded', 'inspection_observed', observation['colors'])
            elif observation['status'] == 'canceled':
                emit('canceled', 'inspection_canceled')
            else:
                emit('failed', 'inspection_unconfirmed', diagnostics=observation.get('diagnostics'))
        elif outcome == 'succeeded' and '--return' in sys.argv:
            emit('succeeded', 'returned_to_start')
        else:
            emit(outcome, reason)
            if outcome == 'interrupted':
                raise RuntimeError('simulated navigation result uncertain')
            if outcome != 'succeeded' and not managed:
                raise RuntimeError('simulated navigation did not succeed')
    finally:
        goal_handle, goal_result = active['handle'], active['result']
        if goal_handle is not None and goal_result is not None and not goal_result.done():
            try:
                wait(goal_handle.cancel_goal_async(), 3)
            except Exception:
                pass
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        if '--managed' in sys.argv:
            known = ('gazebo_start_pose_mismatch', 'gazebo_pose_unavailable', 'nav2_action_unavailable')
            reason = str(exc) if str(exc) in known else 'gazebo_unavailable_or_unconfirmed'
            print('MISSION_RESULT ' + json.dumps({'state': 'interrupted', 'reason': reason}), flush=True)
        raise
