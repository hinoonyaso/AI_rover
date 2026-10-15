#!/usr/bin/env python3
# 한글: T7 MoveIt 실기 통합 시험 — MoveGroup 액션으로 관절 목표·이름 자세·그리퍼·집기 시퀀스를 실행하고 기준을 잰다. 팔이 움직인다.
#       전제: base_node(arm_command_enabled:=true) + move_group mode:=real + execution.launch dry_run:=false.
#       기준(prd/arm-control-path.md R9): 관절 목표 연속 성공(정착 오차 ≤ 0.05 rad), 이름 자세 왕복, 그리퍼 열기·닫기, 서보 온도는 기록만,
#       IMU 끊김 0. 시퀀스: home → 열기 → pregrasp_floor → grasp_floor → arm/grasp → 들기 → 내려놓기 → arm/release → home.
"""T7: MoveIt on the real arm via the MoveGroup action. THE ARM MOVES.

Needs base_node (arm_command_enabled:=true), move_group mode:=real and execution.launch dry_run:=false.
Usage:
  python3 tools/manipulation/moveit_t7.py joint-goals [--count 10] [--scale 0.3]
  python3 tools/manipulation/moveit_t7.py named       [--count 5]        # home <-> pregrasp_floor
  python3 tools/manipulation/moveit_t7.py gripper     [--count 10]       # gripper_open <-> gripper_closed
  python3 tools/manipulation/moveit_t7.py sequence    [--count 1] [--first-delay 20]
Every move: MoveIt result, then the settled /joint_states error vs the target (pass <= --tol, 0.05 rad).
Records arm/servo_stats temperatures (warns from 75 C; stops only with --temp-stop) and /imu/data_raw gaps (> 0.5 s).
Prints one line per move and a summary; raw JSON in Log/moveit_t7_<mode>_<time>.json. Exit 1 on a failure.
"""
import argparse
import json
import os
import sys
import time
import xml.etree.ElementTree as ET

import rclpy
from ament_index_python.packages import get_package_share_directory
from diagnostic_msgs.msg import DiagnosticArray
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, JointConstraint, MoveItErrorCodes
from rclpy.action import ActionClient
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu, JointState
from std_msgs.msg import Bool, String
from jetrover_interfaces.action import Grasp
from jetrover_interfaces.srv import Release

ARM = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5']
ERR = {v: k for k, v in MoveItErrorCodes.__dict__.items() if k.isupper() and isinstance(v, int)}


def named_states():
    """Read the group_state values from the installed SRDF (same file move_group loads)."""
    srdf = os.path.join(get_package_share_directory('jetrover_manipulation'), 'config', 'jetrover.srdf')
    out = {}
    for gs in ET.parse(srdf).getroot().findall('group_state'):
        out[gs.get('name')] = {j.get('name'): float(j.get('value')) for j in gs.findall('joint')}
    return out


class Rig:
    def __init__(self, args):
        rclpy.init()
        self.args = args
        self.n = rclpy.create_node('moveit_t7')
        self.js, self.temps, self.grasp_state = {}, {}, {'name': None}
        self.imu_last, self.imu_gaps, self.imu_max_gap = None, 0, 0.0
        self.n.create_subscription(JointState, 'joint_states',
                                   lambda m: self.js.update(dict(zip(m.name, m.position))), 10)
        self.n.create_subscription(DiagnosticArray, 'arm/servo_stats', self.on_stats, 10)
        # base_node는 IMU를 best-effort로 낸다 — reliable 구독이면 아무것도 못 받는다(L1에서 확인)
        # base_node publishes the IMU best-effort: a reliable subscription receives nothing
        self.n.create_subscription(Imu, 'imu/data_raw', self.on_imu, qos_profile_sensor_data)
        self.imu_count = 0
        self.n.create_subscription(String, 'arm/grasp_state', lambda m: self.grasp_state.update(name=m.data), 10)
        self.lifted = self.n.create_publisher(Bool, 'arm/object_lifted', 10)
        self.move = ActionClient(self.n, MoveGroup, 'move_action')
        self.grasp = ActionClient(self.n, Grasp, 'arm/grasp')
        self.release = self.n.create_client(Release, 'arm/release')
        self.rows = []

    def on_stats(self, m):
        for st in m.status:
            v = {k.key: float(k.value) for k in st.values}
            if v.get('temp_c', -1) >= 0:
                self.temps[st.name] = v['temp_c']

    def on_imu(self, m):
        t = time.monotonic()
        self.imu_count += 1
        if self.imu_last is not None:
            gap = t - self.imu_last
            self.imu_max_gap = max(self.imu_max_gap, gap)
            if gap > 0.5:
                self.imu_gaps += 1
        self.imu_last = t

    def spin(self, sec):
        t0 = time.monotonic()
        while time.monotonic() - t0 < sec:
            rclpy.spin_once(self.n, timeout_sec=0.02)

    def wait(self, fut, limit):
        t0 = time.monotonic()
        while not fut.done() and time.monotonic() - t0 < limit:
            rclpy.spin_once(self.n, timeout_sec=0.02)
        return fut.done()

    def hot(self):
        # 온도로 멈추지 않는다(2026-10-15 사용자 결정: 조건 때문에 시험이 계속 막힘). --temp-stop을 주면 그때만 멈춘다.
        # 경고만 출력 — 서보는 85 ℃에서 스스로 토크를 끊으므로(팔이 처질 수 있음) 기록은 남긴다.
        # No temperature stop by default (user decision); --temp-stop re-enables it. Warn from 75 C: the servo itself
        # cuts its torque at 85 C, which can drop the arm.
        hottest = max(self.temps.values(), default=-1.0)
        if hottest >= 75.0:
            print(f'  WARNING servo temperature {hottest:.0f} C (servo cuts out at 85 C): {self.temps}', flush=True)
        return self.args.temp_stop is not None and hottest >= self.args.temp_stop

    def go(self, label, group, target):
        """Plan + execute a joint goal, then measure the settled error. Returns True on pass."""
        goal = MoveGroup.Goal()
        r = goal.request
        r.group_name = group
        r.num_planning_attempts = 3
        r.allowed_planning_time = 5.0
        r.max_velocity_scaling_factor = self.args.scale
        r.max_acceleration_scaling_factor = self.args.scale
        r.goal_constraints = [Constraints(joint_constraints=[
            JointConstraint(joint_name=j, position=p, tolerance_above=0.01, tolerance_below=0.01, weight=1.0)
            for j, p in target.items()])]
        goal.planning_options.plan_only = False
        t0 = time.monotonic()
        fut = self.move.send_goal_async(goal)
        ok = self.wait(fut, 10) and fut.result() is not None and fut.result().accepted
        code = None
        if ok:
            rf = fut.result().get_result_async()
            ok = self.wait(rf, 90)
            code = rf.result().result.error_code.val if ok else None
        took = time.monotonic() - t0
        self.spin(self.args.settle)
        err = {j: abs(self.js.get(j, float('nan')) - p) for j, p in target.items()}
        worst = max(err.values()) if err else float('nan')
        passed = code == MoveItErrorCodes.SUCCESS and worst <= self.args.tol
        row = {'move': label, 'group': group, 'code': ERR.get(code, code), 'seconds': round(took, 1),
               'max_err_rad': round(worst, 4), 'err': {k: round(v, 4) for k, v in err.items()},
               'temps': dict(self.temps), 'pass': passed}
        self.rows.append(row)
        print(f'  {"PASS" if passed else "FAIL"}  {label}: {row["code"]}, {took:.1f} s, max err {worst:.3f} rad, '
              f'max temp {max(self.temps.values(), default=-1):.0f} C', flush=True)
        return passed

    def note(self, label, passed, detail):
        self.rows.append({'move': label, 'pass': bool(passed), 'detail': detail})
        print(f'  {"PASS" if passed else "FAIL"}  {label}: {detail}', flush=True)
        return passed


def joint_goals(rig, ns):
    home = ns['home']
    offsets = [('joint1', 0.2), ('joint1', -0.2), ('joint2', 0.2), ('joint2', -0.2), ('joint4', -0.2),
               ('joint5', 0.3), ('joint5', -0.3), ('joint3', -0.2), ('joint1', 0.3), ('joint2', 0.3)]
    ok = rig.go('home', 'arm', home)
    for k in range(rig.args.count):
        j, d = offsets[k % len(offsets)]
        tgt = dict(home)
        tgt[j] = home[j] + d
        ok = rig.go(f'goal {k + 1}: {j} {d:+.2f}', 'arm', tgt) and ok
        if rig.hot():
            return rig.note('temperature', False, f'stopped: {rig.temps}')
        if not ok and rig.args.stop_on_fail:
            break
    return rig.go('home', 'arm', home) and ok


def named(rig, ns):
    ok = True
    for k in range(rig.args.count):
        ok = rig.go(f'cycle {k + 1}: pregrasp_floor', 'arm', ns['pregrasp_floor']) and ok
        ok = rig.go(f'cycle {k + 1}: home', 'arm', ns['home']) and ok
        if rig.hot():
            return rig.note('temperature', False, f'stopped: {rig.temps}')
        if not ok and rig.args.stop_on_fail:
            break
    return ok


def gripper(rig, ns):
    ok = True
    for k in range(rig.args.count):
        ok = rig.go(f'{k + 1}: gripper_open', 'gripper', ns['gripper_open']) and ok
        ok = rig.go(f'{k + 1}: gripper_closed', 'gripper', ns['gripper_closed']) and ok
        if not ok and rig.args.stop_on_fail:
            break
    return rig.go('gripper_open', 'gripper', ns['gripper_open']) and ok


def sequence(rig, ns):
    ok_all = True
    for k in range(rig.args.count):
        print(f'sequence {k + 1}/{rig.args.count}', flush=True)
        steps_ok = (rig.go('home', 'arm', ns['home'])
                    and rig.go('open gripper', 'gripper', ns['gripper_open'])
                    and rig.go('pregrasp_floor', 'arm', ns['pregrasp_floor']))
        if not steps_ok:
            return False
        print(f'  put the cube on the floor mark under the gripper; descending in {rig.args.first_delay:g} s',
              flush=True)
        rig.spin(rig.args.first_delay)
        if not rig.go('grasp_floor', 'arm', ns['grasp_floor']):
            return False
        g = Grasp.Goal()
        g.profile = 'cube3cm'
        fut = rig.grasp.send_goal_async(g)
        rig.wait(fut, 5)
        gh = fut.result()
        if gh is None or not gh.accepted:
            return rig.note('grasp accepted', False, 'refused')
        rf = gh.get_result_async()
        rig.wait(rf, 40)
        res = rf.result().result if rf.done() else None
        if not rig.note('grasp', res is not None and res.success,
                        f'reason {res.reason if res else None!r}, contact {res.contact_position if res else None}'):
            rig.go('pregrasp_floor (retreat)', 'arm', ns['pregrasp_floor'])
            return False
        rig.lifted.publish(Bool(data=True))
        lift_ok = rig.go('lift (pregrasp_floor)', 'arm', ns['pregrasp_floor'])
        rig.spin(2.0)
        held = rig.note('still holding after the lift', rig.grasp_state['name'] == 'Holding',
                        f'grasp state {rig.grasp_state["name"]}')
        place_ok = rig.go('place (grasp_floor)', 'arm', ns['grasp_floor'])
        rig.lifted.publish(Bool(data=False))
        rr = rig.release.call_async(Release.Request())
        rig.wait(rr, 5)
        rel_ok = rig.note('release', rr.done() and rr.result().success, 'arm/release')
        rig.spin(2.5)
        back_ok = rig.go('retreat (pregrasp_floor)', 'arm', ns['pregrasp_floor']) and rig.go('home', 'arm', ns['home'])
        ok = lift_ok and held and place_ok and rel_ok and back_ok
        ok_all = ok_all and ok
        if rig.hot():
            return rig.note('temperature', False, f'stopped: {rig.temps}')
        if not ok:
            break
    return ok_all


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('mode', choices=('joint-goals', 'named', 'gripper', 'sequence'))
    ap.add_argument('--count', type=int, default=None)
    ap.add_argument('--scale', type=float, default=0.3, help='MoveIt velocity/acceleration scaling')
    ap.add_argument('--tol', type=float, default=0.05, help='settled joint error pass limit (rad)')
    ap.add_argument('--settle', type=float, default=1.5, help='wait after a move before measuring (s)')
    ap.add_argument('--temp-stop', type=float, default=None, help='stop at this servo temperature (default: no stop)')
    ap.add_argument('--first-delay', type=float, default=20.0)
    ap.add_argument('--stop-on-fail', action='store_true')
    args = ap.parse_args()
    if args.count is None:
        args.count = {'joint-goals': 10, 'named': 5, 'gripper': 10, 'sequence': 1}[args.mode]

    ns = named_states()
    rig = Rig(args)
    if not rig.move.wait_for_server(timeout_sec=15):
        sys.exit('move_action not available: start move_group mode:=real')
    if args.mode == 'sequence' and (not rig.grasp.wait_for_server(timeout_sec=10)
                                    or not rig.release.wait_for_service(timeout_sec=10)):
        sys.exit('arm/grasp or arm/release not available (base_node arm_command_enabled:=true)')
    rig.spin(3.0)
    if not all(j in rig.js for j in ARM):
        sys.exit(f'no /joint_states for the arm yet: {sorted(rig.js)}')
    ok = {'joint-goals': joint_goals, 'named': named, 'gripper': gripper, 'sequence': sequence}[args.mode](rig, ns)
    os.makedirs('Log', exist_ok=True)
    path = 'Log/moveit_t7_%s_%s.json' % (args.mode, time.strftime('%Y%m%d_%H%M%S'))
    summary = {'mode': args.mode, 'scale': args.scale, 'imu_messages': rig.imu_count,
               'imu_gaps_over_0_5s': rig.imu_gaps,
               'imu_max_gap_s': round(rig.imu_max_gap, 3), 'max_temp_c': max(rig.temps.values(), default=-1),
               'moves': rig.rows}
    json.dump(summary, open(path, 'w'), indent=1)
    n_pass = sum(1 for r in rig.rows if r['pass'])
    imu = (f'IMU gaps > 0.5 s: {rig.imu_gaps} (max {rig.imu_max_gap:.2f} s, {rig.imu_count} msgs)'
           if rig.imu_count else 'IMU: NOT MEASURED (no messages)')
    print(f'SUMMARY {args.mode}: {n_pass}/{len(rig.rows)} passed, {imu}, '
          f'max servo temp {summary["max_temp_c"]:.0f} C; raw: {path}')
    rclpy.shutdown()
    sys.exit(0 if ok and n_pass == len(rig.rows) else 1)


if __name__ == '__main__':
    main()
