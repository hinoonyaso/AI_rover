#!/usr/bin/env python3
# 한글: 엔코더 odom 정확도 시험 1회(prd/encoder-odometry-test-plan.md E4). /cmd_vel로 정해진 거리/각도만큼 움직이고
#       시작·끝의 odom_raw(엔코더 적분, wheel_twist_source:=encoder), /odom(EKF), 명령값 적분(open-loop 상당)을 기록한다.
#       로봇이 실제로 움직인다 — 사람이 옆에서, 주변 공간 확보. 실측값은 끝난 뒤 --measured로 넣는다.
"""One odometry accuracy trial (encoder-odometry test plan E4). THE ROBOT MOVES.

Needs base_node with wheel_twist_source:=encoder (odom_raw = integrated encoder twist) and the EKF.
    python3 tools/nav/odom_accuracy_trial.py fwd 1.0  [--speed 0.1]      # straight 1 m
    python3 tools/nav/odom_accuracy_trial.py left 1.0 [--speed 0.1]      # strafe left 1 m
    python3 tools/nav/odom_accuracy_trial.py ccw 360  [--speed 0.3]      # rotate 360 deg (rad/s)
    python3 tools/nav/odom_accuracy_trial.py --measured <trial_id> <value>   # cm or deg, tape/protractor
Duration = target / speed (constant command, then 1 s of zero). Prints, per source, the distance along
the intended axis (cm) or the yaw change (deg):
  command  = commanded velocity x duration (what open-loop odom would report)
  encoder  = odom_raw start->end
  ekf      = /odom start->end (encoder twist + gyro yaw)
Appends to Log/odom_accuracy.csv; --measured fills the measured column of that row.
"""
import argparse
import csv
import math
import os
import time

CSV = 'Log/odom_accuracy.csv'
FIELDS = ['trial_id', 'motion', 'target', 'speed', 'duration_s', 'command', 'encoder', 'ekf',
          'encoder_cross', 'ekf_yaw_deg', 'measured']


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def set_measured(trial_id, value):
    rows = list(csv.DictReader(open(CSV)))
    hit = [r for r in rows if r['trial_id'] == trial_id]
    if not hit:
        raise SystemExit(f'no trial {trial_id} in {CSV}')
    hit[0]['measured'] = value
    with open(CSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    r = hit[0]
    m = float(value)
    for k in ('command', 'encoder', 'ekf'):
        v = float(r[k])
        print(f'  {k:8s} {v:8.1f}  error {v - m:+6.1f} ({(v - m) / m * 100:+.1f} %)')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('motion', nargs='?', choices=['fwd', 'left', 'ccw'])
    ap.add_argument('target', nargs='?', type=float, help='m (fwd/left) or deg (ccw)')
    ap.add_argument('--speed', type=float, help='m/s or rad/s (default 0.1 / 0.3)')
    ap.add_argument('--measured', nargs=2, metavar=('TRIAL_ID', 'VALUE'))
    args = ap.parse_args()
    if args.measured:
        set_measured(*args.measured)
        return
    if args.motion is None or args.target is None:
        ap.error('motion and target are required')

    import rclpy
    from geometry_msgs.msg import Twist
    from nav_msgs.msg import Odometry

    rotate = args.motion == 'ccw'
    speed = args.speed or (0.3 if rotate else 0.1)
    if (not rotate and not 0 < speed <= 0.15) or (rotate and not 0 < speed <= 0.6):
        raise SystemExit('speed limits for this test: <= 0.15 m/s, <= 0.6 rad/s')
    target_si = math.radians(args.target) if rotate else args.target
    duration = target_si / speed

    rclpy.init()
    node = rclpy.create_node('odom_accuracy_trial')
    pub = node.create_publisher(Twist, '/cmd_vel', 10)
    last = {}
    node.create_subscription(Odometry, '/odom_raw', lambda m: last.__setitem__('encoder', m), 10)
    node.create_subscription(Odometry, '/odom', lambda m: last.__setitem__('ekf', m), 10)

    def spin(sec):
        t0 = time.time()
        while time.time() - t0 < sec:
            rclpy.spin_once(node, timeout_sec=0.02)

    # wait for DDS discovery (up to 5 s; 1.5 s was once too short) / DDS 연결 대기(최대 5초)
    t_wait = time.time()
    while ('encoder' not in last or 'ekf' not in last) and time.time() - t_wait < 5.0:
        spin(0.1)
    spin(0.5)
    if 'encoder' not in last or 'ekf' not in last:
        raise SystemExit('no /odom_raw or /odom (base_node + EKF running?)')
    start = {k: v.pose.pose for k, v in last.items()}
    cmd = Twist()
    if args.motion == 'fwd':
        cmd.linear.x = speed
    elif args.motion == 'left':
        cmd.linear.y = speed
    else:
        cmd.angular.z = speed
    try:
        t0 = time.time()
        while time.time() - t0 < duration:
            pub.publish(cmd)
            spin(0.05)
    finally:
        for _ in range(20):  # 1 s of zero / 정지 명령 1초
            pub.publish(Twist())
            spin(0.05)
    spin(1.0)
    end = {k: v.pose.pose for k, v in last.items()}

    def along(k):
        """Displacement along / across the intended axis in the START body frame, and yaw change."""
        p0, p1 = start[k], end[k]
        y0 = yaw_of(p0.orientation)
        dx, dy = p1.position.x - p0.position.x, p1.position.y - p0.position.y
        fx = dx * math.cos(y0) + dy * math.sin(y0)
        fy = -dx * math.sin(y0) + dy * math.cos(y0)
        dyaw = math.degrees(math.atan2(math.sin(yaw_of(p1.orientation) - y0),
                                       math.cos(yaw_of(p1.orientation) - y0)))
        return fx, fy, dyaw

    enc, ekf = along('encoder'), along('ekf')
    if rotate:
        # unwrap: the commanded turn may exceed 180 deg / 180도 넘는 회전은 명령 방향으로 감기
        def unwrap(d):
            return d + 360.0 * round((args.target - d) / 360.0)
        command, encoder, ekf_v = args.target, unwrap(enc[2]), unwrap(ekf[2])
        cross = math.hypot(enc[0], enc[1]) * 100
    else:
        i = 0 if args.motion == 'fwd' else 1
        command = speed * duration * 100
        encoder, ekf_v = enc[i] * 100, ekf[i] * 100
        cross = enc[1 - i] * 100
    unit = 'deg' if rotate else 'cm'
    trial_id = time.strftime('%H%M%S')
    print(f'trial {trial_id}: {args.motion} {args.target} at {speed}, {duration:.1f} s')
    print(f'  command  {command:8.1f} {unit}')
    print(f'  encoder  {encoder:8.1f} {unit}   (cross-axis {cross:+.1f} cm)')
    print(f'  ekf      {ekf_v:8.1f} {unit}   (ekf yaw change {ekf[2]:+.1f} deg)')
    print(f'measure it, then: python3 tools/nav/odom_accuracy_trial.py --measured {trial_id} <{unit}>')
    os.makedirs('Log', exist_ok=True)
    new = not os.path.exists(CSV)
    with open(CSV, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow({'trial_id': trial_id, 'motion': args.motion, 'target': args.target,
                    'speed': speed, 'duration_s': round(duration, 2), 'command': round(command, 1),
                    'encoder': round(encoder, 1), 'ekf': round(ekf_v, 1),
                    'encoder_cross': round(cross, 1), 'ekf_yaw_deg': round(ekf[2], 1),
                    'measured': ''})
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
