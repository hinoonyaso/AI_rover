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
    if (any(arg not in ('--resume', '--managed', '--inspect', '--prepare-only') for arg in sys.argv[1:]) or
            len(set(sys.argv[1:])) != len(sys.argv[1:]) or
            ('--prepare-only' in sys.argv and len(sys.argv) != 2)):
        raise ValueError('unsupported or duplicate option')
    resume = '--resume' in sys.argv[1:]
    managed = '--managed' in sys.argv[1:]
    def stop_requested():
        if not managed:
            return False
        ready, _, _ = select.select([sys.stdin], [], [], 0)
        return bool(ready)
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
    handle = None
    result_future = None
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
        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = node.get_clock().now().to_msg()
        goal.pose.pose.position.x = 1.0
        goal.pose.pose.position.y = 1.45
        goal.pose.pose.orientation.z = math.sin(math.pi / 4)
        goal.pose.pose.orientation.w = math.cos(math.pi / 4)
        print('simulation goal: map x=1.00 y=1.45 yaw=1.571 rad', flush=True)
        future = client.send_goal_async(goal)
        if not wait(future, 15) or future.result() is None or not future.result().accepted:
            raise RuntimeError('simulated goal not accepted')
        handle = future.result()
        result_future = handle.get_result_async()
        started = time.monotonic()
        next_report = started + 10
        canceled_by_user = False
        while not result_future.done() and time.monotonic() - started < (180 if managed else 90):
            rclpy.spin_once(node, timeout_sec=.2)
            if stop_requested():
                canceled_by_user = True
                break
            if time.monotonic() >= next_report:
                print(f'simulation running: {time.monotonic() - started:.0f} s', flush=True)
                next_report += 10
        if not result_future.done():
            print('simulation cancellation requested' if canceled_by_user else 'simulation timed out; requesting cancel', flush=True)
            cancel = handle.cancel_goal_async()
            wait(cancel, 5)
            wait(result_future, 5)
        if not result_future.done() or result_future.result() is None:
            raise RuntimeError('simulation result or cancellation unconfirmed')
        result = result_future.result()
        print(f'action status={result.status} error_code={result.result.error_code} elapsed={time.monotonic() - started:.1f}s', flush=True)
        if result.status == GoalStatus.STATUS_SUCCEEDED and result.result.error_code == 0:
            if '--inspect' not in sys.argv:
                emit('succeeded', 'nav2_succeeded')
            else:
                from stack_light_observer import observe
                print('MISSION_STAGE gazebo_inspection', flush=True)
                observation = observe(node, stop_requested)
                if observation['status'] == 'observed':
                    emit('succeeded', 'inspection_observed', observation['colors'])
                elif observation['status'] == 'canceled':
                    emit('canceled', 'inspection_canceled')
                else:
                    emit('failed', 'inspection_unconfirmed', diagnostics=observation.get('diagnostics'))
        elif result.status == GoalStatus.STATUS_CANCELED:
            emit('canceled' if canceled_by_user else 'failed', 'cancel_confirmed' if canceled_by_user else 'timeout_cancel_confirmed')
            if not managed:
                raise RuntimeError('simulated navigation was canceled')
        elif result.status == GoalStatus.STATUS_ABORTED:
            emit('failed', 'nav2_aborted')
            if not managed:
                raise RuntimeError('simulated navigation failed')
        else:
            emit('interrupted', 'nav2_result_unknown')
            raise RuntimeError('simulated navigation result uncertain')
    finally:
        if handle is not None and result_future is not None and not result_future.done():
            try:
                cancellation = handle.cancel_goal_async()
                wait(cancellation, 3)
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
