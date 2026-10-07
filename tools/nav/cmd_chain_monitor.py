#!/usr/bin/env python3
# 한글: Nav2 속도 명령 체인(DWB -> smoother -> collision_monitor -> base)을 실시간으로 보여주고,
#       "누가 멈췄나", vy 좌우 뒤집힘 횟수, AMCL map->odom 점프를 함께 기록한다. 로봇에 명령은 보내지 않는다(구독만).
"""Live view of the Nav2 velocity chain, read-only (troubleshooting/031).

    cmd_vel_nav (DWB) -> cmd_vel_smoothed (velocity_smoother) -> cmd_vel (collision_monitor) -> base_node

Prints one line per period with the three stages, the collision_monitor state, and flags:
  CM-STOP / CM-SLOW : DWB asks to move but collision_monitor zeroed / scaled the output
  vy-flips          : sign changes of cmd_vel_nav.linear.y (|vy| > deadband) in the last window
                      -- the lateral wobble metric for the DWB A/B test (tools/nav/dwb_ab.sh)
  map->odom jump    : AMCL correction larger than the thresholds since the last line
                      -- compare its timing with the vy flips (AMCL-induced wobble hypothesis)

Usage: python3 tools/nav/cmd_chain_monitor.py [--period 0.5] [--window 10]
At Ctrl+C prints a summary (time spent blocked by CM, total vy flips, jumps).
"""
import argparse
import collections
import math
import time

from geometry_msgs.msg import Twist, TwistStamped
from nav2_msgs.msg import CollisionMonitorState
import rclpy
from rclpy.node import Node
import tf2_ros

# nav2_msgs/CollisionMonitorState action_type values
ACTIONS = {0: 'none', 1: 'STOP', 2: 'SLOW', 3: 'APPROACH', 4: 'LIMIT'}
MOVING = 0.005  # m/s or rad/s; below this a command counts as "zero" / 이보다 작으면 정지로 봄
VY_DEADBAND = 0.01


def _mag(t):
    return math.hypot(t.linear.x, t.linear.y) + abs(t.angular.z)


class ChainMonitor(Node):
    def __init__(self, period, window, jump_xy, jump_yaw, stamped=False):
        super().__init__('cmd_chain_monitor')
        self.last = {'nav': None, 'smooth': None, 'out': None}
        self.cm = (0, '')
        self.window = window
        self.jump_xy, self.jump_yaw = jump_xy, jump_yaw
        self.flip_times = collections.deque()
        self.last_vy_sign = 0
        self.total_flips = 0
        self.jumps = []
        self.blocked_time = {'STOP': 0.0, 'SLOW': 0.0}
        self.prev_map_odom = None
        self.t0 = time.monotonic()
        # Jazzy Nav2 default is plain Twist (enable_stamped_cmd_vel: false); --stamped otherwise.
        # 한글: Jazzy 기본은 Twist. enable_stamped_cmd_vel을 켰다면 --stamped.
        for key, topic in (('nav', '/cmd_vel_nav'), ('smooth', '/cmd_vel_smoothed'),
                           ('out', '/cmd_vel')):
            if stamped:
                self.create_subscription(
                    TwistStamped, topic, lambda m, k=key: self._cmd(k, m.twist), 10)
            else:
                self.create_subscription(Twist, topic, lambda m, k=key: self._cmd(k, m), 10)
        self.create_subscription(
            CollisionMonitorState, '/collision_monitor_state', self._cm_cb, 10)
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        self.period = period
        self.create_timer(period, self._tick)

    def _cmd(self, key, twist):
        self.last[key] = twist
        if key == 'nav':
            vy = twist.linear.y
            sign = 0 if abs(vy) < VY_DEADBAND else (1 if vy > 0 else -1)
            if sign and self.last_vy_sign and sign != self.last_vy_sign:
                now = time.monotonic()
                self.flip_times.append(now)
                self.total_flips += 1
            if sign:
                self.last_vy_sign = sign

    def _cm_cb(self, msg):
        self.cm = (msg.action_type, msg.polygon_name)

    def _map_odom_jump(self):
        try:
            t = self.tf_buffer.lookup_transform('map', 'odom', rclpy.time.Time())
        except Exception:  # noqa: BLE001 -- AMCL not running yet
            return ''
        q = t.transform.rotation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        cur = (t.transform.translation.x, t.transform.translation.y, yaw)
        prev, self.prev_map_odom = self.prev_map_odom, cur
        if prev is None:
            return ''
        dxy = math.hypot(cur[0] - prev[0], cur[1] - prev[1])
        dyaw = abs(math.atan2(math.sin(cur[2] - prev[2]), math.cos(cur[2] - prev[2])))
        if dxy > self.jump_xy or dyaw > self.jump_yaw:
            self.jumps.append((time.monotonic() - self.t0, dxy, dyaw))
            return f' map->odom JUMP {dxy * 100:.1f}cm {math.degrees(dyaw):.1f}deg'
        return ''

    def _tick(self):
        now = time.monotonic()
        while self.flip_times and now - self.flip_times[0] > self.window:
            self.flip_times.popleft()
        nav, smooth, out = self.last['nav'], self.last['smooth'], self.last['out']

        def fmt(t):
            if t is None:
                return '      --       '
            return f'{t.linear.x:+.3f} {t.linear.y:+.3f} {t.angular.z:+.2f}'

        action, poly = self.cm
        flag = ''
        if nav is not None and _mag(nav) > MOVING:
            act = ACTIONS.get(action, str(action))
            if out is not None and _mag(out) <= MOVING and act == 'STOP':
                flag = f' <<CM-STOP {poly}>>'
                self.blocked_time['STOP'] += self.period
            elif act == 'SLOW':
                flag = f' <<CM-SLOW {poly}>>'
                self.blocked_time['SLOW'] += self.period
            elif out is not None and _mag(out) <= MOVING and smooth is not None \
                    and _mag(smooth) <= MOVING:
                flag = ' (smoother ramp/zero)'
        flag += self._map_odom_jump()
        print(f'{now - self.t0:7.1f}s  nav[{fmt(nav)}]  smooth[{fmt(smooth)}]  out[{fmt(out)}]'
              f'  cm={ACTIONS.get(action, action)}  vy-flips/{self.window:.0f}s='
              f'{len(self.flip_times)}{flag}', flush=True)

    def summary(self):
        dur = time.monotonic() - self.t0
        print('\n--- summary / 요약 ---')
        print(f'duration {dur:.1f}s, total vy sign flips {self.total_flips} '
              f'({self.total_flips / max(dur, 1e-6) * 60:.1f}/min)')
        print(f'collision_monitor blocked while DWB wanted to move: STOP {self.blocked_time["STOP"]:.1f}s,'
              f' SLOW {self.blocked_time["SLOW"]:.1f}s')
        print(f'map->odom jumps (> {self.jump_xy * 100:.0f}cm or > {math.degrees(self.jump_yaw):.0f}deg): '
              f'{len(self.jumps)}')
        for t, dxy, dyaw in self.jumps:
            print(f'  t={t:.1f}s  {dxy * 100:.1f}cm  {math.degrees(dyaw):.1f}deg')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--period', type=float, default=0.5, help='print period s')
    ap.add_argument('--window', type=float, default=10.0, help='vy flip counting window s')
    ap.add_argument('--jump-xy', type=float, default=0.03, help='map->odom jump threshold m')
    ap.add_argument('--stamped', action='store_true', help='cmd_vel topics are TwistStamped')
    ap.add_argument('--jump-yaw-deg', type=float, default=2.0, help='map->odom jump threshold deg')
    args = ap.parse_args()
    rclpy.init()
    node = ChainMonitor(args.period, args.window, args.jump_xy, math.radians(args.jump_yaw_deg),
                        args.stamped)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.summary()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
