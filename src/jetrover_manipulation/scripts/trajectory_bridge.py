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
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import JointState
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

        self._lock = threading.Lock()
        self._state = {}      # joint -> position
        self._state_time = 0.0
        self._busy = False
        cbg = ReentrantCallbackGroup()
        self.create_subscription(JointState, 'joint_states', self._on_state, 20, callback_group=cbg)
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

    def _current(self, joints):
        """Returns (positions, error). 한글: 최신 관절값, 없거나 오래되면 에러 문자열."""
        with self._lock:
            age = time.monotonic() - self._state_time
            if self._state_time == 0.0 or age > self.state_timeout:
                return None, f'/joint_states stale ({age:.1f}s)'
            missing = [j for j in joints if j not in self._state]
            if missing:
                return None, f'no joint state for {missing}'
            return [self._state[j] for j in joints], ''

    def _on_goal(self, req, joints):
        traj = req.trajectory
        if not traj.points or set(traj.joint_names) != set(joints):
            self.get_logger().warn(
                f'reject goal: joints {list(traj.joint_names)} != controller joints {joints}')
            return GoalResponse.REJECT
        if self._busy:
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
        if hold and joints:
            cur, err = self._current(joints)
            if cur is not None:
                self._send(joints, cur, self.period)
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
        self._busy = False
        return res

    def _execute(self, gh, joints):
        self._busy = True
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
