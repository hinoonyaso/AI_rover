#!/usr/bin/env python3
# 한글: 게임패드로 팔 손끝을 조금씩 움직이는 조그 도구(교시용). 사람이 보면서 큐브를 잘 잡는 자세를 맞추고
#       그 자세와 카메라 검출값을 함께 기록한다 → 검출 위치와 실제 잡히는 위치의 차이로 보정.
#       팔이 움직인다. base_node(arm_command_enabled)와 joy_node가 떠 있어야 한다. --dry-run이면 명령을 보내지 않는다.
"""Gamepad jog for the arm fingertip (teaching). THE ARM MOVES unless --dry-run.

Needs base_node (arm_command_enabled) and `ros2 run joy joy_node --ros-args -p autorepeat_rate:=20.0`
(continuous messages: the tool stops when the newest is older than 0.3 s). Commands go straight to
base_node `arm/command_timed` every 0.1 s as 0.2 s moves, so the servos never stop between steps
(base_node still applies its step limit and pulse clamp).
Hold L1 (deadman) to move; release = stop. Controls (SHANWAN Android gamepad, see --help-map):
  left stick: fingertip forward/back, left/right   right stick up/down: fingertip up/down
  right stick left/right: wrist (joint5)           R1 held: fine mode (30 % speed)
  A / B held: close / open gripper                 X: snapshot the camera detection (at look_floor)
  Y: record the pose (+ last snapshot)             START / SELECT: go to look_floor / rest_upright
  left stick click (L3): flip forward/left for standing in front of the robot
  right stick click (R3): JOINT mode <-> TIP mode. Joint mode: left stick left/right joint1,
    up/down joint2; right stick up/down joint3, left/right joint4; d-pad left/right joint5
Records: one JSON line per Y press in --out (default Log/jog_records.jsonl).
"""
import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'sim'))
from arm_ik import fk, load_chain  # noqa: E402

ARM = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5']
# 버튼·축 번호(2026-10-18 실측, joy_node + SHANWAN Android Gamepad). 방향 부호는 --dry-run으로 확인.
# Button/axis numbers measured on 2026-10-18 (joy_node). Signs checked with --dry-run.
MAP = {'deadman': 6, 'fine': 7, 'close': 0, 'open': 1, 'snapshot': 3, 'record': 4,
       'look': 11, 'rest': 10, 'flip': 13, 'mode': 14, 'ax_x': 1, 'ax_y': 0, 'ax_z': 3, 'ax_wrist': 2,
       'ax_dpad_x': 6}
JOINT_RATE = 0.3        # rad/s at full stick in joint mode
LOOK_FLOOR = [0.0, -0.35, 1.60, 1.60, 0.0]
REST = [0.0, 0.0, 0.0, 0.0, 0.0]
# 0.1 s마다 0.2 s짜리 목표: 서보가 도착해 멈추기 전에 다음 목표가 와서 끊기지 않는다. 처음엔 0.2 s마다
# 0.2 s 목표라 '뚝뚝 끊김'·'반응 늦음'이었다(사용자, 2026-10-18).
# Every 0.1 s a 0.2 s move: the next target arrives before the servo stops (0.2/0.2 felt jerky and slow).
PERIOD = 0.1
CMD_DUR = 0.2
LAG_WAIT, LAG_BLOCK = 0.2, 0.35   # rad: stop advancing / treat as blocked after 1 s
TOOL_M = 0.036          # fingertip past end_effector_link (pick_detected.py)
GRIP_OPEN, GRIP_CLOSED = 1.257, -0.75
GOAL_RATE = 0.3         # rad/s for named poses (0.5 lagged the servos by 0.2 rad)
CART_SPEED = 0.03       # m/s fingertip speed while retracting before a named pose


def urdf_path():
    from ament_index_python.packages import get_package_share_directory
    xacro = os.path.join(get_package_share_directory('jetrover_description'), 'urdf', 'jetrover.xacro')
    out = tempfile.NamedTemporaryFile(suffix='.urdf', delete=False).name
    with open(out, 'w') as f:
        f.write(subprocess.run(['xacro', xacro], capture_output=True, text=True, check=True).stdout)
    return out


def tip(chain, q):
    """Fingertip xyz (model frame) and gripper tilt from vertical (deg). 한글: 손끝 위치와 기울기."""
    t = fk(chain, np.asarray(q))
    return t[:3, 3] + TOOL_M * t[:3, 2], math.degrees(math.acos(max(-1.0, min(1.0, -t[2, 2]))))


def toward_down(axis, max_deg=2.0):
    """Tool axis turned toward straight down by at most max_deg. 한글: 도구 축을 수직 쪽으로 조금만 돌린다."""
    down = np.array([0.0, 0.0, -1.0])
    ang = math.acos(max(-1.0, min(1.0, float(axis @ down))))
    if ang < 1e-6:
        return down
    f = min(1.0, math.radians(max_deg) / ang)
    v = (1 - f) * axis + f * down          # 작은 각도에서는 선형 보간으로 충분 / fine for small steps
    return v / np.linalg.norm(v)


def _residual(chain, q, target, axis, w):
    t = fk(chain, q)
    p = t[:3, 3] + TOOL_M * t[:3, 2]
    return np.concatenate([target - p, w * (axis - t[:3, 2])])


def local_ik(chain, q, target, iters=6):
    """Joints 1-4 from q (joint5 kept): fingertip on target, tool axis close to its current direction
    turned <= 2 deg toward straight down. Damped least squares, a few ms. -> (q, err m).
    한글: 처음 버전은 매 스텝 수직을 강하게 요구해서 홈 자세(39° 기울어짐)에서 첫 스텝부터 관절이
    0.15 rad 넘게 바뀌어 전부 거부됐다(2026-10-18 dry-run). 지금 방향을 유지하며 조금씩 세운다.
    최적화(L-BFGS, 22~80 ms) 대신 감쇠 최소제곱으로 바꿔 반응을 빠르게 했다."""
    q0 = np.asarray(q, float)
    axis = toward_down(fk(chain, q0)[:3, 2])
    # 방향 가중치: 0.02(1 cm ≈ 29° 도구 축). 관절 한계 근처에서 위치와 방향이 충돌하면 0.002로 한 번 더
    # orientation weight 0.02; if position and orientation conflict near a limit, retry with 0.002
    for w in (0.02, 0.002):
        q = q0.copy()
        for _ in range(iters):
            e = _residual(chain, q, target, axis, w)
            if np.linalg.norm(e[:3]) < 2e-4:
                break
            jac = np.zeros((6, 4))
            for i in range(4):
                dq = np.zeros(5)
                dq[i] = 1e-4
                jac[:, i] = (e - _residual(chain, q + dq, target, axis, w)) / 1e-4   # d(model)/dq
            step = jac.T @ np.linalg.solve(jac @ jac.T + 1e-4 * np.eye(6), e)
            q[:4] = np.clip(q[:4] + step, -1.65, 1.65)
        err = float(np.linalg.norm(tip(chain, q)[0] - target))
        if err < 0.002:
            break
    return q, err


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--dry-run', action='store_true', help='decode and print only, never command the arm')
    ap.add_argument('--speed', type=float, default=0.03, help='fingertip speed at full stick (m/s)')
    ap.add_argument('--floor-z', type=float, default=-0.034, help='model z of the real floor (m)')
    ap.add_argument('--colour', default='red')
    ap.add_argument('--out', default=os.path.join(HERE, '..', '..', 'Log', 'jog_records.jsonl'))
    args = ap.parse_args()

    import rclpy
    from geometry_msgs.msg import PointStamped
    from rclpy.node import Node
    from sensor_msgs.msg import Joy, JointState
    from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

    chain = load_chain(urdf_path())
    # 작업 영역(모델 좌표, 손끝). 바닥 3 mm 위까지만 / workspace for the fingertip, >= 3 mm above the floor
    lo = np.array([0.08, -0.25, args.floor_z + 0.003])
    hi = np.array([0.38, 0.25, 0.30])
    LOOK_TIP = tip(chain, LOOK_FLOOR)[0]      # 이름 자세로 가기 전 물러나는 지점 / retract point before named poses

    class Jog(Node):
        def __init__(self):
            super().__init__('gamepad_jog')
            self.joy, self.joy_t, self.prev_buttons = None, 0.0, []
            self.js, self.js_t = {}, 0.0
            self.q_cmd, self.grip_cmd, self.p_tgt = None, None, None
            self.pts, self.snapshot, self.n_rec = [], None, 0
            self.goal = None          # named-pose target (list of 5) while moving there
            self.goal_phase = 'joint'
            self.block_since = None
            self.flip = False         # True: 로봇 정면에서 볼 때의 앞/왼쪽 / forward-left as seen facing the robot
            self.joint_mode = False   # R3: 관절 따로 제어 / per-joint control
            self.last_print = 0.0
            self.create_subscription(Joy, 'joy', self.on_joy, 10)
            self.create_subscription(JointState, 'joint_states', self.on_js, 10)
            self.create_subscription(PointStamped, f'cubes/{args.colour}',
                                     lambda m: self.pts.append(
                                         (time.monotonic(), m.point.x, m.point.y, m.point.z)), 10)
            self.pub = self.create_publisher(JointTrajectory, 'arm/command_timed', 1)
            self.create_timer(PERIOD, self.tick)
            self.get_logger().info(('DRY RUN: ' if args.dry_run else '') + 'hold L1 to move')

        def on_js(self, m):
            self.js.update(dict(zip(m.name, m.position)))
            self.js_t = time.monotonic()

        def on_joy(self, m):
            pressed = [i for i, b in enumerate(m.buttons)
                       if b and (i >= len(self.prev_buttons) or not self.prev_buttons[i])]
            self.prev_buttons = list(m.buttons)
            self.joy, self.joy_t = m, time.monotonic()
            for b in pressed:
                if b == MAP['snapshot']:
                    self.take_snapshot()
                elif b == MAP['record']:
                    self.record()
                elif b == MAP['mode']:
                    self.joint_mode = not self.joint_mode
                    self.say('mode: ' + ('JOINT (L: j1/j2, R: j3/j4, d-pad: j5)' if self.joint_mode
                                         else 'TIP (L: forward/side, R: up/wrist)'))
                elif b == MAP['flip']:
                    self.flip = not self.flip
                    self.say('directions: ' + ('FACING the robot (stick up = toward you)' if self.flip
                                               else 'BEHIND the robot (stick up = away from you)'))
                elif b in (MAP['look'], MAP['rest']):
                    self.goal = LOOK_FLOOR if b == MAP['look'] else REST
                    q = self.measured()
                    p = tip(chain, q)[0] if q is not None else LOOK_TIP
                    # 손끝이 look_floor 손끝보다 낮거나 앞이면 먼저 직선으로 물러난다 / retract first
                    low_or_ahead = p[2] < LOOK_TIP[2] - 0.01 or p[0] > LOOK_TIP[0] + 0.03
                    self.goal_phase = 'cart' if low_or_ahead else 'joint'
                    self.say(f'going to {"look_floor" if b == MAP["look"] else "rest_upright"} '
                             f'(hold L1)')

        def say(self, text):
            print(text, flush=True)

        def measured(self):
            if time.monotonic() - self.js_t > 0.5 or not all(j in self.js for j in ARM + ['r_joint']):
                return None
            return np.array([self.js[j] for j in ARM])

        def take_snapshot(self):
            now = time.monotonic()
            recent = [p[1:] for p in self.pts if now - p[0] < 1.5]
            q = self.measured()
            if len(recent) < 3 or q is None:
                self.say(f'snapshot: only {len(recent)} detections of {args.colour} in 1.5 s - not saved')
                return
            med = np.median(np.array(recent), axis=0)
            self.snapshot = {'cube': med.round(4).tolist(), 'n': len(recent), 'joints': q.round(4).tolist()}
            self.say(f'snapshot: {args.colour} cube at ({med[0]:.3f}, {med[1]:.3f}) top z {med[2]:.3f} '
                     f'({len(recent)} detections)')

        def record(self):
            q = self.measured()
            if q is None:
                self.say('record: no fresh joint_states - not saved')
                return
            p, tilt = tip(chain, q)
            self.n_rec += 1
            row = {'t': time.time(), 'n': self.n_rec, 'joints': q.round(4).tolist(),
                   'r_joint': round(self.js['r_joint'], 4), 'tip_model': p.round(4).tolist(),
                   'tip_above_floor': round(float(p[2] - args.floor_z), 4), 'tilt_deg': round(tilt, 1),
                   'snapshot': self.snapshot}
            os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
            with open(args.out, 'a') as f:
                f.write(json.dumps(row) + '\n')
            cube = self.snapshot['cube'] if self.snapshot else None
            self.say(f'RECORD #{self.n_rec}: tip ({p[0]:.3f}, {p[1]:.3f}), {100 * (p[2] - args.floor_z):.1f} cm '
                     f'above floor, tilt {tilt:.0f} deg | camera cube {cube} -> {args.out}')

        def goal_step(self, q_new):
            """One step toward a named pose. Low or forward: first lift the fingertip straight up to the
            look_floor tip height, then move it level to the look_floor tip, then blend the joints.
            한글: 앞쪽 낮은 자세에서 관절을 바로 보간했더니 팔이 몸체를 쓸고 지나가 부딪혔다(2026-10-18).
            손끝을 먼저 수직으로 올리고, 수평으로 look_floor 손끝까지 옮긴 뒤에만 관절 보간한다."""
            p = self.p_tgt
            if self.goal_phase == 'cart':
                v = np.zeros(3)
                if p[2] < LOOK_TIP[2] - 0.005:
                    v[2] = min(CART_SPEED * PERIOD, LOOK_TIP[2] - p[2])
                else:
                    dxy = LOOK_TIP[:2] - p[:2]
                    dist = float(np.linalg.norm(dxy))
                    if dist < 0.005:
                        self.goal_phase = 'joint'
                    else:
                        v[:2] = dxy / dist * min(CART_SPEED * PERIOD, dist)
                if np.any(v):
                    target = p + v
                    q_try, err = local_ik(chain, self.q_cmd, target)
                    if err > 0.003 or np.max(np.abs(q_try - self.q_cmd)) > 0.15:
                        self.say(f'cannot retract along a straight line (IK err {1000 * err:.1f} mm) - '
                                 'stopped; jog up/back by hand')
                        self.goal = None
                        return q_new
                    self.p_tgt = target
                    return q_try
            d = np.array(self.goal) - self.q_cmd
            q_new = self.q_cmd + np.clip(d, -GOAL_RATE * PERIOD, GOAL_RATE * PERIOD)
            if np.max(np.abs(d)) < 0.01:
                self.say('arrived')
                self.goal = None
            self.p_tgt = tip(chain, q_new)[0]
            return q_new

        def send(self, names, values):
            """Command only the given joints. 한글: 바뀐 관절만 보낸다 — 그리퍼만 움직일 때 팔 5개도 함께
            (L1 누를 때 읽은 값으로) 보내서, 처짐만큼 팔이 움직였다(사용자, 2026-10-18)."""
            if args.dry_run:
                return
            msg = JointTrajectory()
            msg.joint_names = list(names)
            pt = JointTrajectoryPoint()
            pt.positions = [float(v) for v in values]
            pt.time_from_start.nanosec = int(CMD_DUR * 1e9)
            msg.points = [pt]
            self.pub.publish(msg)

        def tick(self):
            m, q_meas = self.joy, self.measured()
            if m is None:
                return
            # 게임패드 메시지가 끊기면(절전·연결 끊김) 마지막 'L1 눌림'이 남아 계속 움직일 수 있다 →
            # joy_node를 autorepeat_rate 20으로 띄우고 0.3 s 넘게 안 오면 멈춘다(2026-10-18 패드 절전에서 발견).
            # A silent pad (sleep, link lost) would leave the last 'L1 held' message: needs joy_node
            # autorepeat_rate 20 and stops when the newest message is older than 0.3 s.
            if time.monotonic() - self.joy_t > 0.3:
                if self.q_cmd is not None:
                    self.say('gamepad silent > 0.3 s - stopped (run joy_node with autorepeat_rate:=20.0)')
                self.q_cmd, self.grip_cmd, self.p_tgt = None, None, None
                return
            held = len(m.buttons) > MAP['deadman'] and m.buttons[MAP['deadman']]
            if q_meas is None:
                if held:
                    self.say('joint_states stale - not moving')
                self.q_cmd = None
                return
            if not held:
                self.q_cmd, self.grip_cmd, self.p_tgt = None, None, None   # 놓으면 실제 자세에서 다시 시작
                return
            if self.q_cmd is None:
                self.q_cmd, self.grip_cmd = q_meas.copy(), self.js['r_joint']
                self.p_tgt = tip(chain, q_meas)[0]
            # 읽기는 관절당 약 0.3 s마다 갱신되고 서보도 늦게 따라와서, 움직이는 중엔 늘 명령보다 뒤처진다.
            # 처음엔 0.15 rad 넘으면 실제 자세로 되돌려 '원래대로 돌아가고 잘 안 움직임'(사용자, 2026-10-18) →
            # 0.2 rad 넘으면 목표를 더 보내지 않고 기다리고, 0.35 rad가 1 s 넘게 이어질 때만 막힌 것으로 보고 맞춘다.
            # Readings refresh every ~0.3 s per joint and the servos trail, so the reading always lags while
            # moving. Resyncing at 0.15 rad made the arm jump back: now wait above 0.2 rad, and resync only
            # when > 0.35 rad persists for 1 s (really blocked, e.g. by the floor).
            lag = 0.0 if args.dry_run else float(np.max(np.abs(self.q_cmd - q_meas)))
            if lag > LAG_BLOCK:
                self.block_since = self.block_since or time.monotonic()
                if time.monotonic() - self.block_since > 1.0:
                    self.say(f'arm stuck {lag:.2f} rad behind for 1 s (blocked?) - resync to the reading')
                    self.q_cmd, self.p_tgt = q_meas.copy(), tip(chain, q_meas)[0]
                    self.block_since = None
                return
            self.block_since = None
            if lag > LAG_WAIT:
                return                           # 따라올 때까지 기다림 / let the arm catch up
            fine = 0.3 if m.buttons[MAP['fine']] else 1.0
            # 데드존 0.15 + 제곱 곡선: 살짝 밀면 아주 느리게(미세 조정), 끝까지 밀면 최대 속도
            # dead zone + squared response: small push = very slow, full push = full speed
            ax = [math.copysign(((abs(a) - 0.15) / 0.85) ** 2, a) if abs(a) > 0.15 else 0.0 for a in m.axes]
            q_new = self.q_cmd.copy()
            if self.goal is not None:
                q_new = self.goal_step(q_new)
            elif self.joint_mode:
                # 스틱 하나에 관절 하나 / one stick axis per joint
                rate = JOINT_RATE * fine * PERIOD
                # joint1이 커지면 오른쪽으로 돌고(축이 아래), joint3이 커지면 손끝이 내려간다 → 둘은 부호를 뒤집어
                # 스틱 왼쪽 = 왼쪽으로 회전, 오른쪽 스틱 위 = 손끝 위로(사용자: 좌우 반대, 2026-10-18).
                # joint1+ turns right (axis points down) and joint3+ lowers the tip: both negated so that
                # stick left = turn left and right stick up = tip up.
                # joint2도 커지면 손끝이 뒤·아래로 가서 뒤집음(스틱 위 = 손끝 앞·위) / joint2 negated too
                dq = np.array([-ax[MAP['ax_y']], -ax[MAP['ax_x']], -ax[MAP['ax_z']], ax[MAP['ax_wrist']],
                               ax[MAP['ax_dpad_x']]]) * rate
                q_try = np.clip(self.q_cmd + dq, -1.65, 1.65)
                if np.any(dq):
                    if tip(chain, q_try)[0][2] < lo[2] and tip(chain, q_try)[0][2] < self.p_tgt[2]:
                        self.say('joint move would put the fingertip below the floor - not moving')
                    else:
                        q_new = q_try
                        self.p_tgt = tip(chain, q_new)[0]
            else:
                sgn = -1.0 if self.flip else 1.0
                v = np.array([sgn * ax[MAP['ax_x']], sgn * ax[MAP['ax_y']], ax[MAP['ax_z']]]) \
                    * args.speed * fine * PERIOD
                if np.any(v):
                    # 목표점을 따로 누적한다: 매번 풀린 자세에서 다시 더하면 IK 오차가 쌓여 앞으로만 밀어도
                    # 손끝이 4.7 cm 내려갔다(계산 시험). Keep an integrated target: re-adding to the solved pose
                    # let the IK error pile up (4.7 cm drop over 40 forward steps).
                    target = np.clip(self.p_tgt + v, lo, hi)
                    q_try, err = local_ik(chain, self.q_cmd, target)
                    dq = np.max(np.abs(q_try - self.q_cmd))
                    if err > 0.003 or dq > 0.15:
                        self.say(f'out of reach (IK err {1000 * err:.1f} mm, step {dq:.2f} rad) - not moving')
                    else:
                        q_new, self.p_tgt = q_try, target
                q_new[4] = float(np.clip(q_new[4] + ax[MAP['ax_wrist']] * 0.3 * fine * PERIOD, -1.65, 1.65))
            g = self.grip_cmd
            if m.buttons[MAP['close']]:
                g = max(GRIP_CLOSED, g - 0.5 * fine * PERIOD)
            if m.buttons[MAP['open']]:
                g = min(GRIP_OPEN, g + 0.5 * fine * PERIOD)
            # 큐브에 막히면 명령이 실제보다 계속 앞서 나가 base_node가 큰 스텝으로 거부했다(−0.11에서 막혔는데
            # 명령 −0.75). 실제 위치에서 0.25 rad 이상 앞서지 않게 / never lead the measured gripper by > 0.25 rad
            r = self.js['r_joint']
            g = float(np.clip(g, r - 0.25, r + 0.25))
            arm_changed = np.max(np.abs(q_new - self.q_cmd)) > 1e-4
            grip_changed = abs(g - self.grip_cmd) > 1e-4
            changed = arm_changed or grip_changed
            self.q_cmd, self.grip_cmd = q_new, g
            if arm_changed:
                self.send(ARM, q_new)
            if grip_changed:
                self.send(['r_joint'], [g])
            now = time.monotonic()
            if now - self.last_print > 1.0 and (changed or args.dry_run):
                p, tilt = tip(chain, q_new)
                tag = ('[dry] ' if args.dry_run else '') + ('J ' if self.joint_mode else '')
                self.say(f'{tag}tip ({p[0]:.3f}, {p[1]:.3f}) '
                         f'{100 * (p[2] - args.floor_z):.1f} cm up, tilt {tilt:.0f} deg, wrist {q_new[4]:+.2f}, '
                         f'grip {g:+.2f} | sticks x {ax[MAP["ax_x"]]:+.1f} y {ax[MAP["ax_y"]]:+.1f} '
                         f'z {ax[MAP["ax_z"]]:+.1f} w {ax[MAP["ax_wrist"]]:+.1f}')
                self.last_print = now

    rclpy.init()
    node = Jog()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
