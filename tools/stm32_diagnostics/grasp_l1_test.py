#!/usr/bin/env python3
# 한글: T6 L1 시험 — 로봇 없이 가짜 RRC 장치(pty)로 base_node의 접촉 파지 연결을 끝까지 확인한다(arm/grasp Action, arm/release 서비스,
#       ID 10 배타 제어, 상태별 팔 이동 허용, 공중 이상 시 열지 않기). 하드웨어 증거가 아니다 — 실기는 L2.
"""L1 test of the contact-grasp wiring in base_node against a fake RRC device on a pty (no hardware).

Usage: python3 tools/stm32_diagnostics/grasp_l1_test.py     (needs the workspace built and sourced)
The fake device answers FUNC5 position/temperature reads and moves its servos on FUNC5 move commands; the gripper
(ID 10) follows a command after its time unless it meets `block`. It can drop replies and raise the temperature.
Prints one PASS/FAIL line per acceptance check and exits 1 if any failed.
"""
import os
import pty
import struct
import subprocess
import sys
import threading
import time
import tty

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rrc_m4_diag import frames  # noqa: E402
from rrc_m4_raw_pwm_test import frame  # noqa: E402

RPT = 240.0 / 1000.0 * 3.141592653589793 / 180.0   # rad per pulse


class FakeRrc(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.master, slave = pty.openpty()
        tty.setraw(self.master)
        self.path = os.ttyname(slave)
        self.pos = {1: 500, 2: 650, 3: 100, 4: 150, 5: 500, 10: 200}
        self.target = dict(self.pos)
        self.done_at = {i: 0.0 for i in self.pos}
        # 점진 이동(2026-10-15): 명령 시간 동안 일정 속도로 움직이고 block에서 멈춘다(빠른 접근의 멈춤 감시를 실제처럼).
        # Gradual motion: constant speed over the command time, stopping at `block` (realistic for the approach watch).
        self.move = {i: (self.pos[i], 0.0, 0.0, self.pos[i]) for i in self.pos}   # (from, t0, duration, commanded)
        self.block = 523            # gripper stops here when closing (None = nothing in the jaws)
        self.temp = 40
        self.silent = False         # no replies at all
        self.gripper_cmds = []      # (time, pulse) of every move command that touched ID 10
        self.moves = {i: [] for i in self.pos}   # (time, pulse) of every move command per servo
        self.torque_cmds = []
        self.stop = False
        self.t0 = time.monotonic()

    def reading(self, sid):
        now = time.monotonic()
        if now >= self.done_at[sid]:
            self.pos[sid] = self.target[sid]
        else:
            src, t0, dur, cmd = self.move[sid]
            p = src + (cmd - src) * min(1.0, (now - t0) / max(dur, 1e-3))
            stop = self.target[sid]
            self.pos[sid] = int(min(p, stop) if cmd >= src else max(p, stop))
        return self.pos[sid]

    def handle(self, f, d):
        if f != 0x05 or len(d) < 2:
            return
        sub = d[0]
        if sub == 0x05 and not self.silent:                       # read position [05, id]
            sid = d[1]
            if sid in self.pos:
                v = self.reading(sid)
                os.write(self.master, frame(0x05, bytes([sid, 0x05, 0]) + struct.pack('<h', v)))
        elif sub == 0x09 and not self.silent:                     # read temperature [09, id]
            sid = d[1]
            if sid in self.pos:
                os.write(self.master, frame(0x05, bytes([sid, 0x09, 0, self.temp])))
        elif sub == 0x01 and len(d) >= 4:                         # move [01, ms lo, ms hi, n, (id, p lo, p hi)*n]
            ms = struct.unpack('<H', d[1:3])[0]
            n = d[3]
            for k in range(n):
                sid, pulse = d[4 + 3 * k], struct.unpack('<H', d[5 + 3 * k:7 + 3 * k])[0]
                if sid not in self.pos:
                    continue
                cur = self.reading(sid)
                stop = pulse
                self.moves[sid].append((time.monotonic() - self.t0, pulse))
                if sid == 10:
                    stop = min(pulse, 693, self.block if self.block is not None else 693)
                    self.gripper_cmds.append((time.monotonic() - self.t0, pulse))
                if abs(stop - cur) > 3:
                    self.target[sid] = stop
                    self.done_at[sid] = time.monotonic() + ms / 1000.0
                    self.move[sid] = (cur, time.monotonic(), ms / 1000.0, pulse)
        elif sub in (0x0B, 0x0C):
            self.torque_cmds.append((time.monotonic() - self.t0, sub, d[1]))

    def run(self):
        import select
        buf = b''
        while not self.stop:
            if select.select([self.master], [], [], 0.02)[0]:
                try:
                    buf += os.read(self.master, 4096)
                except OSError:
                    return
                for f, d in frames(buf):
                    self.handle(f, bytes(d))
                last = buf.rfind(b'\xaa\x55')
                buf = buf[last:] if last >= 0 else b''
                if len(buf) > 4096:
                    buf = b''


def main():
    import rclpy
    from rclpy.action import ActionClient
    from sensor_msgs.msg import JointState
    from std_msgs.msg import Bool, String
    from jetrover_interfaces.action import Grasp
    from jetrover_interfaces.srv import Release

    fake = FakeRrc()
    fake.start()
    node_proc = subprocess.Popen(
        [os.path.expanduser('~/jetrover_ws/install/jetrover_base/lib/jetrover_base/base_node'), '--ros-args',
         '-p', f'port:={fake.path}', '-p', 'arm_command_enabled:=true', '-p', 'arm_move_home_on_start:=false',
         '-p', 'cmd_vel_timeout:=1000.0', '-p', 'stm32_timeout:=1000.0']
        # GRASP_L1_EXTRA="grasp_approach_margin:=40 ..." 로 파라미터 추가 / extra base_node parameters
        + sum((['-p', e] for e in os.environ.get('GRASP_L1_EXTRA', '').split()), []),
        stdout=subprocess.DEVNULL, stderr=open(os.environ.get('GRASP_L1_LOG', os.devnull), 'w'))

    rclpy.init()
    n = rclpy.create_node('grasp_l1')
    state = {'name': None, 'seen': []}

    def on_state(m):
        state['name'] = m.data
        if not state['seen'] or state['seen'][-1] != m.data:
            state['seen'].append(m.data)
    n.create_subscription(String, 'arm/grasp_state', on_state, 10)
    js = {}
    n.create_subscription(JointState, 'joint_states', lambda m: js.update(dict(zip(m.name, m.position))), 10)
    lifted_pub = n.create_publisher(Bool, 'arm/object_lifted', 10)
    cmd_pub = n.create_publisher(JointState, 'arm/command', 10)
    act = ActionClient(n, Grasp, 'arm/grasp')
    rel = n.create_client(Release, 'arm/release')
    results = []

    def spin(sec):
        t0 = time.monotonic()
        while time.monotonic() - t0 < sec:
            rclpy.spin_once(n, timeout_sec=0.02)

    def wait(pred, limit):
        t0 = time.monotonic()
        while time.monotonic() - t0 < limit:
            rclpy.spin_once(n, timeout_sec=0.02)
            if pred():
                return True
        return False

    def check(name, ok, detail=''):
        results.append(ok)
        print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''), flush=True)

    def send_goal(profile='cube3cm'):
        g = Grasp.Goal()
        g.profile = profile
        fut = act.send_goal_async(g)
        t0 = time.monotonic()
        while not fut.done() and time.monotonic() - t0 < 5:
            rclpy.spin_once(n, timeout_sec=0.02)
        return fut.result()

    def result_of(gh, limit=60):
        fut = gh.get_result_async()
        t0 = time.monotonic()
        while not fut.done() and time.monotonic() - t0 < limit:
            rclpy.spin_once(n, timeout_sec=0.02)
        return fut.result().result if fut.done() else None

    def joint_cmd(name, delta_rad):
        # relative to the CURRENT joint angle (so the step limit arm_max_step_rad 0.35 is never what refuses it)
        m = JointState()
        m.name = [name]
        m.position = [js[name] + delta_rad]
        cmd_pub.publish(m)

    def gripper_cmd(delta_rad=0.08):
        joint_cmd('r_joint', delta_rad)

    def arm_cmd(delta_rad=0.05):
        joint_cmd('joint1', delta_rad)

    try:
        if not act.wait_for_server(timeout_sec=15):
            print('FAIL arm/grasp action server not available (is arm_command_enabled honoured?)')
            return 1
        spin(2.5)    # let the polling fill arm_servo_ticks_
        check('idle at start', state['name'] == 'Idle', str(state['name']))

        # ---- positive control: in Idle the very same small gripper command DOES reach the servo
        spin(1.0)
        before = len(fake.gripper_cmds)
        gripper_cmd(0.08)
        spin(1.0)
        check('control: a small gripper command reaches the servo in Idle', len(fake.gripper_cmds) > before)
        # 이동(2 s)이 끝난 뒤 되돌린다 — 점진 모델에서 중간 위치 기준으로 되돌리면 시작 위치가 6펄스 어긋났다
        # undo only after the 2 s move ends: with gradual motion an undo from mid-move shifted the start by 6 pulses
        spin(1.5)
        gripper_cmd(-0.08)
        spin(2.5)

        # ---- unknown profile is refused
        gh = send_goal('banana')
        check('unknown profile refused', gh is not None and not gh.accepted)

        # ---- normal grasp -> succeeded, Holding keeps the gripper
        fake.block = 523
        gh = send_goal()
        check('goal accepted', gh is not None and gh.accepted)
        res = result_of(gh, 60)
        check('grasp succeeded', res is not None and res.success, f'result {res}')
        check('contact near the block', res is not None and abs(res.contact_position - 523) <= 4,
              str(res.contact_position if res else None))
        spin(0.5)
        check('state is Holding after the action ended', state['name'] == 'Holding', str(state['name']))

        # ---- while holding: ID 10 refused, arm joint allowed
        before = len(fake.gripper_cmds)
        for _ in range(20):
            gripper_cmd(0.08)
            spin(0.05)
        spin(0.5)
        check('20 small gripper commands while Holding -> 0 reach the servo (guard, not the step limit)',
              len(fake.gripper_cmds) == before, f'{len(fake.gripper_cmds) - before} got through')
        m1 = len(fake.moves[1])
        arm_cmd(0.05)
        spin(1.0)
        check('arm joint 1 command reaches the servo while Holding', len(fake.moves[1]) > m1)
        spin(2.5)         # the move takes 2 s

        # ---- fault in the air: temperature -> no opening, needs the user; a second grasp is refused meanwhile
        lifted_pub.publish(Bool(data=True))
        spin(0.3)
        n_cmds = len(fake.gripper_cmds)
        fake.temp = 85
        spin(5.0)
        check('heat while lifted: Holding stays and NO command reaches the gripper',
              state['name'] == 'Holding' and len(fake.gripper_cmds) == n_cmds,
              f'state {state["name"]}, extra cmds {len(fake.gripper_cmds) - n_cmds}')
        gh2 = send_goal()
        check('second grasp refused while holding', gh2 is not None and not gh2.accepted)

        # ---- explicit release returns the gripper
        fake.temp = 40
        r = rel.call_async(Release.Request())
        t0 = time.monotonic()
        while not r.done() and time.monotonic() - t0 < 5:
            rclpy.spin_once(n, timeout_sec=0.02)
        check('release accepted', r.done() and r.result().success, str(r.result() if r.done() else None))
        ok = wait(lambda: state['name'] == 'Idle', 10)
        check('back to Idle after release', ok, str(state['name']))
        check('gripper reopened to the start', abs(fake.reading(10) - 200) <= 4, str(fake.reading(10)))
        r2 = rel.call_async(Release.Request())
        t0 = time.monotonic()
        while not r2.done() and time.monotonic() - t0 < 5:
            rclpy.spin_once(n, timeout_sec=0.02)
        check('release refused when not holding', r2.done() and not r2.result().success)
        spin(1.0)
        before = len(fake.gripper_cmds)
        gripper_cmd(0.08)
        spin(1.0)
        check('gripper command works again in Idle', len(fake.gripper_cmds) > before)
        gripper_cmd(-0.08)
        spin(1.5)

        # ---- empty close -> aborted NoContact, then free again
        lifted_pub.publish(Bool(data=False))
        fake.block = None
        gh = send_goal()
        res = result_of(gh, 90)
        check('empty close aborts with NoContact', res is not None and not res.success and res.reason == 'NoContact',
              str(res.reason if res else None))
        ok = wait(lambda: state['name'] == 'Idle', 10)
        check('Idle again after the failure was reported', ok, str(state['name']))

        # ---- cancel while closing -> canceled, gripper opened again
        fake.block = 523
        gh = send_goal()
        spin(3.0)
        cf = gh.cancel_goal_async()
        t0 = time.monotonic()
        while not cf.done() and time.monotonic() - t0 < 5:
            rclpy.spin_once(n, timeout_sec=0.02)
        res = result_of(gh, 15)
        check('cancel while closing ends the goal', res is not None and not res.success and res.reason == 'Cancelled',
              str(res.reason if res else None))
        ok = wait(lambda: state['name'] == 'Idle', 10)
        check('Idle after the cancel', ok, str(state['name']))

        # ---- arm motion denied while closing
        gh = send_goal()
        spin(2.0)
        m1 = len(fake.moves[1])
        arm_cmd(0.08)
        spin(1.0)
        check('arm joint command refused while Closing', len(fake.moves[1]) == m1,
              f'{len(fake.moves[1]) - m1} got through')
        gh.cancel_goal_async()
        result_of(gh, 15)
        wait(lambda: state['name'] == 'Idle', 10)

        # ---- hot gripper refuses to start
        fake.temp = 82
        spin(1.5)
        n_cmds = len(fake.gripper_cmds)
        gh = send_goal()
        res = result_of(gh, 15) if gh is not None and gh.accepted else None
        extra = [c for c in fake.gripper_cmds[n_cmds:]]
        check('hot gripper: aborted with TempHigh and no gripper command',
              res is not None and res.reason == 'TempHigh' and not extra,
              f'{res.reason if res else None}, commands after the goal: {extra}')
        fake.temp = 40
        wait(lambda: state['name'] == 'Idle', 10)
    finally:
        fake.stop = True
        node_proc.terminate()
        try:
            node_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            node_proc.kill()
        rclpy.shutdown()
    print(f'{sum(results)}/{len(results)} checks passed')
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(main())
