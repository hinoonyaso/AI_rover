#!/usr/bin/env python3
# 한글: 시뮬레이션 전용 "정답 위치 추정": Gazebo 정답 자세(로봇)와 EKF의 odom->base_footprint로 map->odom을 계산해 발행한다.
#       AMCL의 map->odom 발행은 꺼야 한다(`ros2 param set /amcl tf_broadcast false`). 주행 시험에서 위치 추정 오차를 빼고
#       플래너·컨트롤러·회피만 평가하기 위한 것이다. 실기에는 쓰지 않는다(실기는 AMCL). --noise로 위치 오차를 일부러 더할 수 있다.
"""Simulation-only localization from Gazebo ground truth (host, ROS_DOMAIN_ID=31).

map -> odom = T(world->base_footprint ground truth) * T(odom->base_footprint)^-1  (world == map)
Why: in the scan world AMCL drifts 12-24 cm after a rotation in place (tools/sim/amcl_drift_check.py, troubleshooting/046),
which hides the effect of the planner/controller settings under test. Turn AMCL's own broadcast off first:
  ros2 param set /amcl tf_broadcast false
Options: --noise SIGMA  adds a slowly varying position offset (m, random walk bounded to +-3 sigma) to emulate AMCL error.
"""
import argparse
import math
import os
import sys

from geometry_msgs.msg import TransformStamped
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
import tf2_ros

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import avoid_trials as T  # noqa: E402


def mat(x, y, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return np.array([[c, -s, x], [s, c, y], [0, 0, 1.0]])


class GtLoc(Node):
    def __init__(self, noise):
        super().__init__('gt_localization', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.buf = tf2_ros.Buffer()
        self.tfl = tf2_ros.TransformListener(self.buf, self)
        self.br = tf2_ros.TransformBroadcaster(self)
        self.gt = T.GroundTruth()
        self.noise, self.off = noise, np.zeros(2)
        self.rng = np.random.default_rng(1)
        self.create_timer(0.02, self.tick)
        self.n = 0

    def tick(self):
        g = self.gt.latest
        if g is None:
            return
        try:
            tr = self.buf.lookup_transform('odom', 'base_footprint', rclpy.time.Time())
        except Exception:  # noqa: BLE001
            return
        q = tr.transform.rotation
        yo = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        t_odom_base = mat(tr.transform.translation.x, tr.transform.translation.y, yo)
        if self.noise > 0:
            self.off = np.clip(self.off + self.rng.normal(0, self.noise * 0.02, 2), -3 * self.noise, 3 * self.noise)
        t_map_base = mat(g[1] + self.off[0], g[2] + self.off[1], g[3])
        t_map_odom = t_map_base @ np.linalg.inv(t_odom_base)
        m = TransformStamped()
        m.header.stamp = self.get_clock().now().to_msg()
        m.header.frame_id, m.child_frame_id = 'map', 'odom'
        m.transform.translation.x, m.transform.translation.y = float(t_map_odom[0, 2]), float(t_map_odom[1, 2])
        yaw = math.atan2(t_map_odom[1, 0], t_map_odom[0, 0])
        m.transform.rotation.z, m.transform.rotation.w = math.sin(yaw / 2), math.cos(yaw / 2)
        self.br.sendTransform(m)
        self.n += 1
        if self.n == 1:
            self.get_logger().info('publishing map->odom from Gazebo ground truth')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--noise', type=float, default=0.0, help='position error sigma (m), default 0')
    args = ap.parse_args()
    rclpy.init()
    node = GtLoc(args.noise)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.gt.stop()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
