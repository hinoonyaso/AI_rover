#!/usr/bin/python3
"""Capture a fresh measured arm pose without commanding any actuators.

한글: 액추에이터 명령 없이 최신 실측 팔 자세를 캡처한다.
"""
import json
import sys
import time
import rclpy
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener, TransformException
from static_mount import transform_matrix


def main():
    """Read the latest base-to-gripper transform and enforce timestamp freshness.

    한글: 최신 베이스-그리퍼 변환을 읽고 시각 신선도를 검사한다.
    """
    node = None
    try:
        rclpy.init(); node = Node('jetinspect_tcp_pose_capture')
        buffer = Buffer(); listener = TransformListener(buffer, node)
        end = time.monotonic() + 8
        while time.monotonic() < end:
            rclpy.spin_once(node, timeout_sec=.1)
            try:
                transform = buffer.lookup_transform('base_link', 'gripper_link', Time())
                stamp = transform.header.stamp.sec + transform.header.stamp.nanosec * 1e-9
                now = node.get_clock().now().nanoseconds * 1e-9
                if not 0 <= now - stamp < 2: continue
                print(json.dumps({'result':transform_matrix(transform.transform).tolist(), 'stamp':stamp}, allow_nan=False))
                return
            except TransformException:
                continue
        raise ValueError('arm_tf_unavailable')
    except (ValueError, RuntimeError) as exc:
        print(json.dumps({'error':str(exc)})); sys.exit(1)
    finally:
        if node is not None: node.destroy_node(); rclpy.shutdown()

if __name__ == '__main__': main()
