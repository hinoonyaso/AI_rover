#!/usr/bin/python3
"""Read only the isolated Gazebo map transform. / 격리 Gazebo 지도 좌표만 읽는다."""
import json
import math
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'mission'))
from gazebo_nav_trial import require_simulation


def track_clock(previous, seen_at, current, wall_now):
    """Track advancing or reset simulation time. / 진행 또는 초기화된 시뮬레이션 시각을 추적한다."""
    if current < previous:
        return current, 0.0
    if current > previous:
        return current, wall_now
    return previous, seen_at


def main():
    """Publish fresh simulation pose snapshots to a private file. / 최신 시뮬레이션 위치를 전용 파일에 기록한다."""
    require_simulation()
    import rclpy
    from rclpy.node import Node
    from rclpy.parameter import Parameter
    from tf2_ros import Buffer, TransformException, TransformListener

    rclpy.init()
    node = Node('jetinspect_gazebo_pose_monitor', parameter_overrides=[Parameter('use_sim_time', value=True)])
    # Bind TF's clock jump callback to simulation time, not wall time.
    # 한글: TF 시간 역행 콜백을 벽시계가 아닌 시뮬레이션 시계에 연결한다.
    buffer = Buffer(node=node)
    listener = TransformListener(buffer, node)
    directory = Path.home() / '.local/share/jetinspect-ops/run'
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    last_clock = 0
    clock_seen = 0.0
    next_write = 0.0
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.3)
            now_clock = node.get_clock().now().nanoseconds
            last_clock, clock_seen = track_clock(last_clock, clock_seen, now_clock, time.monotonic())
            if time.monotonic() < next_write:
                continue
            next_write = time.monotonic() + 1.0
            try:
                transform = buffer.lookup_transform('map', 'base_footprint', rclpy.time.Time())
                p = transform.transform.translation
                q = transform.transform.rotation
                stamp = transform.header.stamp.sec * 1_000_000_000 + transform.header.stamp.nanosec
                if (not now_clock or time.monotonic() - clock_seen > 3 or not 0 <= now_clock - stamp < 3_000_000_000 or
                        not all(math.isfinite(v) for v in (p.x, p.y, q.z, q.w))):
                    continue
                output = {'timestamp': time.time(), 'source': 'gazebo', 'frame': 'map',
                          'x': p.x, 'y': p.y, 'yaw': math.atan2(2*q.w*q.z, 1-2*q.z*q.z)}
                temp = directory / 'gazebo-pose.tmp'
                temp.write_text(json.dumps(output))
                os.replace(temp, directory / 'gazebo-pose.json')
            except (TransformException, OSError):
                continue
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
