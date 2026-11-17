"""Check a standalone Gazebo camera fixture; no motion commands are sent.

한글: 독립 Gazebo 카메라 시험 월드를 확인하며 구동 명령은 보내지 않는다.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src/jetrover_perception/scripts'))
from stack_light import classify  # noqa: E402


def main():
    """Observe actual bridge images and report the fixture result. / 실제 브리지 영상으로 판정한다."""
    if (os.environ.get('ROS_DOMAIN_ID') != '31' or
            os.environ.get('ROS_AUTOMATIC_DISCOVERY_RANGE') != 'LOCALHOST' or
            os.environ.get('RMW_IMPLEMENTATION') != 'rmw_fastrtps_cpp'):
        raise RuntimeError('isolated ROS configuration required')
    if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1] not in ('off', 'blink', 'inverted')):
        raise ValueError('expected optional off, blink or inverted')
    mode = sys.argv[1] if len(sys.argv) == 2 else 'on'
    rclpy.init()
    node = Node('stack_light_fixture_check')
    frames = []
    stop = threading.Event()
    failures = []

    def switch_green():
        # Move a Gazebo-only visual, never a robot actuator.
        # 한글: Gazebo 시험 모형만 이동하며 실제 로봇 구동기는 제어하지 않는다.
        visible = mode != 'off'
        while not stop.is_set():
            y = 0 if visible else .3
            cmd = ['gz', 'service', '-s', '/world/stack_light_fixture/set_pose',
                   '--reqtype', 'gz.msgs.Pose', '--reptype', 'gz.msgs.Boolean',
                   '--timeout', '3000', '--req',
                   f'name: "green_on", position: {{x: 0.98, y: {y}, z: 0.85}}, orientation: {{w: 1}}']
            try:
                response = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=True)
                if 'data: true' not in response.stdout:
                    raise RuntimeError('Gazebo did not confirm pose change')
            except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
                failures.append(str(exc))
                stop.set()
                return
            if mode != 'blink':
                return
            visible = not visible
            stop.wait(.8)

    thread = threading.Thread(target=switch_green)
    thread.start()

    def receive(msg):
        now = time.monotonic()
        if frames and now - frames[-1][0] < .49:
            return
        if msg.encoding != 'rgb8' or msg.step != msg.width * 3:
            return
        image = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width, 3).copy()
        frames.append((now, image))

    node.create_subscription(Image, '/stack_test/image', receive, qos_profile_sensor_data)
    try:
        deadline = time.monotonic() + 30
        target_samples = 11 if mode == 'blink' else 7
        while len(frames) < target_samples and time.monotonic() < deadline and not failures:
            rclpy.spin_once(node, timeout_sec=.1)
        if failures:
            raise RuntimeError(failures[0])
        if len(frames) < target_samples:
            raise RuntimeError('insufficient camera frames')
        regions = {'red': (312, 84, 16, 16), 'yellow': (312, 172, 16, 16),
                   'green': (312, 260, 16, 16)}
        result = classify(frames, regions, time.monotonic())
        print(json.dumps({'result': result, 'rgb_centres': {
            key: frames[-1][1][y + 8, x + 8].tolist()
            for key, (x, y, _, _) in regions.items()}}, ensure_ascii=False))
        expected = ('off', 'on', 'on') if mode == 'inverted' else (
            'on', 'off', 'blinking' if mode == 'blink' else mode)
        if tuple(result[key]['state'] for key in regions) != expected:
            raise RuntimeError('fixture classification did not match known scene')
    finally:
        stop.set()
        thread.join(timeout=6)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
