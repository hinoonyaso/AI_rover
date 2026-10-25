#!/usr/bin/env python3
# 한글: Nav2 baseline 시험 1회를 자동으로 진행한다: AMCL 초기 위치 -> rosbag 기록 시작 -> 목표 전송 -> 결과/지표 수집 -> meta.json.
# 충돌 여부와 줄자 실측은 사람이 판정하므로 meta.json에 TODO로 남긴다(set_meta.py로 채운다).
"""Run one baseline trial (see prd/nav2-baseline-test-plan.md).

Usage: python3 run_trial.py <A|B|C> <trial#> [--tag baseline_openloop]
Needs Nav2 + AMCL running. The robot MOVES. A person must stand at the power switch.
  A/B: straight line from S=(1.05,0.10) with waypoints every 0.3 m (same as tools/nav/line_goal.py)
  C  : NavigateToPose to (0.50, 0.80, yaw 180)
Writes bags/<tag>/trial_<S><NN>/ (rosbag2) and meta.json with auto-measured fields; collision/notes stay for the operator.
"""
import argparse
import json
import math
import os
import signal
import subprocess
import sys
import time

from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped, Twist
from nav2_msgs.action import NavigateThroughPoses, NavigateToPose
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from nav_msgs.msg import Odometry, Path
from sensor_msgs.msg import BatteryState
import tf2_ros

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trial_judge as judge  # noqa: E402
from set_measured_scan import run_scan  # noqa: E402
from confirm_last_trial import confirm as confirm_last  # noqa: E402

LAST_TRIAL = 'Log/last_trial.json'  # operator convention: starting the next trial confirms 'no collision' for this one

START = (1.05, 0.10, 90.0)
SCENARIOS = {
    'A': {'goal': (1.05, 1.10, 90.0), 'mode': 'line'},
    # B: NavigateToPose (2026-10-10 E6): the line waypoints put one pose (1.05, 0.62) inside the box, so
    # ComputePathThroughPoses failed ("no valid path") and every B run aborted. The "back on the line" check is
    # the final lateral deviation (<= 0.10 m). 한글: 경유점이 상자 안에 찍혀 경로 실패 → 최종 목표로 바로 보낸다.
    'B': {'goal': (1.05, 1.40, 90.0), 'mode': 'pose'},
    'C': {'goal': (0.50, 0.80, 180.0), 'mode': 'pose'},
    # D (2026-10-11): A's goal sent as a single NavigateToPose. A uses NavigateThroughPoses whose BT deletes the last
    # waypoint at RemovePassedGoals radius 0.12 m, so A always stops ~12 cm short whatever the goal checker says
    # (found with the tolerance 0.10 test) -- D is the straight-line trial where the goal checker tolerance applies.
    # 한글: A는 BT가 0.12 m에서 마지막 경유점을 지워 허용 오차와 무관하게 약 12 cm 앞에서 끝난다 → 허용 오차 시험은 D(NavigateToPose).
    'D': {'goal': (1.05, 1.10, 90.0), 'mode': 'pose'},
    # E (2026-10-11): C mirrored to the right (turn 90 deg CW). There is an object on the left that cannot be removed and
    # disturbed C; the right side of the map is tighter (clearance 0.34 m at the goal vs 0.65 m for C).
    # 한글: C의 좌우 대칭(오른쪽 대각 + 시계 90° 회전). 왼쪽에 치울 수 없는 물체가 있어 C가 영향을 받음.
    'E': {'goal': (1.50, 0.70, 0.0), 'mode': 'pose'},
}
# --start X Y YAW (2026-10-25, 8.15/8.16 실기): 출발점을 바꿀 때 A/B/D 목표는 출발 방향으로 이 거리만큼 앞(원래 S 기준과 같은 거리).
# With --start, the A/B/D goals are this far ahead of the start along its heading (same distances as from the original S).
FORWARD_M = {'A': 1.00, 'B': 1.30, 'D': 1.00}


def ahead(start, dist):
    """Map pose `dist` m ahead of start (x, y, yaw_deg), same heading. 한글: 출발 방향으로 dist m 앞."""
    yaw = math.radians(start[2])
    return (start[0] + dist * math.cos(yaw), start[1] + dist * math.sin(yaw), start[2])


def line_offset(start, x, y):
    """Signed lateral offset (m) of (x, y) from the line through start along its heading (left +)."""
    yaw = math.radians(start[2])
    return -math.sin(yaw) * (x - start[0]) + math.cos(yaw) * (y - start[1])


TOPICS = ('/tf /tf_static /odom /amcl_pose /cmd_vel /cmd_vel_nav /scan /plan /received_global_plan '
          '/depth_cam/depth/points_sparse /global_costmap/costmap /local_costmap/costmap '
          '/collision_monitor_state').split()
TIMEOUT_S = 70.0


def quat(yaw_deg):
    h = math.radians(yaw_deg) / 2.0
    return math.sin(h), math.cos(h)


def yaw_of(q):
    return math.degrees(2.0 * math.atan2(q.z, q.w))


def wrap(d):
    return (d + 180.0) % 360.0 - 180.0


def make_pose(x, y, yaw_deg):
    p = PoseStamped()
    p.header.frame_id = 'map'
    p.pose.position.x, p.pose.position.y = x, y
    p.pose.orientation.z, p.pose.orientation.w = quat(yaw_deg)
    return p


class Trial(Node):
    def __init__(self):
        super().__init__('baseline_trial')
        self.amcl = None
        self.volt = None
        self.track = []  # (t, x, y)
        self.create_subscription(PoseWithCovarianceStamped, 'amcl_pose', self.on_amcl, 10)
        self.create_subscription(BatteryState, 'battery_state', lambda m: setattr(self, 'volt', m.voltage), 10)
        # Last planned path end: the planner (tolerance 0.25) ends short when the goal area is blocked, and the
        # controller then "succeeds" there (2026-10-10 A01: something ~1 m ahead, path cut to 0.97 for 1.10).
        # 한글: 목표 주변이 막히면 경로가 짧아지고 그 끝에서 '성공'이 나므로 경로 끝을 기록해 무효를 가린다.
        self.plan_end = None
        self.create_subscription(Path, 'plan', self.on_plan, 10)
        # 한글: 정지 확인용 속도(EKF /odom). 측정은 로봇이 실제로 멈춘 뒤에 한다.
        self.odom_samples = []   # (time.monotonic(), v, |wz|)
        self.create_subscription(Odometry, 'odom', self.on_odom, 10)
        self.init_pub = self.create_publisher(PoseWithCovarianceStamped, 'initialpose', 1)
        # /amcl_pose is only published after update_min_d/a of motion, so its last value lags the stop pose
        # (2026-10-10: A01 "stopped" 31 cm short). The final pose and the line deviation use TF
        # map->base_footprint sampled at 10 Hz. 한글: AMCL 메시지는 늦게 갱신돼 TF로 최종 위치·궤적을 잰다.
        self.tf_buf = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buf, self)
        self.tf_track = []  # (t, x, y)
        self.create_timer(0.1, self.sample_tf)

    def tf_pose(self):
        try:
            t = self.tf_buf.lookup_transform('map', 'base_footprint', rclpy.time.Time())
        except Exception:  # noqa: BLE001
            return None
        tr = t.transform
        return (tr.translation.x, tr.translation.y, yaw_of(tr.rotation))

    def sample_tf(self):
        p = self.tf_pose()
        if p is not None:
            self.tf_track.append((time.time(), p[0], p[1]))

    def on_plan(self, m):
        if m.poses:
            p = m.poses[-1].pose.position
            self.plan_end = (p.x, p.y)

    def on_odom(self, m):
        t = m.twist.twist
        now = time.monotonic()
        self.odom_samples.append((now, math.hypot(t.linear.x, t.linear.y), abs(t.angular.z)))
        del self.odom_samples[:-200]

    def wait_stopped(self, hold=1.0, limit=6.0):
        """(True, reason) once /odom has been FRESH and below the stop limits for `hold` s (trial_judge.stop_state).
        A silent /odom is never counted as stopped. 한글: /odom이 끊기면 마지막 값(0)을 믿지 않고 정지로 치지 않는다."""
        t0 = time.monotonic()
        reason = 'no_odom'
        while time.monotonic() - t0 < limit:
            self.spin(0.1)
            ok, reason = judge.stop_state(self.odom_samples, time.monotonic(), hold)
            if ok:
                return True, reason
        return False, reason

    def cancel_goal(self, handle, timeout=3.0):
        """Cancel and wait for the action server's answer. Returns (acknowledged, text)."""
        if handle is None:
            return True, 'no goal'
        fut = handle.cancel_goal_async()
        t0 = time.monotonic()
        while not fut.done() and time.monotonic() - t0 < timeout:
            self.spin(0.05)
        if not fut.done():
            return False, 'cancel request not answered in %.0f s' % timeout
        codes = [c.goal_info.goal_id for c in fut.result().goals_canceling]
        return True, 'canceled' if codes else 'nothing to cancel (already finished)'

    def on_amcl(self, m):
        p = m.pose.pose
        self.amcl = (p.position.x, p.position.y, yaw_of(p.orientation))
        self.track.append((time.time(), p.position.x, p.position.y))

    def spin(self, secs):
        t0 = time.time()
        while time.time() - t0 < secs:
            rclpy.spin_once(self, timeout_sec=0.05)

    def set_initial_pose(self):
        m = PoseWithCovarianceStamped()
        m.header.frame_id = 'map'
        m.pose.pose.position.x, m.pose.pose.position.y = START[0], START[1]
        m.pose.pose.orientation.z, m.pose.pose.orientation.w = quat(START[2])
        m.pose.covariance[0] = m.pose.covariance[7] = 0.05
        m.pose.covariance[35] = 0.05
        for _ in range(3):
            self.init_pub.publish(m)
            self.spin(1.0)
        self.spin(4.0)


def confirm_previous_trial():
    """Operator convention (2026-10-11): an unreported collision means none. Starting the next trial confirms it."""
    path, m = confirm_last(False, 'convention: no collision reported before the next trial started', path_file=LAST_TRIAL)
    if path and m.get('collision_source', '').startswith('convention: no collision reported before'):
        print('previous trial %s: collision none (confirmed) -> %s' % (path, m['outcome']))


def relocalize(node, radius=0.3):
    """Scan-match near the current pose and let it reset AMCL (/initialpose). Returns a dict for meta.json.

    한글: 지금 위치 근처(반경 radius)에서 스캔 매칭 → 확신이 있으면 /initialpose로 AMCL을 다시 잡는다. 이동 전후 자세도 남긴다.
    """
    node.wait_stopped()
    before = node.tf_pose()
    if before is None:
        return {'status': 'no_pose'}
    rc = subprocess.run(['ros2', 'run', 'jetrover_navigation', 'scan_match_init.py', '--near', '%.3f' % before[0],
                         '%.3f' % before[1], '--near-radius', str(radius)], capture_output=True, text=True, timeout=90)
    published = 'published /initialpose' in rc.stdout + rc.stderr
    node.spin(2.0)
    after = node.tf_pose()
    out = {'status': 'published' if published else 'not_confident', 'before': before, 'after': after}
    if after is not None:
        out['shift_m'] = round(math.hypot(after[0] - before[0], after[1] - before[1]), 3)
    return out


def run_approach(node, gx, gy, gyaw, max_start_m=0.28, timeout_s=25.0):
    """Precise approach after Nav2 (tools: jetrover_navigation precise_approach.py). Returns a dict for meta.json.

    한글: Nav2 종료 후 목표 max_start_m 안이면 정밀 접근 액션 호출. 노드가 속도(0.06 m/s)·시작 거리(0.30 m)·시간(20 s)을 제한한다.
    """
    pose = node.tf_pose() or node.amcl
    if pose is None:
        return {'status': 'no_pose'}
    dist = math.hypot(pose[0] - gx, pose[1] - gy)
    if dist > max_start_m:
        return {'status': 'skipped', 'start_dist_m': round(dist, 3)}
    client = ActionClient(node, NavigateToPose, 'precise_approach')
    if not client.wait_for_server(timeout_sec=3.0):
        return {'status': 'no_server', 'start_dist_m': round(dist, 3)}
    goal = NavigateToPose.Goal()
    goal.pose = make_pose(gx, gy, gyaw)
    t0 = time.time()
    send = client.send_goal_async(goal)
    rclpy.spin_until_future_complete(node, send)
    handle = send.result()
    if not handle.accepted:
        return {'status': 'rejected', 'start_dist_m': round(dist, 3)}
    res = handle.get_result_async()
    while not res.done() and time.time() - t0 < timeout_s:
        rclpy.spin_once(node, timeout_sec=0.05)
    if not res.done():
        node.cancel_goal(handle)
        node.spin(1.0)
        status = 'timeout'
    else:
        status = {4: 'succeeded', 5: 'canceled', 6: 'aborted'}.get(res.result().status, str(res.result().status))
    return {'status': status, 'start_dist_m': round(dist, 3), 'time_s': round(time.time() - t0, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('scenario', choices=sorted(SCENARIOS))
    ap.add_argument('trial', type=int)
    ap.add_argument('--tag', default='baseline_openloop')
    # 2026-10-10 E6: stale depth marks (a person standing near the goal earlier) stayed in the global costmap and
    # forced a 3.5 m detour. Clear both costmaps and let the sensors repopulate before every trial (same for every
    # condition). 한글: 매 시험 전 costmap을 비우고 센서로 다시 채운다(모든 조건 동일).
    ap.add_argument('--no-clear', action='store_true', help='do not clear the costmaps before the trial')
    # 2026-10-10 E6 v2: the nominal START forced into AMCL was ~5 cm off the real start mark and AMCL then stayed
    # 3-7 cm biased, hiding the odometry difference. Default now: scan-match the robot on the start mark and
    # initialise AMCL there (the goals stay the same map points). 한글: 출발 위치를 스캔 매칭으로 잡아 AMCL 초기화.
    ap.add_argument('--nominal-start', action='store_true',
                    help='old behaviour: force AMCL to the nominal START instead of scan matching')
    ap.add_argument('--no-scan', action='store_true', help='do not scan-match the final pose (manual tape only)')
    # 2026-10-25 (8.15/8.16 실기): Nav2가 끝난 뒤 목표 0.28 m 안이면 정밀 접근(precise_approach 노드)을 이어서 호출 — sim 시험과 같은 순서.
    # Call the precise_approach action after Nav2 when within 0.28 m of the goal (the node must be running), as in the sim.
    ap.add_argument('--approach', action='store_true', help='run precise_approach after Nav2 (node must be running)')
    # 2026-10-25 (troubleshooting/055): AMCL이 이동을 5~7 % 짧게 잡아 실제로 8~9 cm 더 갔다(스캔 매칭은 줄자와 1 cm 안).
    # 정밀 접근 직전에 지금 위치 근처에서 스캔 매칭으로 AMCL을 다시 잡는다. / re-localize by scan matching before the approach.
    ap.add_argument('--relocalize', action='store_true',
                    help='with --approach: scan-match near the current pose and reset AMCL before the precise approach')
    ap.add_argument('--start', type=float, nargs=3, metavar=('X', 'Y', 'YAW_DEG'),
                    help='use this start pose (map) instead of S; A/B/D goals become FORWARD_M ahead of it')
    args = ap.parse_args()
    global START
    sc = SCENARIOS[args.scenario]
    if args.start:
        if args.scenario not in FORWARD_M:
            sys.exit('--start works with A/B/D only (their goals are a distance ahead of the start)')
        START = tuple(args.start)
        sc = dict(sc, goal=ahead(START, FORWARD_M[args.scenario]))
        print('start %.2f %.2f %.0f deg -> goal %.2f %.2f (%.2f m ahead)' % (*START, *sc['goal'][:2], FORWARD_M[args.scenario]))
    confirm_previous_trial()
    gx, gy, gyaw = sc['goal']
    out_dir = 'bags/%s/trial_%s%02d' % (args.tag, args.scenario, args.trial)
    if os.path.exists(out_dir):
        sys.exit('%s already exists' % out_dir)
    os.makedirs(os.path.dirname(out_dir), exist_ok=True)

    rclpy.init()
    node = Trial()
    node.spin(1.5)
    battery_start = node.volt
    if not args.no_clear:
        for svc in ('/global_costmap/clear_entirely_global_costmap', '/local_costmap/clear_entirely_local_costmap'):
            subprocess.run(['ros2', 'service', 'call', svc, 'nav2_msgs/srv/ClearEntireCostmap', '{}'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        node.spin(2.0)  # sensors repopulate / 센서가 다시 채우는 시간
    if args.nominal_start:
        node.set_initial_pose()
    else:
        node.amcl = None
        rc = subprocess.run(['ros2', 'run', 'jetrover_navigation', 'scan_match_init.py', '--near',
                             str(START[0]), str(START[1]), '--near-radius', '0.3'],
                            capture_output=True, text=True, timeout=90)
        if 'published /initialpose' not in rc.stdout + rc.stderr:
            sys.exit('scan matching was not confident at the start: check the start area and retry\n'
                     + (rc.stdout + rc.stderr)[-600:])
        node.spin(3.0)
    if node.amcl is None or math.hypot(node.amcl[0] - START[0], node.amcl[1] - START[1]) > 0.15 or \
            abs(wrap(node.amcl[2] - START[2])) > 10.0:
        sys.exit('AMCL pose %s is not at the start pose %s (15 cm / 10 deg): place the robot and retry'
                 % (node.amcl, START))
    start_amcl = node.amcl
    print('start ok: AMCL %.2f %.2f %.0f deg, battery %s V' % (*start_amcl, battery_start))

    bag = subprocess.Popen(['ros2', 'bag', 'record', '-o', out_dir] + TOPICS,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)
    node.spin(3.0)  # let the recorder subscribe
    node.track.clear()
    # 2026-10-11: tf_track was filled since the node started, i.e. with the pre-initialisation pose (previous trial's end)
    # -> max_line_dev 0.55 m in a box-less run. 한글: 초기화 전 자세가 궤적에 섞이지 않게 여기서 비운다.
    node.tf_track.clear()

    fb = {'recoveries': 0, 'remaining': None}
    approach = None
    t0 = time.time()
    status = None
    if sc['mode'] == 'line':
        client = ActionClient(node, NavigateThroughPoses, 'navigate_through_poses')
        goal = NavigateThroughPoses.Goal()
        dx, dy = gx - START[0], gy - START[1]
        n = max(1, int(math.ceil(math.hypot(dx, dy) / 0.3)))
        goal.poses = [make_pose(START[0] + dx * i / n, START[1] + dy * i / n, gyaw) for i in range(1, n + 1)]
    else:
        client = ActionClient(node, NavigateToPose, 'navigate_to_pose')
        goal = NavigateToPose.Goal()
        goal.pose = make_pose(gx, gy, gyaw)
    if not client.wait_for_server(timeout_sec=10.0):
        os.killpg(bag.pid, signal.SIGINT)
        sys.exit('action server not available')

    def on_fb(f):
        fb['recoveries'] = f.feedback.number_of_recoveries
        fb['remaining'] = f.feedback.distance_remaining
    handle = None
    cancel_ok, cancel_msg = True, 'not needed'
    try:
        send = client.send_goal_async(goal, feedback_callback=on_fb)
        rclpy.spin_until_future_complete(node, send)
        handle = send.result()
        if not handle.accepted:
            status = 'rejected'
        else:
            res = handle.get_result_async()
            while not res.done():
                rclpy.spin_once(node, timeout_sec=0.05)
                if time.time() - t0 > TIMEOUT_S:
                    cancel_ok, cancel_msg = node.cancel_goal(handle)  # 한글: 시간 초과면 취소하고 응답을 확인한다
                    node.spin(2.0)
                    status = 'timeout'
                    break
            if status is None:
                status = {4: 'succeeded', 5: 'canceled', 6: 'aborted'}.get(res.result().status, str(res.result().status))
        if args.approach and status in ('succeeded', 'aborted'):
            reloc = relocalize(node) if args.relocalize else None
            approach = run_approach(node, gx, gy, gyaw)
            if reloc is not None:
                approach['relocalize'] = reloc
            print('precise approach: %s' % approach)
    except KeyboardInterrupt:
        cancel_ok, cancel_msg = node.cancel_goal(handle)
        status = 'interrupted'
    finally:
        elapsed = time.time() - t0
        stopped, stop_reason = node.wait_stopped()
        stop_recovery = None
        safety_error = None
        if not cancel_ok:
            safety_error = 'goal cancel not acknowledged: %s' % cancel_msg
        if not stopped:
            # 2026-10-11 review: never measure a robot that may still be moving, and never trust a silent /odom.
            # Cancel (and wait for the answer), send zero velocity, check again; the measurement is skipped either way.
            # 한글: 정지 확인 실패 → 취소(응답 확인) + 정지 명령 후 다시 확인, 측정은 하지 않는다.
            ok2, msg2 = node.cancel_goal(handle)
            if not ok2:
                safety_error = 'goal cancel not acknowledged: %s' % msg2
            stop_pub = node.create_publisher(Twist, 'cmd_vel', 10)
            for _ in range(10):
                stop_pub.publish(Twist())
                node.spin(0.1)
            stopped2, stop_reason2 = node.wait_stopped()
            stop_recovery = 'stopped after cancel + zero cmd_vel' if stopped2 else 'NOT stopped (%s)' % stop_reason2
            if not stopped2:
                safety_error = (safety_error + '; ' if safety_error else '') + \
                    'robot not confirmed stopped (%s -> %s)' % (stop_reason, stop_reason2)
            print('WARNING: robot not confirmed stopped after the goal (%s) -- no scan match%s' %
                  (stop_recovery, '' if not safety_error else '; SAFETY ERROR: ' + safety_error))
        node.spin(1.0)  # settle so the final pose is stable
        final_tf = node.tf_pose()
        final = final_tf or node.amcl
        # Scan-match while the bag is still recording, so the scans the match used stay in the bag for re-checking.
        # 한글: bag 녹화 중에 스캔 매칭을 돌려, 매칭에 쓴 스캔이 bag에 남게 한다(나중에 재검증 가능).
        if not stopped:
            scan = {'status': 'not_stopped'}
        elif args.no_scan or status == 'interrupted':
            scan = {'status': 'skipped'}
        else:
            scan = run_scan(gx, gy)
        os.killpg(bag.pid, signal.SIGINT)
        try:
            bag.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(bag.pid, signal.SIGKILL)

    line_dev = None
    track = node.tf_track or node.track
    # 직선 이탈은 출발 방향 기준(원래 S는 +y 방향이라 |x - 1.05|와 같다) / lateral offset from the start heading line
    if args.scenario in ('A', 'B', 'D') and track:
        line_dev = max(abs(line_offset(START, x, y)) for _, x, y in track)
    pos_err = math.hypot(final[0] - gx, final[1] - gy) if final else None
    yaw_err = abs(wrap(final[2] - gyaw)) if final else None
    final_dev = abs(line_offset(START, final[0], final[1])) if (final and args.scenario in ('A', 'B', 'D')) else None
    plan_short = None
    if node.plan_end is not None:
        plan_short = math.hypot(node.plan_end[0] - gx, node.plan_end[1] - gy)
    invalid = plan_short is not None and plan_short > judge.PLAN_CUT_M
    meta = {
        'scenario': args.scenario, 'trial': args.trial, 'goal': {'x': gx, 'y': gy, 'yaw_deg': gyaw},
        'start': {'x': START[0], 'y': START[1], 'yaw_deg': START[2]},   # trial_judge.line_offset_m
        'outcome': None,
        'collision': None,   # 한글: 사람이 판정 (set_meta.py, 또는 다음 회차 시작 시 '충돌 없음'으로 확정)
        'recoveries': fb['recoveries'], 'measured_final': None,
        'auto': {'action_status': status, 'elapsed_s': round(elapsed, 1), 'battery_start_v': battery_start,
                 'amcl_start': start_amcl, 'amcl_final': final, 'pos_err_m': pos_err, 'yaw_err_deg': yaw_err,
                 'max_line_dev_m': line_dev, 'final_line_dev_m': final_dev,
                 'final_from': 'tf' if final_tf else 'amcl_pose',
                 'start_from': 'nominal' if args.nominal_start else 'scan_match',
                 'last_plan_end_to_goal_m': plan_short, 'invalid_plan_cut_short': invalid,
                 'stopped_before_measure': stopped, 'stop_reason': stop_reason, 'stop_recovery': stop_recovery,
                 'cancel': cancel_msg, 'safety_error': safety_error, 'approach': approach},
        'notes': ''}
    meta = judge.apply_scan(meta, scan)
    with open(os.path.join(out_dir, 'meta.json'), 'w') as f:
        json.dump(meta, f, indent=1)
    print(json.dumps(meta['auto'], indent=1))
    sf = meta.get('scan_final') or {}
    if sf.get('status') == 'ok':
        print('scan match: (%.3f, %.3f, %.1f deg) score %.3f margin %.3f %s' % (
            sf['x'], sf['y'], sf['yaw_deg'], sf['score'], sf['margin'], 'trusted' if sf['trusted'] else 'NOT trusted'))
    else:
        print('scan match: %s' % sf.get('status'))
    os.makedirs(os.path.dirname(LAST_TRIAL), exist_ok=True)
    with open(LAST_TRIAL, 'w') as f:
        json.dump({'meta': os.path.join(out_dir, 'meta.json')}, f)
    if invalid:
        print('INVALID: the last plan ended %.2f m from the goal (goal area blocked: person/object in front?) '
              '-> clear the area and repeat this trial number with a new tag or delete %s' % (plan_short, out_dir))
    print('MVP approach (<= %.0f cm): %s' % (judge.MVP_POS_TOL_M * 100, meta['mvp']['pass']))
    print('trial %s%02d: outcome=%s (%s) -> %s/meta.json'
          % (args.scenario, args.trial, meta['outcome'], meta['outcome_reason'], out_dir))
    print('collision: say so now if there was one (set_meta.py ... y); starting the next trial records "none"')
    rclpy.shutdown()


if __name__ == '__main__':
    main()
