#!/usr/bin/env python3
"""MoveIt FollowJointTrajectory -> jetrover_base `arm/command_timed` bridge.

한글: MoveIt이 보내는 궤적(FollowJointTrajectory 액션)을 받아 일정 간격(기본 0.2 s)으로 다시 샘플링하고,
점마다 `arm/command_timed`(JointTrajectory 1점, time_from_start = 이동 시간)로 base_node에 보낸다.
base_node가 스텝 제한(arm_max_step_rad)과 펄스 클램프(100~900)를 한 번 더 걸러 준다(이중 안전).

English: receives MoveIt trajectories, resamples them at a fixed period and streams them one point at a
time to base_node. base_node still enforces its own step limit and pulse clamp (two independent guards).

The bridge refuses to start moving unless the arm is where the trajectory says it starts, and it stops
(holds the current pose) when the arm stops following, on cancel, or on a stale /joint_states.
"""
import math
import threading
import time

import rclpy
from control_msgs.action import FollowJointTrajectory
from diagnostic_msgs.msg import DiagnosticArray
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

Result = FollowJointTrajectory.Result


def point_time(pt):
    """한글: 궤적 점의 time_from_start를 초로. / time_from_start in seconds."""
    return pt.time_from_start.sec + pt.time_from_start.nanosec * 1e-9


def interpolate(times, positions, t):
    """Linear interpolation of a list of position vectors at time t (clamped to the ends).
    한글: 점 사이를 선형 보간한다. 범위 밖이면 양 끝 값."""
    if t <= times[0]:
        return list(positions[0])
    if t >= times[-1]:
        return list(positions[-1])
    for k in range(1, len(times)):
        if t <= times[k]:
            span = times[k] - times[k - 1]
            a = 0.0 if span <= 0.0 else (t - times[k - 1]) / span
            return [p0 + a * (p1 - p0) for p0, p1 in zip(positions[k - 1], positions[k])]
    return list(positions[-1])


def resample(times, positions, period):
    """Samples [(t, vector)] at t = period, 2*period, ... and always ends exactly at the last point.
    한글: period 간격으로 다시 샘플링. 마지막 점은 항상 정확히 포함."""
    total = times[-1]
    out = []
    k = 1
    while k * period < total - 1e-9:
        out.append((k * period, interpolate(times, positions, k * period)))
        k += 1
    out.append((total, list(positions[-1])))
    return out


def validate_plan(start, samples, limits, max_step):
    """Returns an error string, or '' if the resampled plan is safe to send.
    한글: 전송 전에 계획 전체를 검사한다: 유한값, 관절 한계, 스텝 크기(시작 포함)."""
    prev = start
    for t, vec in samples:
        for i, v in enumerate(vec):
            if not math.isfinite(v):
                return f'non-finite position at t={t:.2f}'
            lo, hi = limits[i]
            if v < lo or v > hi:
                return f'joint {i} target {v:.3f} outside [{lo:.3f}, {hi:.3f}] at t={t:.2f}'
            if abs(v - prev[i]) > max_step:
                return f'joint {i} step {abs(v - prev[i]):.3f} rad > {max_step:.3f} at t={t:.2f}'
        prev = vec
    return ''


def joint_age_error(joints, joint_servo, ages, now, limit_s, stats_timeout_s):
    """'' if every joint's own servo reading is fresh, else a reason. Pure (unit-tested).
    한글: 관절별 신선도 검사. /joint_states의 헤더 시각은 base_node가 캐시 값을 계속 재발행해서 항상 최신처럼 보이므로 쓰지 않고,
    base_node의 arm/servo_stats가 알려 주는 서보별 "마지막 응답 프레임 이후 경과 시간"(age_s)을 쓴다.
    ages: {servo_id: (age_s_when_reported, monotonic_time_of_report)}; age_s < 0 = that servo never answered.
    A servo with a few failed reads in a row can legitimately be silent for ~1 s (T1: up to 0.9 s at 20 Hz), so limit_s must
    be longer than that. Per joint, not per message: one silent servo must not hide behind five fresh ones."""
    if not ages:
        return 'no arm/servo_stats received (is base_node running with arm joint polling?)'
    newest = max(t for _, t in ages.values())
    if now - newest > stats_timeout_s:
        return f'arm/servo_stats is stale ({now - newest:.1f}s)'
    for j in joints:
        sid = joint_servo.get(j)
        if sid is None or sid not in ages:
            return f'no servo stats for joint {j}'
        age, reported = ages[sid]
        if age < 0:
            return f'joint {j} (servo {sid}) has never answered'
        eff = age + (now - reported)
        if eff > limit_s:
            return f'joint {j} (servo {sid}) reading is {eff:.1f}s old (limit {limit_s:.1f}s)'
    return ''


# 파지 상태별로 팔 관절 목표를 받아도 되는가(R6). HOLDING은 물체를 들고 옮겨야 하므로 허용.
# Whether an arm trajectory may start per grasp state (R6). HOLDING must be allowed: the arm carries the object.
ARM_DENIED_STATES = {'Check', 'Closing', 'Squeeze', 'Releasing', 'Failed'}


def grasp_goal_error(state, age_s, is_gripper, stale_s=3.0):
    """'' if a goal may start, else the reason. Pure (unit-tested). state: last arm/grasp_state text or None if
    never received; age_s: seconds since it was received.
    - never received -> allowed (an older base_node without the grasp feature must keep working);
    - received but silent for > stale_s -> refused (lost contact with base_node: do not guess);
    - gripper goals: only in Idle (while a grasp owns ID 10 -- even Holding -- only arm/release may open it);
    - arm goals: refused in the denied states, allowed in Idle and Holding.
    한글: 파지 중 소유권/제어권 판정의 브리지 쪽 첫 번째 겹(base_node가 두 번째 겹)."""
    if state is None:
        return ''
    if age_s > stale_s:
        return f'arm/grasp_state is stale ({age_s:.1f}s): not starting a trajectory'
    if is_gripper:
        return '' if state == 'Idle' else f'gripper is owned by the grasp ({state}); use arm/release'
    if state in ARM_DENIED_STATES:
        return f'arm motion is not allowed while the grasp is in state {state}'
    return ''


class BusyGate:
    """Atomic single-trajectory gate. acquire() is one locked test-and-set, so two goal requests arriving at the same
    moment can never both be accepted (the old plain bool was checked in the goal callback and set later in execute).
    A token older than `max_hold_s` is treated as leaked (e.g. an execute that never ran) and taken over.
    한글: 목표 수락을 한 번의 잠금 아래에서 원자적으로 한다. 오래된 토큰(실행이 안 돌았을 때)은 넘겨받는다."""

    def __init__(self, max_hold_s=120.0, clock=time.monotonic):
        self._lock = threading.Lock()
        self._since = None
        self._max = max_hold_s
        self._clock = clock
        self.takeovers = 0

    def acquire(self):
        with self._lock:
            now = self._clock()
            if self._since is not None:
                if now - self._since <= self._max:
                    return False
                self.takeovers += 1
            self._since = now
            return True

    def release(self):
        with self._lock:
            self._since = None

    @property
    def busy(self):
        with self._lock:
            return self._since is not None


class TrajectoryBridge(Node):
    def __init__(self):
        super().__init__('trajectory_bridge')
        # 한글: 컨트롤러 이름 -> 담당 관절. moveit_controllers.yaml과 같아야 한다.
        self.declare_parameter('arm_joints', ['joint1', 'joint2', 'joint3', 'joint4', 'joint5'])
        self.declare_parameter('gripper_joints', ['r_joint'])
        self.declare_parameter('command_topic', 'arm/command_timed')
        self.declare_parameter('period_s', 0.2)            # 전송 간격 / streaming period
        self.declare_parameter('max_step_rad', 0.2)        # 한 번에 보낼 최대 변화량(base_node는 0.35) / per-point step cap
        self.declare_parameter('limit_rad', 1.70)          # 관절 한계(MoveIt과 동일). 실제 팔은 홈에서 클램프(1.676)보다 6틱 더 처져 1.688로 읽힘 / same as MoveIt; the real arm rests at 1.688, slightly past the 1.676 pulse clamp
        self.declare_parameter('start_tolerance_rad', 0.1)  # 시작 자세 허용 오차 / start pose tolerance
        self.declare_parameter('tracking_tolerance_rad', 0.4)  # 이만큼 못 따라오면 중단 / abort beyond this lag
        self.declare_parameter('goal_tolerance_rad', 0.06)
        self.declare_parameter('state_timeout_s', 1.5)     # /joint_states가 이보다 오래되면 거부 / stale limit
        self.declare_parameter('settle_timeout_s', 3.0)
        # 관절별 신선도(arm/servo_stats). joint->servo id 대응은 base.yaml arm_joint_names/arm_servo_ids와 같아야 한다.
        self.declare_parameter('stats_joint_names', ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'r_joint'])
        self.declare_parameter('stats_servo_ids', [1, 2, 3, 4, 5, 10])
        # > longest silent gap seen at 20 Hz (0.9 s); needs arm_poll_hz >= 12 (5 Hz had 2.4 s gaps)
        self.declare_parameter('joint_age_limit_s', 1.5)
        self.declare_parameter('stats_timeout_s', 3.0)       # arm/servo_stats is 5 Hz (servo_stats_period_s 0.2)
        self.declare_parameter('require_servo_stats', True)  # False only for dry runs without base_node
        self.declare_parameter('busy_max_hold_s', 120.0)
        self.declare_parameter('dry_run', False)           # True면 명령을 발행하지 않고 검사/로그만 / validate+log only

        gp = self.get_parameter
        self.period = float(gp('period_s').value)
        self.max_step = float(gp('max_step_rad').value)
        self.limit = float(gp('limit_rad').value)
        self.start_tol = float(gp('start_tolerance_rad').value)
        self.track_tol = float(gp('tracking_tolerance_rad').value)
        self.goal_tol = float(gp('goal_tolerance_rad').value)
        self.state_timeout = float(gp('state_timeout_s').value)
        self.settle_timeout = float(gp('settle_timeout_s').value)
        self.dry_run = bool(gp('dry_run').value)
        names = [str(n) for n in gp('stats_joint_names').value]
        ids = [int(i) for i in gp('stats_servo_ids').value]
        self.joint_servo = dict(zip(names, ids))
        self.joint_age_limit = float(gp('joint_age_limit_s').value)
        self.stats_timeout = float(gp('stats_timeout_s').value)
        self.require_stats = bool(gp('require_servo_stats').value)
        self.gripper_set = {str(j) for j in gp('gripper_joints').value}
        self._ages = {}
        self._grasp_state = None
        self._grasp_state_time = 0.0

        self._lock = threading.Lock()
        self._state = {}      # joint -> position
        self._state_time = 0.0
        self._gate = BusyGate(float(gp('busy_max_hold_s').value))
        cbg = ReentrantCallbackGroup()
        self.create_subscription(JointState, 'joint_states', self._on_state, 20, callback_group=cbg)
        self.create_subscription(DiagnosticArray, 'arm/servo_stats', self._on_stats, 10, callback_group=cbg)
        self.create_subscription(String, 'arm/grasp_state', self._on_grasp_state, 10, callback_group=cbg)
        self.pub = self.create_publisher(JointTrajectory, str(gp('command_topic').value), 10)

        self._servers = []
        for name, key in (('arm_controller', 'arm_joints'), ('gripper_controller', 'gripper_joints')):
            joints = [str(j) for j in gp(key).value]
            self._servers.append(ActionServer(
                self, FollowJointTrajectory, f'{name}/follow_joint_trajectory',
                execute_callback=lambda gh, j=joints: self._execute(gh, j),
                goal_callback=lambda req, j=joints: self._on_goal(req, j),
                cancel_callback=lambda gh: CancelResponse.ACCEPT,
                callback_group=cbg))
        self.get_logger().info(
            f'trajectory bridge ready (period {self.period}s, max_step {self.max_step} rad, '
            f'dry_run={self.dry_run}); arm_command_enabled must be true in base_node')

    def _on_state(self, msg):
        with self._lock:
            for n, p in zip(msg.name, msg.position):
                self._state[n] = p
            self._state_time = time.monotonic()

    def _on_grasp_state(self, msg):
        with self._lock:
            self._grasp_state = str(msg.data)
            self._grasp_state_time = time.monotonic()

    def _on_stats(self, msg):
        t = time.monotonic()
        with self._lock:
            for st in msg.status:
                try:
                    sid = int(st.hardware_id)
                    age = next(float(kv.value) for kv in st.values if kv.key == 'age_s')
                except (ValueError, StopIteration):
                    continue
                self._ages[sid] = (age, t)

    def _current(self, joints):
        """Returns (positions, error). 한글: 최신 관절값, 없거나 오래되면 에러 문자열."""
        with self._lock:
            age = time.monotonic() - self._state_time
            if self._state_time == 0.0 or age > self.state_timeout:
                return None, f'/joint_states stale ({age:.1f}s)'
            missing = [j for j in joints if j not in self._state]
            if missing:
                return None, f'no joint state for {missing}'
            if self.require_stats:
                err = joint_age_error(joints, self.joint_servo, self._ages, time.monotonic(), self.joint_age_limit,
                                      self.stats_timeout)
                if err:
                    return None, err
            return [self._state[j] for j in joints], ''

    def _on_goal(self, req, joints):
        traj = req.trajectory
        if not traj.points or set(traj.joint_names) != set(joints):
            self.get_logger().warn(
                f'reject goal: joints {list(traj.joint_names)} != controller joints {joints}')
            return GoalResponse.REJECT
        with self._lock:
            gstate, gtime = self._grasp_state, self._grasp_state_time
        gerr = grasp_goal_error(gstate, time.monotonic() - gtime, set(joints) <= self.gripper_set)
        if gerr:
            self.get_logger().warn(f'reject goal: {gerr}')
            return GoalResponse.REJECT
        if not self._gate.acquire():
            self.get_logger().warn('reject goal: another trajectory is executing')
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def _send(self, joints, vec, duration):
        if self.dry_run:
            return
        msg = JointTrajectory()
        msg.joint_names = list(joints)
        pt = JointTrajectoryPoint()
        pt.positions = [float(v) for v in vec]
        pt.time_from_start.sec = int(duration)
        pt.time_from_start.nanosec = int((duration - int(duration)) * 1e9)
        msg.points = [pt]
        self.pub.publish(msg)

    def _finish(self, gh, code, text, joints=None, hold=False):
        """한글: 중단/실패 시 현재 자세를 유지시키고 결과를 돌려준다. / Hold the current pose on failure."""
        # 한글: 그리퍼는 hold 명령을 보내지 않는다 — "현재 읽은 위치로 이동"은 파지 중 조임을 풀어 물체를 떨어뜨린다.
        # 조임은 파지 상태 기계가 소유한다(prd/arm-control-path.md R7·D5). 팔 관절만 hold.
        # Never hold the gripper: commanding its current reading would release a squeeze.
        hold_joints = [j for j in (joints or []) if j not in self.gripper_set]
        if hold and hold_joints:
            cur, err = self._current(hold_joints)
            if cur is not None:
                self._send(hold_joints, cur, self.period)
        res = Result()
        res.error_code = code
        res.error_string = text
        if code == Result.SUCCESSFUL:
            gh.succeed()
        elif gh.is_cancel_requested:
            gh.canceled()
        else:
            gh.abort()
        if code != Result.SUCCESSFUL:
            self.get_logger().warn(f'trajectory not completed: {text}')
        return res

    def _execute(self, gh, joints):
        try:
            return self._execute_locked(gh, joints)
        finally:
            self._gate.release()   # 예외가 나도 반드시 해제 / released even if the body raises

    def _execute_locked(self, gh, joints):
        traj = gh.request.trajectory
        order = [list(traj.joint_names).index(j) for j in joints]
        times = [point_time(p) for p in traj.points]
        pos = [[p.positions[i] for i in order] for p in traj.points]
        if len(times) == 1:   # 점이 하나면 이동 시간 1 s로 간주 / single point: 1 s move
            times = [0.0, max(times[0], 1.0)]
            pos = [pos[0], pos[0]]
        cur, err = self._current(joints)
        if cur is None:
            return self._finish(gh, Result.INVALID_GOAL, err)
        if max(abs(a - b) for a, b in zip(cur, pos[0])) > self.start_tol:
            return self._finish(gh, Result.INVALID_GOAL,
                                f'arm is not at the trajectory start (cur {cur}, start {pos[0]})')
        samples = resample(times, pos, self.period)
        err = validate_plan(cur, samples, [(-self.limit, self.limit)] * len(joints), self.max_step)
        if err:
            return self._finish(gh, Result.INVALID_GOAL, 'plan rejected: ' + err)
        self.get_logger().info(
            f'executing {len(samples)} points over {samples[-1][0]:.1f}s for {joints}'
            + (' [DRY RUN]' if self.dry_run else ''))

        t0 = time.monotonic()
        for t, vec in samples:
            # 한글: 목표 시각까지 대기하면서 취소/상태 끊김을 감시한다.
            send_at = t0 + t - self.period
            while time.monotonic() < send_at:
                if gh.is_cancel_requested:
                    return self._finish(gh, Result.PATH_TOLERANCE_VIOLATED, 'canceled', joints, hold=True)
                time.sleep(0.01)
            if gh.is_cancel_requested:
                return self._finish(gh, Result.PATH_TOLERANCE_VIOLATED, 'canceled', joints, hold=True)
            now_cur, err = self._current(joints)
            if now_cur is None:
                return self._finish(gh, Result.PATH_TOLERANCE_VIOLATED, err, joints, hold=True)
            if not self.dry_run:
                desired = interpolate(times, pos, max(0.0, t - self.period))
                lag = max(abs(a - b) for a, b in zip(now_cur, desired))
                if lag > self.track_tol:
                    return self._finish(gh, Result.PATH_TOLERANCE_VIOLATED,
                                        f'arm lags the plan by {lag:.2f} rad', joints, hold=True)
            self._send(joints, vec, self.period)

        # 한글: 마지막 점 도달 대기(서보 지연). / wait for the servos to settle on the last point.
        deadline = time.monotonic() + self.period + self.settle_timeout
        while time.monotonic() < deadline:
            fin, err = self._current(joints)
            if self.dry_run or (fin is not None and
                                max(abs(a - b) for a, b in zip(fin, samples[-1][1])) <= self.goal_tol):
                return self._finish(gh, Result.SUCCESSFUL, '')
            time.sleep(0.05)
        return self._finish(gh, Result.GOAL_TOLERANCE_VIOLATED, 'did not reach the final point',
                            joints, hold=False)


def main():
    rclpy.init()
    node = TrajectoryBridge()
    ex = MultiThreadedExecutor(num_threads=4)
    ex.add_node(node)
    try:
        ex.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
