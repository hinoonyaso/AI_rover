#!/usr/bin/env python3
"""Read-only simulation probe of the swept-disc candidate; never publishes commands.

한글: 원 궤적 후보를 시뮬레이션에서 관찰만 하며 구동 명령은 발행하지 않는다.
"""
import json
import math
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src/jetrover_navigation/scripts'))
from precise_guard_candidate import path_clear  # noqa: E402


def main():
    """Observe local costmap, TF, and navigation velocity in domain 31.

    한글: 격리된 31번 도메인에서 비용지도·TF·주행 속도를 관찰한다.
    """
    if os.environ.get('ROS_DOMAIN_ID') != '31':
        raise SystemExit('ROS_DOMAIN_ID=31 is required')
    import rclpy
    from geometry_msgs.msg import Twist
    from nav_msgs.msg import OccupancyGrid
    from rclpy.node import Node
    from rclpy.executors import ExternalShutdownException
    from tf2_ros import Buffer, TransformListener

    class Probe(Node):
        def __init__(self):
            super().__init__('precise_guard_probe')
            self.grid = None
            self.cmd = None
            self.buffer = Buffer()
            self.listener = TransformListener(self.buffer, self)
            self.create_subscription(OccupancyGrid, '/local_costmap/costmap', self.on_grid, 10)
            self.create_subscription(Twist, '/cmd_vel_nav', self.on_cmd, 10)
            self.create_timer(1.0, self.observe)

        def on_grid(self, msg):
            self.grid = (time.monotonic(), msg)

        def on_cmd(self, msg):
            self.cmd = (time.monotonic(), msg)

        def observe(self):
            # Diagnostic bounds only: no stopping-distance or sensor-freshness guarantee.
            # 한글: 진단용 한계일 뿐 정지거리와 센서 최신성을 보장하지 않는다.
            record = {'wall_s': time.time(), 'state': 'unavailable'}
            now = time.monotonic()
            if not self.grid or not self.cmd:
                print(json.dumps(record), flush=True)
                return
            gt, m = self.grid
            ct, c = self.cmd
            record.update(grid_age_s=round(now - gt, 3), cmd_age_s=round(now - ct, 3))
            if now - gt > 2.0 or now - ct > 1.0:
                record['state'] = 'stale'
                print(json.dumps(record), flush=True)
                return
            try:
                t = self.buffer.lookup_transform(m.header.frame_id, 'base_footprint', rclpy.time.Time())
            except Exception:
                print(json.dumps(record), flush=True)
                return
            q, o = t.transform.rotation, m.info.origin
            if abs(o.orientation.z) > 1e-8 or abs(o.orientation.w - 1.0) > 1e-8:
                record['state'] = 'rotated_grid_unsupported'
                print(json.dumps(record), flush=True)
                return
            yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
            x, y = t.transform.translation.x, t.transform.translation.y
            vx = math.cos(yaw) * c.linear.x - math.sin(yaw) * c.linear.y
            vy = math.sin(yaw) * c.linear.x + math.cos(yaw) * c.linear.y
            # Illustrative radius and horizon, not validated safety settings.
            # 한글: 반경과 지평은 예시이며 안전 설정으로 검증되지 않았다.
            clear = path_clear(list(m.data), m.info.width, m.info.height, m.info.resolution,
                               (o.position.x, o.position.y), (x, y), (x + vx, y + vy), 0.30)
            record.update(state='clear' if clear else 'blocked', speed=round(math.hypot(vx, vy), 4))
            print(json.dumps(record), flush=True)

    rclpy.init()
    node = Probe()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
