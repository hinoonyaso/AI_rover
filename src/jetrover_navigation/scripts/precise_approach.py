#!/usr/bin/env python3
# 한글: 정밀 접근 — Nav2가 목표 근처(0.25 m 이내)까지 온 뒤, 메카넘 전방향 이동으로 마지막 위치·방향 오차를 맞춘다.
#       NavigateToPose와 같은 액션 인터페이스(`precise_approach`)로 목표(map 프레임)를 받고,
#       저속(0.06 m/s 이하)으로 /cmd_vel_nav에 명령을 낸다. 속도 평활기와 충돌 감시기를 그대로 거치므로 안전망이 유지된다.
#       위치는 TF의 map->base_footprint를 믿는다(실기는 AMCL).
"""
Precise final approach for the mecanum base.

checklist 8.15 task 4, prd/sim-avoidance-precision.md.

Goal: NavigateToPose action `precise_approach` (map frame pose). The robot moves in x, y and
yaw at once with a small proportional controller until the position error is below pos_tol
(0.02 m) and the yaw error below yaw_tol (2 deg) for hold_s (0.4 s). Commands go to
/cmd_vel_nav (-> velocity smoother -> collision monitor -> /cmd_vel), so the safety net stays
in the loop. A goal farther than max_start_dist (0.30 m) is rejected: this is a last-few-cm
tool, not a planner. Aborted on timeout (time_limit_s 20) or when the pose TF is stale.
Its accuracy is limited by the localization (AMCL error).
"""
import math
import time

pi = math.pi


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


def approach_command(ex, ey, eyaw, v_max=0.06, v_min=0.025, w_max=0.25, w_min=0.08,
                     gain=1.2, yaw_gain=1.2, pos_tol=0.02, yaw_tol=math.radians(2.0)):
    """
    Body-frame velocity command (vx, vy, wz) toward the error (ex, ey) m and eyaw rad.

    Proportional with saturation at v_max / w_max and a floor v_min / w_min so the wheels keep
    turning while the error is above its tolerance; zero inside the tolerances.
    한글: 비례 제어 + 상·하한. 허용 오차 안이면 0.
    """
    dist = math.hypot(ex, ey)
    vx = vy = 0.0
    if dist > pos_tol:
        speed = min(v_max, max(v_min, gain * dist))
        speed = min(speed, dist / 0.5)    # never cover more than the remaining distance in 0.5 s
        vx, vy = speed * ex / dist, speed * ey / dist
    wz = 0.0
    if abs(eyaw) > yaw_tol:
        w = min(w_max, max(w_min, yaw_gain * abs(eyaw)))
        wz = math.copysign(w, eyaw)
    return vx, vy, wz


def body_error(robot, goal):
    """Goal minus robot pose in the robot frame: (ex, ey, eyaw); poses (x, y, yaw) in map."""
    dx, dy = goal[0] - robot[0], goal[1] - robot[1]
    c, s = math.cos(robot[2]), math.sin(robot[2])
    return c * dx + s * dy, -s * dx + c * dy, wrap(goal[2] - robot[2])


def main():
    import rclpy
    from geometry_msgs.msg import Twist
    from nav2_msgs.action import NavigateToPose
    from rclpy.action import ActionServer, CancelResponse, GoalResponse
    from rclpy.node import Node
    import tf2_ros

    class PreciseApproach(Node):
        def __init__(self):
            super().__init__('precise_approach')
            gp = self.declare_parameter
            self.pos_tol = float(gp('pos_tol_m', 0.02).value)
            self.yaw_tol = math.radians(float(gp('yaw_tol_deg', 2.0).value))
            self.hold_s = float(gp('hold_s', 0.4).value)
            self.v_max = float(gp('v_max', 0.06).value)
            self.v_min = float(gp('v_min', 0.025).value)
            self.w_max = float(gp('w_max', 0.25).value)
            self.w_min = float(gp('w_min', 0.08).value)
            self.time_limit = float(gp('time_limit_s', 20.0).value)
            self.max_start = float(gp('max_start_dist_m', 0.30).value)
            self.rate = float(gp('rate_hz', 20.0).value)
            self.frame = gp('global_frame', 'map').value
            self.base = gp('base_frame', 'base_footprint').value
            self.cmd_topic = gp('cmd_vel_topic', '/cmd_vel_nav').value
            self.buf = tf2_ros.Buffer()
            self.tfl = tf2_ros.TransformListener(self.buf, self)
            self.pub = self.create_publisher(Twist, self.cmd_topic, 10)
            self.server = ActionServer(
                self, NavigateToPose, 'precise_approach', self.execute,
                goal_callback=self.on_goal, cancel_callback=lambda _: CancelResponse.ACCEPT)
            self.get_logger().info(
                f'precise approach ready: tol {self.pos_tol} m / {math.degrees(self.yaw_tol):.1f} '
                f'deg, v <= {self.v_max} m/s, {self.cmd_topic}')

        def pose(self):
            try:
                t = self.buf.lookup_transform(self.frame, self.base, rclpy.time.Time())
            except Exception:  # noqa: BLE001
                return None
            stamp = rclpy.time.Time.from_msg(t.header.stamp)
            age = (self.get_clock().now() - stamp).nanoseconds * 1e-9
            if age > 1.0:
                return None
            q = t.transform.rotation
            return (t.transform.translation.x, t.transform.translation.y,
                    math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z)))

        def goal_pose(self, goal):
            p = goal.pose.pose
            q = p.orientation
            yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
            return (p.position.x, p.position.y, yaw)

        def on_goal(self, req):
            robot = self.pose()
            if robot is None:
                self.get_logger().warn('rejected: no fresh pose TF')
                return GoalResponse.REJECT
            ex, ey, _ = body_error(robot, self.goal_pose(req))
            if math.hypot(ex, ey) > self.max_start:
                dist = math.hypot(ex, ey)
                self.get_logger().warn(f'rejected: goal {dist:.2f} m away (> {self.max_start} m)')
                return GoalResponse.REJECT
            return GoalResponse.ACCEPT

        def stop(self):
            for _ in range(3):
                self.pub.publish(Twist())

        def execute(self, handle):
            goal = self.goal_pose(handle.request)
            result = NavigateToPose.Result()
            t0, in_tol_since = time.monotonic(), None
            period = 1.0 / self.rate
            while rclpy.ok():
                if handle.is_cancel_requested:
                    self.stop()
                    handle.canceled()
                    return result
                if time.monotonic() - t0 > self.time_limit:
                    self.stop()
                    self.get_logger().warn('timeout')
                    handle.abort()
                    return result
                robot = self.pose()
                if robot is None:
                    self.stop()
                    self.get_logger().warn('pose TF stale: abort')
                    handle.abort()
                    return result
                ex, ey, eyaw = body_error(robot, goal)
                fb = NavigateToPose.Feedback()
                fb.distance_remaining = float(math.hypot(ex, ey))
                handle.publish_feedback(fb)
                if math.hypot(ex, ey) <= self.pos_tol and abs(eyaw) <= self.yaw_tol:
                    in_tol_since = in_tol_since or time.monotonic()
                    if time.monotonic() - in_tol_since >= self.hold_s:
                        self.stop()
                        handle.succeed()
                        return result
                else:
                    in_tol_since = None
                vx, vy, wz = approach_command(
                    ex, ey, eyaw, self.v_max, self.v_min, self.w_max, self.w_min,
                    pos_tol=self.pos_tol, yaw_tol=self.yaw_tol)
                m = Twist()
                m.linear.x, m.linear.y, m.angular.z = vx, vy, wz
                self.pub.publish(m)
                time.sleep(period)
            return result

    rclpy.init()
    node = PreciseApproach()
    from rclpy.executors import MultiThreadedExecutor
    ex = MultiThreadedExecutor()
    ex.add_node(node)
    try:
        ex.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
