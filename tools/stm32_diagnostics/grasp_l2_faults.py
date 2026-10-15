#!/usr/bin/env python3
# 한글: T6 L2 실기 시험 2 — 접촉 파지의 이상·취소·배타 제어를 실제 서보로 확인한다. 그리퍼가 닫힌다. 팔(관절 1~5)은 움직이지 않는다.
#       base_node가 arm_command_enabled:=true로 떠 있어야 한다(타임아웃·고온 시나리오는 파라미터를 바꿔 직접 띄움 — 아래 Usage).
#       시나리오:
#         cancel-closing  닫는 중(Closing, 시작 후 4 s)에 취소 → 결과 Cancelled, 그리퍼가 시작 위치로 돌아감, Idle 복귀
#         cancel-squeeze  조이는 중(Squeeze)에 취소 → 결과 Cancelled, 그리퍼가 접촉 위치로 풀림(완전히 열지 않음), Idle 복귀
#         refuse-holding  Idle에서 그리퍼 명령 1회가 먹는지 대조 → 파지(HOLDING) → 그리퍼 명령 N회 → 위치 그대로·Holding 유지 → Release
#         timeout         (grasp_timeout_s를 짧게 띄운 base_node) 결과 Timeout, 그리퍼가 시작 위치로
#         temp-refuse     (grasp_temp_limit_c를 현재 온도보다 낮게 띄운 base_node) 결과 TempHigh, 그리퍼 명령 0(위치 그대로)
"""T6 L2 part 2: cancel / exclusive-control / fault checks of the contact grasp on the REAL gripper (arm joints stay).

Usage (base_node running with arm_command_enabled:=true; the cube goes between the open jaws when asked):
  python3 tools/stm32_diagnostics/grasp_l2_faults.py cancel-closing  [--trials 3] [--first-delay 20] [--gap 15]
  python3 tools/stm32_diagnostics/grasp_l2_faults.py cancel-squeeze  [--trials 2]
  python3 tools/stm32_diagnostics/grasp_l2_faults.py refuse-holding  [--commands 20]
  # timeout / temp-refuse need base_node started directly with an override, e.g.
  #   ros2 run jetrover_base base_node --ros-args \
  #     --params-file install/jetrover_base/share/jetrover_base/config/base.yaml \
  #     -p arm_command_enabled:=true -p grasp_timeout_s:=6.0          (or -p grasp_temp_limit_c:=30.0)
  python3 tools/stm32_diagnostics/grasp_l2_faults.py timeout     [--trials 2]
  python3 tools/stm32_diagnostics/grasp_l2_faults.py temp-refuse [--trials 2]
One PASS/FAIL line per trial check, a summary, raw JSON in Log/grasp_l2_faults_<scenario>_<time>.json. Exit 1 on a FAIL.
Dry run without hardware: the L1 fake RRC (grasp_l1_test.FakeRrc) + base_node on its pty; on the Jetson unset
FASTRTPS_DEFAULT_PROFILES_FILE (Wi-Fi-only profile) when using ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST.
"""
import argparse
import json
import math
import os
import sys
import time

import rclpy
from action_msgs.msg import GoalStatus
from rclpy.action import ActionClient
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from jetrover_interfaces.action import Grasp
from jetrover_interfaces.srv import Release

RPT = math.radians(240.0) / 1000.0     # rad per servo pulse
STATUS = {GoalStatus.STATUS_SUCCEEDED: 'succeeded', GoalStatus.STATUS_ABORTED: 'aborted',
          GoalStatus.STATUS_CANCELED: 'canceled'}


class Rig:
    def __init__(self):
        rclpy.init()
        self.n = rclpy.create_node('grasp_l2_faults')
        self.js, self.state, self.fb = {}, {'name': None}, {}
        self.n.create_subscription(JointState, 'joint_states',
                                   lambda m: self.js.update(dict(zip(m.name, m.position))), 10)
        self.n.create_subscription(String, 'arm/grasp_state', lambda m: self.state.update(name=m.data), 10)
        self.cmd = self.n.create_publisher(JointState, 'arm/command', 10)
        self.act = ActionClient(self.n, Grasp, 'arm/grasp')
        self.rel = self.n.create_client(Release, 'arm/release')

    def spin(self, sec):
        t0 = time.monotonic()
        while time.monotonic() - t0 < sec:
            rclpy.spin_once(self.n, timeout_sec=0.02)

    def wait(self, pred, limit):
        t0 = time.monotonic()
        while time.monotonic() - t0 < limit:
            rclpy.spin_once(self.n, timeout_sec=0.02)
            if pred():
                return True
        return False

    def gripper(self):
        """r_joint reading in pulses relative to the reading convention (rad / RPT)."""
        v = self.js.get('r_joint')
        return None if v is None else v / RPT

    def send_goal(self):
        self.fb.clear()

        def on_fb(f):
            self.fb.update(state=f.feedback.state, pos=f.feedback.gripper_position, contact=f.feedback.contact_position,
                           temp=f.feedback.temperature_c, elapsed=f.feedback.elapsed_s)
        g = Grasp.Goal()
        g.profile = 'cube3cm'
        fut = self.act.send_goal_async(g, feedback_callback=on_fb)
        self.wait(fut.done, 5)
        gh = fut.result()
        if gh is not None and gh.accepted:
            gh.result_future = gh.get_result_async()
        return gh

    def result(self, gh, limit=90):
        # goal 수락 직후 send_goal()에서 만든 future를 쓴다(늦게 요청하면 일찍 끝난 결과가 만료돼 status 0, 2026-10-15)
        # use the future requested right after acceptance (a late request lost an early result: status 0)
        rf = getattr(gh, 'result_future', None) or gh.get_result_async()
        self.wait(rf.done, limit)
        if not rf.done():
            return None, None
        r = rf.result()
        return STATUS.get(r.status, str(r.status)), r.result

    def release(self):
        rr = self.rel.call_async(Release.Request())
        self.wait(rr.done, 5)
        return bool(rr.done() and rr.result().success)

    def open_gripper(self, target_reading=300.0):
        """Open the gripper slowly to `target_reading` (reading units = 500 - pulse) in <= 0.25 rad steps."""
        for _ in range(12):
            cur = self.js.get('r_joint')
            if cur is None or abs(target_reading * RPT - cur) < 0.02:
                break
            self.gripper_cmd(cur + max(-0.25, min(0.25, target_reading * RPT - cur)))
            self.spin(2.0)
        return self.gripper()

    def gripper_cmd(self, rad):
        m = JointState()
        m.name = ['r_joint']
        m.position = [rad]
        self.cmd.publish(m)


def check(rows, name, ok, detail):
    rows.append({'check': name, 'pass': bool(ok), 'detail': detail})
    print(f'  {"PASS" if ok else "FAIL"}  {name}: {detail}', flush=True)
    return ok


def run_cancel(rig, args, phase, rows, raw):
    for k in range(1, args.trials + 1):
        wait_s = args.first_delay if k == 1 else args.gap
        if rig.gripper() is not None and rig.gripper() < 250:
            # Squeeze 취소는 그리퍼를 접촉 위치에 둔다 — 다음 회차 전에 연다(시작 위치 ≤ 450 펄스 조건)
            # a squeeze cancel leaves the jaws at the contact: open before the next trial (start must be open)
            print(f'  opening the gripper first (reading {rig.gripper():.0f})', flush=True)
            rig.open_gripper()
        print(f'trial {k}/{args.trials} ({phase}): put the cube between the open jaws; closing starts in {wait_s:g} s',
              flush=True)
        rig.spin(wait_s)
        start = rig.gripper()
        gh = rig.send_goal()
        if gh is None or not gh.accepted:
            check(rows, f'{phase}#{k} goal accepted', False, 'refused')
            continue
        if phase == 'cancel-closing':
            hit = rig.wait(lambda: rig.fb.get('state') == 'Closing' and rig.fb.get('elapsed', 0) >= 4.0, 30)
        else:
            hit = rig.wait(lambda: rig.fb.get('state') == 'Squeeze', 40)
        at_cancel = dict(rig.fb)
        if not hit:
            status, res = rig.result(gh)
            # 단계에 못 갔을 때도 파지 결과를 남긴다(빈 닫기 NoContact 등) / record the grasp result anyway
            raw.append({'trial': k, 'phase': phase, 'start': start, 'at_timeout': at_cancel, 'status': status,
                        'reason': res.reason if res else None, 'contact': res.contact_position if res else None,
                        'final_reported': res.final_position if res else None})
            check(rows, f'{phase}#{k} reached the phase', False,
                  f'last feedback {at_cancel}; grasp ended {status}, reason {res.reason if res else None}')
            if status == 'succeeded':
                rig.release()
            rig.wait(lambda: rig.state['name'] == 'Idle', 15)
            continue
        cf = gh.cancel_goal_async()
        rig.wait(cf.done, 5)
        status, res = rig.result(gh, 15)
        rig.spin(2.5)                         # 풀림 동작(1.5 s)이 끝나도록 / let the slow opening finish
        end = rig.gripper()
        idle = rig.wait(lambda: rig.state['name'] == 'Idle', 10)
        row = {'trial': k, 'phase': phase, 'start': start, 'at_cancel': at_cancel, 'status': status,
               'reason': res.reason if res else None, 'contact': res.contact_position if res else None,
               'final_reported': res.final_position if res else None, 'end_reading': end, 'idle': idle}
        raw.append(row)
        check(rows, f'{phase}#{k} result Cancelled', status == 'canceled' and res and res.reason == 'Cancelled',
              f'status {status}, reason {res.reason if res else None}')
        if phase == 'cancel-closing':
            ok = start is not None and end is not None and abs(end - start) <= 15
            check(rows, f'{phase}#{k} gripper back at start (±15 pulses)', ok,
                  f'start {start and round(start, 1)}, end {end and round(end, 1)} (reading units)')
        else:
            contact = res.contact_position if res else -1
            ok = res is not None and contact > 0 and start is not None and end is not None and abs(end - start) > 100
            check(rows, f'{phase}#{k} relaxed to the contact, not opened (end > 100 pulses from start)', ok,
                  f'contact {contact}, final reported {res.final_position if res else None}, '
                  f'start reading {start and round(start, 1)}, end reading {end and round(end, 1)}')
        check(rows, f'{phase}#{k} back to Idle', idle, f'state {rig.state["name"]}')
        print('  (take the cube out)', flush=True)


def run_refuse(rig, args, rows, raw):
    if rig.gripper() is not None and rig.gripper() < 250:
        print(f'  opening the gripper first (reading {rig.gripper():.0f})', flush=True)
        rig.open_gripper()
    print(f'control: one small gripper command while Idle must move the gripper (in {args.first_delay:g} s)',
          flush=True)
    rig.spin(args.first_delay)
    g0 = rig.gripper()
    rig.gripper_cmd(rig.js['r_joint'] + 20 * RPT)   # r_joint는 클수록 열림: 20 펄스 더 열기 / larger = more open
    rig.spin(2.5)
    g1 = rig.gripper()
    check(rows, 'control: gripper command accepted while Idle', abs(g1 - g0) >= 8,
          f'reading {g0:.1f} -> {g1:.1f}')
    print(f'now put the cube between the open jaws; closing starts in {args.gap:g} s', flush=True)
    rig.spin(args.gap)
    gh = rig.send_goal()
    if gh is None or not gh.accepted:
        check(rows, 'grasp accepted', False, 'refused')
        return
    status, res = rig.result(gh)
    if not check(rows, 'grasp succeeded (Holding)', status == 'succeeded' and res and res.success,
                 f'status {status}, reason {res.reason if res else None}'):
        rig.wait(lambda: rig.state['name'] == 'Idle', 15)
        return
    rig.spin(1.0)
    h0, lo, hi = rig.gripper(), None, None
    base = rig.js['r_joint']
    for i in range(args.commands):
        # 번갈아 열기/닫기 쪽 30 펄스 / alternate 30 pulses either way
        rig.gripper_cmd(base + (30 if i % 2 == 0 else -30) * RPT)
        t0 = time.monotonic()
        while time.monotonic() - t0 < 0.5:
            rclpy.spin_once(rig.n, timeout_sec=0.02)
            v = rig.gripper()
            if v is not None:
                lo, hi = (v, v) if lo is None else (min(lo, v), max(hi, v))
    rig.spin(1.5)
    h1 = rig.gripper()
    spread = hi - lo if lo is not None else None
    raw.append({'holding_start': h0, 'holding_end': h1, 'min': lo, 'max': hi, 'commands': args.commands,
                'state_after': rig.state['name']})
    check(rows, f'{args.commands} gripper commands while Holding did not move it (spread <= 4 pulses)',
          spread is not None and spread <= 4, f'reading {h0:.1f} -> {h1:.1f}, spread {spread:.1f}')
    check(rows, 'still Holding after the commands', rig.state['name'] == 'Holding', f'state {rig.state["name"]}')
    ok = rig.release()
    idle = rig.wait(lambda: rig.state['name'] == 'Idle', 15)
    check(rows, 'release -> Idle', ok and idle, f'release {ok}, state {rig.state["name"]}')
    print('  (take the cube out)', flush=True)


def run_fault(rig, args, kind, rows, raw):
    want = {'timeout': 'Timeout', 'temp-refuse': 'TempHigh'}[kind]
    for k in range(1, args.trials + 1):
        wait_s = args.first_delay if k == 1 else args.gap
        print(f'trial {k}/{args.trials} ({kind}): cube between the jaws (or empty); starts in {wait_s:g} s', flush=True)
        rig.spin(wait_s)
        start = rig.gripper()
        gh = rig.send_goal()
        if gh is None or not gh.accepted:
            check(rows, f'{kind}#{k} goal accepted', False, 'refused')
            continue
        status, res = rig.result(gh, 60)
        rig.spin(2.5)
        end = rig.gripper()
        idle = rig.wait(lambda: rig.state['name'] == 'Idle', 10)
        raw.append({'trial': k, 'kind': kind, 'start': start, 'end': end, 'status': status,
                    'reason': res.reason if res else None, 'temp_seen': rig.fb.get('temp'), 'idle': idle})
        check(rows, f'{kind}#{k} result {want}', res is not None and res.reason == want,
              f'status {status}, reason {res.reason if res else None}, temp {rig.fb.get("temp")}')
        ok = start is not None and end is not None and abs(end - start) <= 15
        check(rows, f'{kind}#{k} gripper at its start position (±15 pulses)', ok,
              f'start {start and round(start, 1)}, end {end and round(end, 1)}')
        check(rows, f'{kind}#{k} back to Idle', idle, f'state {rig.state["name"]}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('scenario',
                    choices=('cancel-closing', 'cancel-squeeze', 'refuse-holding', 'timeout', 'temp-refuse'))
    ap.add_argument('--trials', type=int, default=3)
    ap.add_argument('--first-delay', type=float, default=20.0)
    ap.add_argument('--gap', type=float, default=15.0)
    ap.add_argument('--commands', type=int, default=20)
    args = ap.parse_args()

    rig = Rig()
    if not rig.act.wait_for_server(timeout_sec=10) or not rig.rel.wait_for_service(timeout_sec=10):
        sys.exit('arm/grasp or arm/release not available: base_node must run with arm_command_enabled:=true')
    rig.spin(2.0)
    if rig.state['name'] != 'Idle' or rig.gripper() is None:
        sys.exit(f'grasp state {rig.state["name"]}, gripper reading {rig.gripper()}: expected Idle and a reading')
    rows, raw = [], []
    if args.scenario in ('cancel-closing', 'cancel-squeeze'):
        run_cancel(rig, args, args.scenario, rows, raw)
    elif args.scenario == 'refuse-holding':
        run_refuse(rig, args, rows, raw)
    else:
        run_fault(rig, args, args.scenario, rows, raw)
    os.makedirs('Log', exist_ok=True)
    path = 'Log/grasp_l2_faults_%s_%s.json' % (args.scenario, time.strftime('%Y%m%d_%H%M%S'))
    json.dump({'checks': rows, 'raw': raw}, open(path, 'w'), indent=1, default=str)
    n_fail = sum(1 for r in rows if not r['pass'])
    print(f'SUMMARY {args.scenario}: {len(rows) - n_fail}/{len(rows)} checks passed; raw: {path}')
    rclpy.shutdown()
    sys.exit(1 if n_fail else 0)


if __name__ == '__main__':
    main()
