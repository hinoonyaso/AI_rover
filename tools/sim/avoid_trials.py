#!/usr/bin/env python3
# 한글: Gazebo 회피 주행 시험 반복 실행기(host). 회차마다 로봇·상자를 순간이동하고 AMCL을 정답으로 초기화한 뒤
#       NavigateToPose를 보내고, Gazebo 정답 자세·컨트롤러 명령·/plan으로 avoid_metrics 지표를 계산해 CSV에 남긴다.
#       실기 로봇은 쓰지 않는다. Gazebo + Nav2(auto_localize:=false)가 떠 있어야 한다: tools/sim/sim_avoid_run.sh
"""Repeat avoidance trials in Gazebo and score them against ground truth (host only, ROS_DOMAIN_ID=31).

  python3 tools/sim/avoid_trials.py run --tag dwb --scenario S2 --repeats 5
  python3 tools/sim/avoid_trials.py summary --prefix dwb

Scenarios (map = Gazebo world; the box is the 33 x 22 x 11 cm `object_0`; the 3 cm cubes are moved under the floor):
  S1  (0.55, 0.40, 90 deg) -> (0.55, 1.20)               no obstacle on the line (box far away at 1.21, 0.78)
  S2  A (1.02, 0.30, 83) <-> B (1.00, 1.25)              box at (1.21, 0.78): its left edge 4.5 cm right of the line
  S4  A <-> B                                            box at (1.00, 0.78): in the middle of the line
(simulation-room coordinates: the real F2 geometry, 20 cm further north, is not usable in the scanned room, see SCENARIOS)
Each leg is its own trial. Output: Log/sim_avoid_trials.csv, Log/sim_avoid/<tag>_<scenario>_<leg>_<n>_<stamp>.json
Success = Nav2 succeeded AND no contact (footprint-box gap > 0) AND the box was pushed < 2 cm.
"""
import argparse
import csv
import json
import math
import os
import pty
import signal
import subprocess
import sys
import threading
import time

from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped, Twist
from nav2_msgs.action import NavigateToPose
from nav2_msgs.msg import CollisionMonitorState
from nav2_msgs.srv import ClearEntireCostmap
from nav_msgs.msg import Path
import numpy as np
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.parameter import Parameter
import tf2_ros

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import avoid_metrics as M  # noqa: E402
import dyn_obstacles as DYN  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
CSV_PATH = os.path.join(ROOT, 'Log', 'sim_avoid_trials.csv')
JSON_DIR = os.path.join(ROOT, 'Log', 'sim_avoid')
WORLD = 'jetrover_room'
BOX = 'object_0'
BOX_SIZE = (0.33, 0.22)
CUBES = ('object_1', 'object_2', 'object_3')
# 지표의 발자국은 실제 몸(줄자 0.36 x 0.26 = 시뮬레이션 충돌 형상: 바퀴 바깥 ±0.13, 몸 앞 0.15·뒤 0.166)이다. Nav2 발자국 0.38 x 0.28은
# 여유 1 cm가 든 값이라 그걸로 재면 접촉이 없는데도 간격이 음수로 나왔다(상자 이동 0.0 cm, 2026-10-19).
# The metric footprint is the real body (tape-measured 0.36 x 0.26, = the simulated collision shape). Nav2's 0.38 x 0.28 carries
# a 1 cm margin and reported negative gaps with no contact (box moved 0.0 cm).
FOOTPRINT_HALF = (0.166, 0.13)    # URDF collision extents: rear shell 0.166, front 0.15, wheels +-0.13 (conservative, symmetric)
# 시뮬레이션 방에 맞춘 좌표(2026-10-19). 실기 F2 좌표는 A (1.02, 0.37) / B (1.00, 1.45) / 상자 (1.21, 1.00)이지만, 스캔한 방 메쉬는
# y >= 1.50에 벽 밑 경사면(높이 9~26 cm)이 있어 B가 로컬 코스트맵에서 내접 영역이 되고 컨트롤러가 B 앞에서 멈춘다
# (tools/sim/costmap_probe.py). 북쪽 끝을 20 cm 내리고 상자도 같이 내렸다(상자와 경로선의 상대 배치는 그대로).
# Simulation-room coordinates. The real F2 geometry is A (1.02, 0.37), B (1.00, 1.45), box (1.21, 1.00), but the scanned mesh
# has a wall-foot ramp at y >= 1.50 that makes B inscribed in the local costmap; the north end and the box were lowered 20 cm.
A, B = (1.02, 0.30), (1.00, 1.25)
SCENARIOS = {
    'S1': {'box': (1.21, 0.78), 'legs': {'AB': ((0.55, 0.40, 90.0), (0.55, 1.20))}},
    'S2': {'box': (1.21, 0.78), 'legs': {'AB': ((*A, 83.0), B), 'BA': ((*B, -97.0), A)}},
    'S4': {'box': (1.00, 0.78), 'legs': {'AB': ((*A, 83.0), B), 'BA': ((*B, -97.0), A)}},
}
# 동적 장애물 시나리오 D1~D4(8.16): 정지 상자 object_0은 방 밖으로 치우고 dyn_obstacles.py의 모델을 움직인다.
# Dynamic-obstacle scenarios: object_0 is parked away; the models of dyn_obstacles.py move (motions rebuilt every trial).
for _name, _sc in DYN.scenarios().items():
    SCENARIOS[_name] = {'box': DYN.OBJECT_0_PARK, 'legs': _sc['legs'], 'dyn': True}
DYN_MODELS = ('person_0', 'dyn_box', 'gate_l', 'gate_r', 'person_1')   # new models go last (column layout)
FIELDS = ['tag', 'scenario', 'leg', 'n', 'stamp', 'success', 'status', 'nav_status', 'nav_time_s', 'approach_status',
          'approach_time_s', 'time_s', 'pos_err_m', 'yaw_err_deg',
          'min_clearance_m', 'box_moved_m', 'detour_width_m', 'vy_flips_near', 'vy_flips_per_s_near',
          'stopped_s_near', 'near_time_s', 'heading_dev_deg_near', 'heading_dev_deg_all', 'plan_flips',
          'plan_sides', 'n_plans', 'amcl_init_err_m', 'amcl_end_err_m',
          'dyn_min_gap_m', 'dyn_contact', 'dyn_contact_moving', 'dyn_stop_gap_m', 'dyn_wait_s', 'dyn_resume_delay_s',
          'dyn_blocked_s']


def quat_yaw(q):
    return math.atan2(2 * (q['w'] * q['z'] + q['x'] * q['y']), 1 - 2 * (q['y'] ** 2 + q['z'] ** 2))


class GroundTruth:
    """Streams Gazebo's dynamic poses (`gz topic --json-output`, through a pty so it is line buffered)."""

    def __init__(self):
        self.rows, self.latest, self.recording = [], None, False
        master, slave = pty.openpty()
        self.proc = subprocess.Popen(
            ['gz', 'topic', '-e', '-t', f'/world/{WORLD}/dynamic_pose/info', '--json-output'],
            stdout=slave, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)
        os.close(slave)
        self.fd = master
        self.alive = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        buf = b''
        while self.alive:
            try:
                chunk = os.read(self.fd, 65536)
            except OSError:
                break
            buf += chunk
            while b'\n' in buf:
                line, buf = buf.split(b'\n', 1)
                line = line.strip()
                if not line.startswith(b'{'):
                    continue
                try:
                    self._on(json.loads(line))
                except ValueError:
                    continue

    def _on(self, m):
        st = m.get('header', {}).get('stamp', {})
        t = int(st.get('sec', 0)) + float(st.get('nsec', 0)) * 1e-9
        robot = box = None
        dyn = {}
        for p in m.get('pose', []):
            name = p.get('name')
            if name not in ('jetrover', BOX) + DYN_MODELS:
                continue
            pos = p.get('position', {})
            o = p.get('orientation', {})
            q = {'x': o.get('x', 0.0), 'y': o.get('y', 0.0), 'z': o.get('z', 0.0), 'w': o.get('w', 0.0)}
            if not any(q.values()):
                q['w'] = 1.0
            val = (pos.get('x', 0.0), pos.get('y', 0.0), quat_yaw(q))
            if name == 'jetrover' and robot is None:
                robot = val
            elif name == BOX and box is None:
                box = val
            elif name in DYN_MODELS and name not in dyn:
                dyn[name] = val
        if robot and box:
            # 열: t, 로봇 x y yaw, 상자 x y yaw, 그다음 DYN_MODELS 순서로 x y yaw (없으면 nan)
            # columns: t, robot, box, then each of DYN_MODELS (nan when absent)
            nan3 = (float('nan'),) * 3
            row = (t, *robot, *box, *[v for name in DYN_MODELS for v in dyn.get(name, nan3)])
            self.latest = row
            if self.recording:
                self.rows.append(row)

    def stop(self):
        self.alive = False
        try:
            os.killpg(self.proc.pid, signal.SIGINT)
        except ProcessLookupError:
            pass


class Runner(Node):
    def __init__(self):
        super().__init__('avoid_trials', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.buf = tf2_ros.Buffer()
        self.tfl = tf2_ros.TransformListener(self.buf, self)
        self.cmd, self.plans = [], []
        self.create_subscription(Twist, '/cmd_vel_nav', lambda m: self.cmd.append(
            (self.now(), m.linear.x, m.linear.y, m.angular.z)), 50)
        # 명령 사슬의 뒷단계와 충돌 감시기 상태: 컨트롤러 명령(/cmd_vel_nav)이 로봇까지 가는지 보려고(2026-10-19)
        # Later stages of the command chain and the collision monitor, to see where a command is lost.
        self.smooth, self.out, self.cm = [], [], []
        self.create_subscription(Twist, '/cmd_vel_smoothed', lambda m: self.smooth.append(
            (self.now(), m.linear.x, m.linear.y, m.angular.z)), 50)
        self.create_subscription(Twist, '/cmd_vel', lambda m: self.out.append(
            (self.now(), m.linear.x, m.linear.y, m.angular.z)), 50)
        self.create_subscription(CollisionMonitorState, '/collision_monitor_state', lambda m: self.cm.append(
            (self.now(), int(m.action_type), m.polygon_name)), 20)
        self.create_subscription(Path, '/plan', self._on_plan, 10)
        self.init_pub = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 1)
        self.client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.approach = ActionClient(self, NavigateToPose, 'precise_approach')
        self.clear_local = self.create_client(ClearEntireCostmap, '/local_costmap/clear_entirely_local_costmap')
        self.clear_global = self.create_client(ClearEntireCostmap, '/global_costmap/clear_entirely_global_costmap')

    def now(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def _on_plan(self, m):
        if m.poses:
            self.plans.append((self.now(), np.array([[p.pose.position.x, p.pose.position.y] for p in m.poses])))

    def spin(self, secs):
        t0 = time.time()
        while time.time() - t0 < secs:
            rclpy.spin_once(self, timeout_sec=0.02)

    def clear_costmaps(self):
        """Clear both costmaps (call after a teleport).

        한글: 순간이동하면 map->odom이 점프해서 odom 프레임 로컬 코스트맵의 옛 장애물 표시가 엉뚱한 자리의 유령 장애물이 된다.
        다회차 시험에서 첫 회차 뒤에 출발점에서 맴돌던 정지가 이것이었다(2026-10-19). 회차마다 지운다.
        A teleport makes map->odom jump, so old marks of the odom-frame local costmap become ghost obstacles at wrong places.
        """
        for cli in (self.clear_local, self.clear_global):
            if cli.wait_for_service(timeout_sec=3.0):
                fut = cli.call_async(ClearEntireCostmap.Request())
                rclpy.spin_until_future_complete(self, fut, timeout_sec=3.0)

    def amcl_pose(self):
        try:
            t = self.buf.lookup_transform('map', 'base_footprint', rclpy.time.Time())
        except Exception:  # noqa: BLE001
            return None
        q = t.transform.rotation
        return (t.transform.translation.x, t.transform.translation.y,
                math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z)))

    def set_initial_pose(self, x, y, yaw):
        m = PoseWithCovarianceStamped()
        m.header.frame_id = 'map'
        m.pose.pose.position.x, m.pose.pose.position.y = x, y
        m.pose.pose.orientation.z, m.pose.pose.orientation.w = math.sin(yaw / 2), math.cos(yaw / 2)
        m.pose.covariance[0] = m.pose.covariance[7] = 0.0025
        m.pose.covariance[35] = 0.003
        for _ in range(3):
            self.init_pub.publish(m)
            self.spin(0.3)


def gz_set_pose(name, x, y, z, yaw_deg=0.0):
    yaw = math.radians(yaw_deg)
    req = (f'name: "{name}", position: {{x: {x}, y: {y}, z: {z}}}, '
           f'orientation: {{z: {math.sin(yaw / 2)}, w: {math.cos(yaw / 2)}}}')
    subprocess.run(['gz', 'service', '-s', f'/world/{WORLD}/set_pose', '--reqtype', 'gz.msgs.Pose',
                    '--reptype', 'gz.msgs.Boolean', '--timeout', '3000', '--req', req],
                   capture_output=True, check=False)


def setup_leg(node, gt, scen, start, box):
    """Teleport box, cubes and robot; give AMCL the ground-truth pose; returns the AMCL error before the goal."""
    for c in CUBES:
        gz_set_pose(c, 0.45, 1.35, -3.0)
    gz_set_pose(BOX, box[0], box[1], 0.055)
    gz_set_pose('jetrover', start[0], start[1], 0.01, start[2])
    node.spin(1.5)
    yaw = math.radians(start[2])
    err = float('nan')
    for _ in range(3):
        node.set_initial_pose(start[0], start[1], yaw)
        node.spin(3.0)
        p = node.amcl_pose()
        if p is not None:
            err = math.hypot(p[0] - start[0], p[1] - start[1])
            if err < 0.05:
                break
    node.clear_costmaps()
    node.spin(3.0)        # costmaps refill from the sensors after the clear / 지운 뒤 센서로 다시 채워질 시간
    return err


def run_trial(node, gt, tag, scen, leg, n, timeout, quiet=False, approach=False, bt=''):
    spec = SCENARIOS[scen]
    start, goal_xy = spec['legs'][leg]
    driver = getattr(node, 'driver', None) if spec.get('dyn') else None
    if spec.get('dyn') and driver is None:
        raise SystemExit(f'{scen} needs the set_pose bridge (dynamic obstacles)')
    if driver:
        driver.park_all()
    amcl_init_err = setup_leg(node, gt, scen, start, spec['box'])
    line_yaw = math.atan2(goal_xy[1] - start[1], goal_xy[0] - start[0])
    goal = (goal_xy[0], goal_xy[1], line_yaw)
    start_rad = (start[0], start[1], math.radians(start[2]))
    if not node.client.wait_for_server(timeout_sec=10.0):
        raise SystemExit('navigate_to_pose not available')
    node.cmd.clear()
    node.plans.clear()
    node.smooth.clear()
    node.out.clear()
    node.cm.clear()
    gt.rows.clear()
    gt.recording = True
    goal_msg = NavigateToPose.Goal()
    goal_msg.pose = PoseStamped()
    goal_msg.pose.header.frame_id = 'map'
    goal_msg.pose.pose.position.x, goal_msg.pose.pose.position.y = goal[0], goal[1]
    goal_msg.pose.pose.orientation.z, goal_msg.pose.pose.orientation.w = math.sin(line_yaw / 2), math.cos(line_yaw / 2)
    # 목표마다 BT 선택(9.5, 정밀 도착 BT 시험) / per-goal BT (precise-arrival BT tests); '' = default BT
    goal_msg.behavior_tree = bt
    status, t0 = None, time.time()
    nav_error_code, nav_error_msg = 0, ''
    if driver:
        driver.begin(DYN.scenarios()[scen]['motions'], start[:2], goal_xy, node.now())
    send = node.client.send_goal_async(goal_msg)
    rclpy.spin_until_future_complete(node, send)
    handle = send.result()
    if not handle.accepted:
        status = 'rejected'
    else:
        res = handle.get_result_async()
        while not res.done():
            rclpy.spin_once(node, timeout_sec=0.02)
            if time.time() - t0 > timeout:
                handle.cancel_goal_async()
                status = 'timeout'
                break
        if status is None:
            status = {4: 'succeeded', 5: 'canceled', 6: 'aborted'}.get(res.result().status, str(res.result().status))
            nav_error_code = int(res.result().result.error_code)
            nav_error_msg = str(getattr(res.result().result, 'error_msg', ''))
    nav_status, t_nav_end = status, node.now()
    approach_status, approach_time = '', 0.0
    if approach:
        # 정밀 접근: Nav2가 끝났을 때 로봇이 목표 0.28 m 이내면 마지막 위치·방향을 메카넘으로 맞춘다.
        # Precise approach when the robot is within 0.28 m of the goal after Nav2 finished (any Nav2 status).
        g = gt.latest
        dist = math.hypot(g[1] - goal[0], g[2] - goal[1]) if g else float('inf')
        if dist <= 0.28 and node.approach.wait_for_server(timeout_sec=3.0):
            t_ap = node.now()
            send = node.approach.send_goal_async(goal_msg)
            rclpy.spin_until_future_complete(node, send)
            ah = send.result()
            if not ah.accepted:
                approach_status = 'rejected'
            else:
                ares = ah.get_result_async()
                wall0 = time.time()
                while not ares.done() and time.time() - wall0 < 60.0:
                    rclpy.spin_once(node, timeout_sec=0.02)
                approach_status = ({4: 'succeeded', 5: 'canceled', 6: 'aborted'}.get(ares.result().status, 'other')
                                   if ares.done() else 'timeout')
            approach_time = node.now() - t_ap
            status = 'succeeded' if approach_status == 'succeeded' else (nav_status if nav_status != 'succeeded' else 'approach_failed')
        else:
            approach_status = 'skipped' if dist > 0.28 else 'no_server'
    node.spin(1.5)
    gt.recording = False
    dyn_log = []
    if driver:
        dyn_log = [list(x) for x in driver.log[::max(1, len(driver.log) // 600)]]
        driver.end()
    amcl_end = node.amcl_pose()
    rows = np.array(gt.rows)
    if len(rows) < 10:
        print(f'{tag} {scen}{leg} #{n}: only {len(rows)} ground-truth samples - skipped', flush=True)
        return None
    g = {k: rows[:, i] for i, k in enumerate(('t', 'rx', 'ry', 'ryaw', 'bx', 'by', 'byaw'))}   # extra columns: DYN_MODELS
    cmd = np.array(node.cmd) if node.cmd else np.zeros((0, 4))
    c = {'t': cmd[:, 0], 'vx': cmd[:, 1], 'vy': cmd[:, 2], 'wz': cmd[:, 3]}
    out = M.summarize(g, c, node.plans, start_rad, goal, BOX_SIZE, FOOTPRINT_HALF, status)
    out['nav_status'], out['approach_status'] = nav_status, approach_status
    out['nav_time_s'], out['approach_time_s'] = float(t_nav_end - g['t'][0]), float(approach_time)
    out['success'] = bool(status == 'succeeded' and out['min_clearance_m'] > 0 and out['box_moved_m'] < 0.02)
    if spec.get('dyn'):
        # 움직이는 장애물 지표: 시나리오에서 쓰는 모델만(정답 열 7~9 person_0, 10~12 dyn_box, 없으면 방 밖으로 취급).
        # Dynamic-obstacle metrics for the models this scenario moves (nan columns = absent -> treated as parked).
        used = {mo.model for mo in DYN.scenarios()[scen]['motions']}
        obstacles = []
        sizes = {'dyn_box': DYN.DYN_BOX_SIZE, 'gate_l': DYN.GATE_SIZE, 'gate_r': DYN.GATE_SIZE}
        for k, name in enumerate(DYN_MODELS):
            col = 7 + 3 * k
            if name in used and rows.shape[1] > col + 2:
                ox = np.where(np.isfinite(rows[:, col]), rows[:, col], 99.0)
                ob = {'kind': 'person' if name.startswith('person') else 'box', 'x': ox,
                      'y': np.nan_to_num(rows[:, col + 1]), 'yaw': np.nan_to_num(rows[:, col + 2])}
                if name in sizes:
                    ob['half'] = (sizes[name][0] / 2, sizes[name][1] / 2)
                if name in DYN.FEET:
                    ob['feet'] = DYN.FEET[name]      # 모델마다 발 모양이 다름 / per-model feet
                obstacles.append(ob)
        out.update(M.dynamic_summary(g, obstacles, start_rad, goal, FOOTPRINT_HALF, DYN.PERSON_LEGS, DYN.PERSON_LEG_R,
                                     (DYN.DYN_BOX_SIZE[0] / 2, DYN.DYN_BOX_SIZE[1] / 2), feet=DYN.PERSON_FEET))
        out['success'] = bool(status == 'succeeded' and not out['dyn_contact'])
    out['amcl_init_err_m'] = amcl_init_err
    out['nav_error_code'], out['nav_error_msg'], out['bt'] = nav_error_code, nav_error_msg, os.path.basename(bt)
    out['amcl_end_err_m'] = (float(math.hypot(amcl_end[0] - g['rx'][-1], amcl_end[1] - g['ry'][-1]))
                             if amcl_end else float('nan'))
    stamp = time.strftime('%Y%m%d_%H%M%S')
    row = {'tag': tag, 'scenario': scen, 'leg': leg, 'n': n, 'stamp': stamp, **out}
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    # 열이 바뀌었으면 옛 파일은 이름을 바꿔 보관하고 새 머리글로 시작한다(머리글이 어긋나면 summary가 틀린 열을 읽는다).
    # If the columns changed, keep the old file under a new name and start fresh (a stale header misreads every column).
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH) as f:
            if f.readline().strip().split(',') != FIELDS:
                os.rename(CSV_PATH, CSV_PATH.replace('.csv', f'_old_{time.strftime("%Y%m%d_%H%M%S")}.csv'))
    new = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, 'a', newline='') as f:
        w = csv.DictWriter(f, FIELDS, extrasaction='ignore')
        if new:
            w.writeheader()
        w.writerow({k: (f'{v:.4f}' if isinstance(v, float) else v) for k, v in row.items()})
    os.makedirs(JSON_DIR, exist_ok=True)
    step = max(1, len(rows) // 400)
    with open(os.path.join(JSON_DIR, f'{tag}_{scen}_{leg}_{n}_{stamp}.json'), 'w') as f:
        def thin(lst, n=400):
            return [list(x) for x in lst[::max(1, len(lst) // n)]]
        json.dump({**row, 'start': start_rad, 'goal': goal, 'gt': rows[::step].round(4).tolist(),
                   'cmd': cmd[::max(1, len(cmd) // 400)].round(4).tolist(),
                   'smoothed': thin(node.smooth), 'out': thin(node.out), 'collision_monitor': thin(node.cm, 200),
                   'dyn_cmd': dyn_log}, f)
    if not quiet and spec.get('dyn'):
        print(f'{tag} {scen}{leg} #{n}: {"OK  " if out["success"] else "FAIL"} {status:9s} {out["time_s"]:5.1f} s  '
              f'err {out["pos_err_m"] * 100:4.1f} cm  dyn gap {out["dyn_min_gap_m"] * 100:5.1f} cm  '
              f'stop gap {out["dyn_stop_gap_m"] * 100:5.1f} cm  wait {out["dyn_wait_s"]:4.1f} s  '
              f'resume {out["dyn_resume_delay_s"]:4.1f} s  blocked {out["dyn_blocked_s"]:4.1f} s  '
              f'{"CONTACT(robot moving) " if out["dyn_contact_moving"] else ("contact(robot still) " if out["dyn_contact"] else "")}'
              f'hdg {out["heading_dev_deg_all"]:4.0f} deg'
              + (f'  [nav {nav_status} {out["nav_time_s"]:.1f} s, approach {approach_status} {approach_time:.1f} s]'
                 if approach else ''),
              flush=True)
    elif not quiet:
        print(f'{tag} {scen}{leg} #{n}: {"OK  " if out["success"] else "FAIL"} {status:9s} {out["time_s"]:5.1f} s  '
              f'err {out["pos_err_m"] * 100:4.1f} cm  gap {out["min_clearance_m"] * 100:5.1f} cm  '
              f'detour {out["detour_width_m"] * 100:4.1f} cm  flips {out["vy_flips_near"]:2d}  '
              f'stop {out["stopped_s_near"]:4.1f} s  hdg {out["heading_dev_deg_near"]:4.0f} deg  '
              f'plan flips {out["plan_flips"]}  amcl {amcl_init_err * 100:.1f}/{out["amcl_end_err_m"] * 100:.1f} cm'
              + (f'  [nav {nav_status} {out["nav_time_s"]:.1f} s, approach {approach_status} {approach_time:.1f} s]'
                 if approach else ''),
              flush=True)
    return out


def summary(prefix):
    if not os.path.exists(CSV_PATH):
        sys.exit(f'no {CSV_PATH}')
    rows = [r for r in csv.DictReader(open(CSV_PATH)) if r['tag'].startswith(prefix)]
    groups = {}
    for r in rows:
        groups.setdefault((r['tag'], r['scenario'], r['leg']), []).append(r)

    def stat(rs, key, scale=1.0):
        v = [float(r[key]) * scale for r in rs if r[key] not in ('', 'nan')]
        return f'{np.mean(v):6.1f}±{np.std(v):4.1f}' if v else '     -     '
    print(f'{"tag":14s} {"scen":5s} {"ok":>6s} {"time s":>11s} {"err cm":>11s} {"gap cm":>11s} {"detour cm":>11s} '
          f'{"vy flips":>11s} {"stop s":>11s} {"hdg dev":>11s} {"plan flips":>11s}')
    for (tag, scen, leg), rs in sorted(groups.items()):
        ok = sum(r['success'] == 'True' for r in rs)
        if SCENARIOS.get(scen, {}).get('dyn'):
            continue
        print(f'{tag:14s} {scen + leg:5s} {ok:3d}/{len(rs):<2d} {stat(rs, "time_s")} {stat(rs, "pos_err_m", 100)} '
              f'{stat(rs, "min_clearance_m", 100)} {stat(rs, "detour_width_m", 100)} {stat(rs, "vy_flips_near")} '
              f'{stat(rs, "stopped_s_near")} {stat(rs, "heading_dev_deg_near")} {stat(rs, "plan_flips")}')
    dyn = {k: v for k, v in groups.items() if SCENARIOS.get(k[1], {}).get('dyn')}
    if dyn:
        # 동적 장애물 시나리오 요약(8.16): 접촉 수, 장애물과 최소 간격(최소/평균), 정지 시 간격, 대기, 재출발 지연(최대)
        print(f'{"tag":14s} {"scen":5s} {"ok":>6s} {"contact":>7s} {"min gap cm":>10s} {"gap cm":>11s} {"stop gap cm":>11s} '
              f'{"wait s":>11s} {"resume s":>11s} {"err cm":>11s} {"time s":>11s}')
    for (tag, scen, leg), rs in sorted(dyn.items()):
        ok = sum(r['success'] == 'True' for r in rs)
        contact = sum(r.get('dyn_contact') == 'True' for r in rs)
        gaps = [float(r['dyn_min_gap_m']) * 100 for r in rs if r.get('dyn_min_gap_m') not in ('', 'nan', None)]
        res = [float(r['dyn_resume_delay_s']) for r in rs if r.get('dyn_resume_delay_s') not in ('', 'nan', None)]
        print(f'{tag:14s} {scen + leg:5s} {ok:3d}/{len(rs):<2d} {contact:7d} {(min(gaps) if gaps else float("nan")):10.1f} '
              f'{stat(rs, "dyn_min_gap_m", 100)} {stat(rs, "dyn_stop_gap_m", 100)} {stat(rs, "dyn_wait_s")} '
              f'{(max(res) if res else float("nan")):11.1f} {stat(rs, "pos_err_m", 100)} {stat(rs, "time_s")}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run')
    r.add_argument('--tag', required=True, help='condition label, e.g. dwb, mppi, dwb_h1')
    # 쉼표로 여러 개(2026-10-29, Gazebo·Nav2를 한 번만 띄움) / comma-separated list runs several in one bringup
    r.add_argument('--scenario', default='S2', help='|'.join(sorted(SCENARIOS) + ['all', 'dyn']) + ', or a comma list (D10,S2)')
    r.add_argument('--repeats', type=int, default=3)
    r.add_argument('--timeout', type=float, default=90.0, help='wall-clock seconds per leg')
    r.add_argument('--approach', action='store_true', help='call the precise_approach action after Nav2 (node must be running)')
    r.add_argument('--bt', default='', help='behavior_tree for each goal (e.g. the precise-arrival BT); default BT if empty')
    s = sub.add_parser('summary')
    s.add_argument('--prefix', default='')
    args = ap.parse_args()
    if args.cmd == 'summary':
        return summary(args.prefix)
    if os.environ.get('ROS_DOMAIN_ID') != '31':
        sys.exit('export ROS_DOMAIN_ID=31 first (keep away from the robot, domain 25)')
    rclpy.init()
    node, gt = Runner(), GroundTruth()
    # all = 정지 상자 S1/S2/S4(예전과 같음), dyn = 동적 D1~D4 / all keeps its old meaning (static scenarios), dyn = D1-D4
    if args.scenario in ('all', 'dyn'):
        scens = [s for s in sorted(SCENARIOS) if bool(SCENARIOS[s].get('dyn')) == (args.scenario == 'dyn')
                 and not s.startswith('N')]   # N50/N60 (narrow passage) run by name / 좁은 통로는 이름으로
    else:
        scens = args.scenario.split(',')
        bad = [s for s in scens if s not in SCENARIOS]
        if bad:
            sys.exit(f'unknown scenario(s) {bad}')
    if any(SCENARIOS[s].get('dyn') for s in scens):
        # 동적 장애물 구동기: set_pose 서비스 브리지가 떠 있어야 한다(sim_avoid_run.sh가 띄움).
        node.driver = DYN.ObstacleDriver(node, WORLD, lambda: gt.latest[1:3] if gt.latest else None)
        if not node.driver.ready():
            raise SystemExit('set_pose bridge not available (ros_gz_bridge parameter_bridge .../set_pose@...)')
    try:
        node.spin(3.0)
        if gt.latest is None:
            gt.recording = False
            node.spin(2.0)
        for scen in scens:
            for n in range(1, args.repeats + 1):
                for leg in SCENARIOS[scen]['legs']:
                    run_trial(node, gt, args.tag, scen, leg, n, args.timeout, approach=args.approach, bt=args.bt)
    finally:
        gt.stop()
        summary(args.tag)
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
