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
in the loop. A goal farther than max_start_dist (0.30 m) is aborted (START_TOO_FAR): this is a
last-few-cm tool, not a planner. Aborted on timeout (time_limit_s 20, TIMEOUT) or when the pose TF
is stale (POSE_LOST); the result's error_code / error_msg carry the reason (9.4, 2026-10-28).
Its accuracy is limited by the localization (AMCL error).

Relocalize (2026-10-25, troubleshooting/055, default on): on the real robot AMCL
under-reports motion by 5-7 %, so the robot stopped 8-9 cm past the goal although AMCL
said 1.5 cm. Before approaching, the node waits until /odom says the robot stands still,
runs scan_match_init.py near the current pose (radius relocalize_radius_m) and, when the
match is confident, AMCL is reset to it (/initialpose). Straight 1.00 m x3 then ended
0.98 m by tape. Off in the simulator (ground-truth localization).
한글: 접근 전 스캔 매칭으로 AMCL 재위치(실기 +8~9 cm -> -2 cm). sim은 끈다.
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


# 실패 이유 코드(결과 error_code, 2026-10-28 체크리스트 9.4). NavigateToPose는 NONE=0만 정의해서 9100번대를 따로 쓴다.
# Failure reasons in the result error_code (NavigateToPose defines only NONE=0; 9100+ are ours).
START_TOO_FAR = 9101   # 목표가 너무 멂 / goal beyond max_start_dist
TIMEOUT = 9102         # time_limit 안에 허용 오차에 못 들어옴 / not within tolerance before time_limit
POSE_LOST = 9103       # map->base TF가 없거나 오래됨 / pose TF missing or stale
PATH_BLOCKED = 9104    # 시뮬레이션 검사: 경로 차단 / simulation guard: path blocked
GUARD_UNAVAILABLE = 9105  # 시뮬레이션 검사: 입력 무효 / simulation guard: invalid input


def scan_match_published(text):
    """Return (published, (x, y, yaw_deg) or None) from scan_match_init.py output.

    한글: 스캔 매칭이 /initialpose를 냈는지.
    """
    import re
    r = re.search(r'published /initialpose \(([-\d.]+), ([-\d.]+), ([-\d.]+)deg\)', text)
    if not r:
        return False, None
    return True, tuple(float(v) for v in r.groups())


def body_error(robot, goal):
    """Goal minus robot pose in the robot frame: (ex, ey, eyaw); poses (x, y, yaw) in map."""
    dx, dy = goal[0] - robot[0], goal[1] - robot[1]
    c, s = math.cos(robot[2]), math.sin(robot[2])
    return c * dx + s * dy, -s * dx + c * dy, wrap(goal[2] - robot[2])


def main():
    import rclpy
    import subprocess
    from geometry_msgs.msg import Twist
    from nav2_msgs.action import NavigateToPose
    from nav_msgs.msg import OccupancyGrid, Odometry
    from rclpy.callback_groups import ReentrantCallbackGroup
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
            # 접근 전 스캔 매칭 재위치(docstring) / scan-match relocalize before approaching
            self.relocalize = bool(gp('relocalize', True).value)
            self.reloc_radius = float(gp('relocalize_radius_m', 0.3).value)
            self.reloc_timeout = float(gp('relocalize_timeout_s', 60.0).value)
            # Experimental guard is opt-in and must never run on the real robot.
            # 한글: 실험 검사는 명시적으로 켜야 하며 실제 로봇에서는 실행하지 않는다.
            import os
            self.sim_guard = bool(gp('sim_guard_enabled', False).value)
            self.guard_radius = float(gp('sim_guard_radius_m', 0.30).value)
            self.guard_wall_age = float(gp('sim_guard_max_wall_age_s', 8.0).value)
            self.guard_ros_age = float(gp('sim_guard_max_ros_age_s', 1.5).value)
            self.guard_grid = None
            if self.sim_guard:
                if (not self.get_parameter('use_sim_time').value or
                        os.environ.get('ROS_DOMAIN_ID') != '31'):
                    raise RuntimeError('sim guard requires use_sim_time and ROS_DOMAIN_ID=31')
                if not all(math.isfinite(v) and v > 0.0 for v in
                           (self.guard_radius, self.guard_wall_age, self.guard_ros_age)):
                    raise ValueError('sim guard radius and age limits must be finite and positive')
                from precise_guard_candidate import path_clear
                self.path_clear = path_clear
                self.guard_group = ReentrantCallbackGroup()
                self.create_subscription(
                    OccupancyGrid, '/local_costmap/costmap', self.on_guard_grid,
                    10, callback_group=self.guard_group)
            self.speed = None            # latest /odom planar speed / 최근 /odom 속도
            self.create_subscription(Odometry, 'odom', self.on_odom, 10)
            self.buf = tf2_ros.Buffer()
            self.tfl = tf2_ros.TransformListener(self.buf, self)
            self.pub = self.create_publisher(Twist, self.cmd_topic, 10)
            self.server = ActionServer(
                self, NavigateToPose, 'precise_approach', self.execute,
                goal_callback=self.on_goal, cancel_callback=lambda _: CancelResponse.ACCEPT)
            self.get_logger().info(
                f'precise approach ready: tol {self.pos_tol} m / {math.degrees(self.yaw_tol):.1f} '
                f'deg, v <= {self.v_max} m/s, {self.cmd_topic}, '
                f'relocalize {self.relocalize}')

        def on_guard_grid(self, msg):
            # Atomic reference swap keeps the message and receipt time together.
            # 한글: 메시지와 수신 시각을 함께 교체해 같은 스냅샷으로 사용한다.
            self.guard_grid = (time.monotonic(), msg)

        def guard_check(self, goal):
            """
            Return (code, reason), failing closed on unavailable simulation data.

            한글: 시뮬레이션 입력이 유효하지 않으면 실패 코드와 이유를 반환한다.
            """
            sample = self.guard_grid
            if sample is None or time.monotonic() - sample[0] > self.guard_wall_age:
                return GUARD_UNAVAILABLE, 'guard costmap missing or stale by receipt time'
            m = sample[1]
            try:
                stamp = rclpy.time.Time.from_msg(m.header.stamp)
                age = (self.get_clock().now() - stamp).nanoseconds * 1e-9
                if age < -0.1 or age > self.guard_ros_age or not m.header.frame_id:
                    return GUARD_UNAVAILABLE, 'guard costmap stamp or frame invalid'
                q = m.info.origin.orientation
                if (not all(math.isfinite(v) for v in (q.x, q.y, q.z, q.w)) or
                        abs(q.x) > 1e-8 or abs(q.y) > 1e-8 or abs(q.z) > 1e-8 or
                        abs(q.w - 1.0) > 1e-8):
                    return GUARD_UNAVAILABLE, 'rotated or invalid costmap unsupported'
                base = self.buf.lookup_transform(m.header.frame_id, self.base, rclpy.time.Time())
                transform = self.buf.lookup_transform(
                    m.header.frame_id, self.frame, rclpy.time.Time())
                for t in (base, transform):
                    delta = self.get_clock().now() - rclpy.time.Time.from_msg(t.header.stamp)
                    tf_age = delta.nanoseconds * 1e-9
                    if tf_age < -0.1 or tf_age > 1.0:
                        return GUARD_UNAVAILABLE, 'guard transform stale'
                tq = transform.transform.rotation
                yaw = math.atan2(2 * (tq.w * tq.z + tq.x * tq.y),
                                 1 - 2 * (tq.y * tq.y + tq.z * tq.z))
                trans = transform.transform.translation
                gx = trans.x + math.cos(yaw) * goal[0] - math.sin(yaw) * goal[1]
                gy = trans.y + math.sin(yaw) * goal[0] + math.cos(yaw) * goal[1]
                pos = base.transform.translation
                origin = m.info.origin.position
                ok = self.path_clear(m.data, m.info.width, m.info.height, m.info.resolution,
                                     (origin.x, origin.y), (pos.x, pos.y), (gx, gy),
                                     self.guard_radius)
                if not ok:
                    return PATH_BLOCKED, 'guard path blocked, unknown, out of bounds, or malformed'
                return 0, ''
            except Exception as exc:  # noqa: BLE001
                return GUARD_UNAVAILABLE, f'guard data or TF error: {exc}'

        def on_odom(self, m):
            t = m.twist.twist
            self.speed = (time.monotonic(), math.hypot(t.linear.x, t.linear.y), abs(t.angular.z))

        def wait_stopped(self, hold=0.5, limit=3.0):
            """Return True once /odom was fresh and below 0.01 m/s, 0.02 rad/s for hold s.

            한글: 정지 확인.
            """
            t0, since = time.monotonic(), None
            while time.monotonic() - t0 < limit:
                s = self.speed
                fresh = s is not None and time.monotonic() - s[0] < 0.5
                ok = fresh and s[1] < 0.01 and s[2] < 0.02
                since = (since or time.monotonic()) if ok else None
                if since and time.monotonic() - since >= hold:
                    return True
                time.sleep(0.05)
            return False

        def relocalize_now(self):
            """Scan-match near the current pose (AMCL takes a confident result); return a log."""
            robot = self.pose()
            if robot is None:
                return 'no pose'
            if not self.wait_stopped():
                return 'not stopped: skipped'
            try:
                cmd = ['ros2', 'run', 'jetrover_navigation', 'scan_match_init.py',
                       '--near', '%.3f' % robot[0], '%.3f' % robot[1],
                       '--near-radius', str(self.reloc_radius)]
                rc = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=self.reloc_timeout)
            except subprocess.TimeoutExpired:
                return 'scan matching timed out'
            ok, pose = scan_match_published(rc.stdout + rc.stderr)
            if not ok:
                return 'not confident: kept AMCL'
            time.sleep(2.0)       # AMCL takes /initialpose and republishes TF / AMCL 반영 대기
            after = self.pose()
            shift = (math.hypot(after[0] - robot[0], after[1] - robot[1])
                     if after else float('nan'))
            return (f'AMCL reset to ({pose[0]:.2f}, {pose[1]:.2f}, {pose[2]:.0f} deg), '
                    f'moved {shift * 100:.1f} cm')

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
            # 먼 목표도 받아서 execute에서 이유 코드와 함께 중단(거부하면 BT가 이유를 모름)
            # Far goals are aborted with START_TOO_FAR; rejection carries no reason.
            return GoalResponse.ACCEPT

        def stop(self):
            # 종료 중(컨텍스트 무효)에는 발행할 수 없다 / cannot publish after the context is shut down
            if not rclpy.ok():
                return
            for _ in range(3):
                self.pub.publish(Twist())

        def fail(self, handle, result, code, msg):
            """Stop, log and abort with a reason code. 한글: 멈추고 이유 코드와 함께 중단."""
            self.stop()
            self.get_logger().warn(msg)
            result.error_code, result.error_msg = code, msg
            handle.abort()
            return result

        def execute(self, handle):
            goal = self.goal_pose(handle.request)
            result = NavigateToPose.Result()
            robot = self.pose()
            if robot is None:
                return self.fail(handle, result, POSE_LOST, 'pose TF stale')
            ex, ey, _ = body_error(robot, goal)
            if math.hypot(ex, ey) > self.max_start + (0.10 if self.relocalize else 0.0):
                # AMCL may shift 8–9 cm on relocalization; allow 0.10 m before it.
                # 한글: 재위치 전에는 AMCL 이동을 고려해 0.10 m 더 허용한다.
                return self.fail(handle, result, START_TOO_FAR,
                                 f'goal {math.hypot(ex, ey):.2f} m away (> {self.max_start} m)')
            if self.relocalize:
                self.stop()
                self.get_logger().info('relocalize: ' + self.relocalize_now())
                robot = self.pose()
                if robot is not None:
                    ex, ey, _ = body_error(robot, goal)
                    # 재위치 뒤 목표가 너무 멀면 계획기 몫 / far goals are the planner's job
                    dist = math.hypot(ex, ey)
                    if dist > self.max_start + 0.10:
                        return self.fail(handle, result, START_TOO_FAR,
                                         f'after relocalize the goal is {dist:.2f} m away')
            t0, in_tol_since = time.monotonic(), None
            period = 1.0 / self.rate
            while rclpy.ok():
                if handle.is_cancel_requested:
                    self.stop()
                    handle.canceled()
                    return result
                if time.monotonic() - t0 > self.time_limit:
                    return self.fail(
                        handle, result, TIMEOUT, f'not within tolerance after {self.time_limit} s')
                robot = self.pose()
                if robot is None:
                    return self.fail(handle, result, POSE_LOST, 'pose TF stale')
                if self.sim_guard:
                    code, message = self.guard_check(goal)
                    if code:
                        return self.fail(handle, result, code, message)
                ex, ey, eyaw = body_error(robot, goal)
                fb = NavigateToPose.Feedback()
                fb.distance_remaining = float(math.hypot(ex, ey))
                handle.publish_feedback(fb)
                if math.hypot(ex, ey) <= self.pos_tol and abs(eyaw) <= self.yaw_tol:
                    in_tol_since = in_tol_since or time.monotonic()
                    if time.monotonic() - in_tol_since >= self.hold_s:
                        self.stop()
                        # 성공 기록(BT가 정말 불렀는지 로그로 확인) / log success so BT calls are visible
                        self.get_logger().info(
                            f'succeeded: err {math.hypot(ex, ey) * 100:.1f} cm / '
                            f'{math.degrees(eyaw):.1f} deg in {time.monotonic() - t0:.1f} s')
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
