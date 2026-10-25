#!/usr/bin/env python3
# 한글: 로봇을 손으로 출발점(또는 다른 지도 좌표)에 놓을 때, 지금 위치(AMCL, map→base_footprint)가 목표에서 얼마나 어긋났는지
#       로봇 기준(앞/오른쪽 cm, 방향 도)으로 2 Hz 출력한다. 모터 명령은 보내지 않는다. 실기 시험 출발 표시 붙이기용(2026-10-25).
"""Print how far the robot is from a map pose, in the robot's own frame, while it is placed by hand (no motor commands).

  python3 tools/nav/start_guide.py                 # S = (1.05, 0.10, 90 deg), the benchmark start
  python3 tools/nav/start_guide.py 1.05 0.60 90    # e.g. where the box goes (S + 0.5 m)
Needs robot.launch.py + localization (AMCL) running. "forward +12 cm" means: push the robot 12 cm forward.
A robot that is lifted and put down does not move its wheels, so AMCL does not see the move: after placing it, re-localize with
  ros2 run jetrover_navigation scan_match_init.py --near 1.05 0.10 --near-radius 0.5
and read the guide again. 한글: 들어서 옮기면 바퀴가 안 돌아 AMCL이 모른다 → 놓을 때마다 스캔 매칭으로 다시 잡고 본다.
"""
import math
import sys

import rclpy
from rclpy.node import Node
import tf2_ros


def main():
    gx, gy, gyaw = (float(v) for v in sys.argv[1:4]) if len(sys.argv) >= 4 else (1.05, 0.10, 90.0)
    rclpy.init()
    node = Node('start_guide')
    buf = tf2_ros.Buffer()
    tf2_ros.TransformListener(buf, node)

    def tick():
        try:
            t = buf.lookup_transform('map', 'base_footprint', rclpy.time.Time())
        except Exception:  # noqa: BLE001
            print('waiting for map -> base_footprint (is AMCL localized?)', flush=True)
            return
        q = t.transform.rotation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        dx, dy = gx - t.transform.translation.x, gy - t.transform.translation.y
        # 로봇 기준: 앞(+), 왼쪽(+) / robot frame: forward +, left +
        fwd = math.cos(yaw) * dx + math.sin(yaw) * dy
        left = -math.sin(yaw) * dx + math.cos(yaw) * dy
        dyaw = math.degrees(math.atan2(math.sin(math.radians(gyaw) - yaw), math.cos(math.radians(gyaw) - yaw)))
        ok = math.hypot(dx, dy) < 0.03 and abs(dyaw) < 3.0
        print(f'move: forward {fwd * 100:+5.1f} cm   right {-left * 100:+5.1f} cm   turn {"left" if dyaw > 0 else "right"} '
              f'{abs(dyaw):4.1f} deg   {"<== OK (within 3 cm, 3 deg)" if ok else ""}', flush=True)

    node.create_timer(0.5, tick)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
