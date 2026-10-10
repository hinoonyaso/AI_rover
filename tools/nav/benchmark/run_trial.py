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

from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_msgs.action import NavigateThroughPoses, NavigateToPose
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from nav_msgs.msg import Path
from sensor_msgs.msg import BatteryState
import tf2_ros

START = (1.05, 0.10, 90.0)
SCENARIOS = {
    'A': {'goal': (1.05, 1.10, 90.0), 'mode': 'line'},
    # B: NavigateToPose (2026-10-10 E6): the line waypoints put one pose (1.05, 0.62) inside the box, so
    # ComputePathThroughPoses failed ("no valid path") and every B run aborted. The "back on the line" check is
    # the final lateral deviation (<= 0.10 m). 한글: 경유점이 상자 안에 찍혀 경로 실패 → 최종 목표로 바로 보낸다.
    'B': {'goal': (1.05, 1.40, 90.0), 'mode': 'pose'},
    'C': {'goal': (0.50, 0.80, 180.0), 'mode': 'pose'},
}
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
    args = ap.parse_args()
    sc = SCENARIOS[args.scenario]
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

    fb = {'recoveries': 0, 'remaining': None}
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
                    handle.cancel_goal_async()  # 한글: 시간 초과면 목표를 취소해 로봇을 세운다
                    node.spin(2.0)
                    status = 'timeout'
                    break
            if status is None:
                status = {4: 'succeeded', 5: 'canceled', 6: 'aborted'}.get(res.result().status, str(res.result().status))
    except KeyboardInterrupt:
        if handle is not None:
            handle.cancel_goal_async()
        status = 'interrupted'
    finally:
        elapsed = time.time() - t0
        node.spin(3.0)  # settle so the final pose is stable
        final_tf = node.tf_pose()
        final = final_tf or node.amcl
        os.killpg(bag.pid, signal.SIGINT)
        try:
            bag.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(bag.pid, signal.SIGKILL)

    line_dev = None
    track = node.tf_track or node.track
    if args.scenario in ('A', 'B') and track:
        line_dev = max(abs(x - START[0]) for _, x, _ in track)
    pos_err = math.hypot(final[0] - gx, final[1] - gy) if final else None
    yaw_err = abs(wrap(final[2] - gyaw)) if final else None
    final_dev = abs(final[0] - START[0]) if (final and args.scenario in ('A', 'B')) else None
    ok = (status == 'succeeded' and elapsed <= 60.0 and pos_err is not None and pos_err <= 0.15 and
          yaw_err is not None and math.radians(yaw_err) <= 0.4 and (final_dev is None or args.scenario != 'B' or final_dev <= 0.10))
    plan_short = None
    if node.plan_end is not None:
        plan_short = math.hypot(node.plan_end[0] - gx, node.plan_end[1] - gy)
    invalid = plan_short is not None and plan_short > 0.10
    meta = {
        'scenario': args.scenario, 'trial': args.trial, 'goal': {'x': gx, 'y': gy, 'yaw_deg': gyaw},
        'outcome': 'success' if ok else ('abort' if status in ('aborted', 'canceled', 'interrupted', 'timeout') else 'fail'),
        'collision': None,   # 한글: 사람이 판정 (set_meta.py)
        'recoveries': fb['recoveries'], 'measured_final': None,
        'auto': {'action_status': status, 'elapsed_s': round(elapsed, 1), 'battery_start_v': battery_start,
                 'amcl_start': start_amcl, 'amcl_final': final, 'pos_err_m': pos_err, 'yaw_err_deg': yaw_err,
                 'max_line_dev_m': line_dev, 'final_line_dev_m': final_dev,
                 'final_from': 'tf' if final_tf else 'amcl_pose',
                 'start_from': 'nominal' if args.nominal_start else 'scan_match',
                 'last_plan_end_to_goal_m': plan_short, 'invalid_plan_cut_short': invalid},
        'notes': ''}
    with open(os.path.join(out_dir, 'meta.json'), 'w') as f:
        json.dump(meta, f, indent=1)
    print(json.dumps(meta['auto'], indent=1))
    if invalid:
        print('INVALID: the last plan ended %.2f m from the goal (goal area blocked: person/object in front?) '
              '-> clear the area and repeat this trial number with a new tag or delete %s' % (plan_short, out_dir))
    print('trial %s%02d: auto-outcome=%s (collision still TODO) -> %s/meta.json' % (args.scenario, args.trial, meta['outcome'], out_dir))
    rclpy.shutdown()


if __name__ == '__main__':
    main()
