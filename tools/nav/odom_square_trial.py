#!/usr/bin/env python3
# 한글: EKF 왕복(원점 복귀) 시험(prd/encoder-odometry-test-plan.md E5). 몸 방향을 유지한 채 메카넘으로 사각형
#       (앞 → 왼쪽 → 뒤 → 오른쪽, 각 SIDE m)을 돌아 출발점으로 돌아오고, 끝에서 odom이 보는 출발점 대비 위치/방향을 출력한다.
#       이상적으로는 (0, 0, 0°). 실측(출발 표시 대비 앞뒤/좌우 cm, 방향 °)과 비교한다. 로봇이 실제로 움직인다.
"""Closed-loop square (return-to-start) trial for EKF drift, test plan E5. THE ROBOT MOVES.

Needs base_node (wheel_twist_source:=encoder for the encoder run) and the EKF.
    python3 tools/nav/odom_square_trial.py [--side 1.0] [--speed 0.1]
Legs, body heading kept: +x (forward), +y (left), -x (back), -y (right), each side/speed seconds,
0.5 s of zero between legs. Prints the final pose relative to the start in the START body frame for
odom_raw (encoder integration) and /odom (EKF): forward/left offset [cm] and heading change [deg].
Appends to Log/odom_square.csv; fill the tape measurement with --measured ID FWD_CM LEFT_CM YAW_DEG.
"""
import argparse
import csv
import math
import os
import time

CSV = 'Log/odom_square.csv'
FIELDS = ['trial_id', 'side', 'speed', 'source', 'enc_fwd_cm', 'enc_left_cm', 'enc_yaw_deg',
          'ekf_fwd_cm', 'ekf_left_cm', 'ekf_yaw_deg', 'meas_fwd_cm', 'meas_left_cm', 'meas_yaw_deg']


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def set_measured(trial_id, fwd, left, yaw):
    rows = list(csv.DictReader(open(CSV)))
    hit = [r for r in rows if r['trial_id'] == trial_id]
    if not hit:
        raise SystemExit(f'no trial {trial_id} in {CSV}')
    hit[0].update({'meas_fwd_cm': fwd, 'meas_left_cm': left, 'meas_yaw_deg': yaw})
    with open(CSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    r = hit[0]
    for k in ('enc', 'ekf'):
        print(f'  {k}: fwd {float(r[k + "_fwd_cm"]):+.1f} (meas {fwd}), left {float(r[k + "_left_cm"]):+.1f} '
              f'(meas {left}), yaw {float(r[k + "_yaw_deg"]):+.1f} (meas {yaw})')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--side', type=float, default=1.0)
    ap.add_argument('--speed', type=float, default=0.1)
    ap.add_argument('--source', default='encoder', help='label only: the base_node wheel_twist_source')
    ap.add_argument('--measured', nargs=4, metavar=('TRIAL_ID', 'FWD_CM', 'LEFT_CM', 'YAW_DEG'))
    args = ap.parse_args()
    if args.measured:
        set_measured(*args.measured)
        return
    if not 0 < args.speed <= 0.15 or not 0 < args.side <= 1.5:
        raise SystemExit('limits for this test: speed <= 0.15 m/s, side <= 1.5 m')

    import rclpy
    from geometry_msgs.msg import Twist
    from nav_msgs.msg import Odometry

    rclpy.init()
    node = rclpy.create_node('odom_square_trial')
    pub = node.create_publisher(Twist, '/cmd_vel', 10)
    last = {}
    node.create_subscription(Odometry, '/odom_raw', lambda m: last.__setitem__('enc', m), 10)
    node.create_subscription(Odometry, '/odom', lambda m: last.__setitem__('ekf', m), 10)

    def spin(sec):
        t0 = time.time()
        while time.time() - t0 < sec:
            rclpy.spin_once(node, timeout_sec=0.02)

    t_wait = time.time()
    while ('enc' not in last or 'ekf' not in last) and time.time() - t_wait < 5.0:
        spin(0.1)
    spin(0.5)
    if 'enc' not in last or 'ekf' not in last:
        raise SystemExit('no /odom_raw or /odom (base_node + EKF running?)')
    start = {k: v.pose.pose for k, v in last.items()}
    legs = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    leg_s = args.side / args.speed
    try:
        for i, (sx, sy) in enumerate(legs):
            name = 'forward' if sx > 0 else 'back' if sx < 0 else 'left' if sy > 0 else 'right'
            print(f'  leg {i + 1}/4: {name}')
            cmd = Twist()
            cmd.linear.x, cmd.linear.y = sx * args.speed, sy * args.speed
            t0 = time.time()
            while time.time() - t0 < leg_s:
                pub.publish(cmd)
                spin(0.05)
            t0 = time.time()
            while time.time() - t0 < 0.5:
                pub.publish(Twist())
                spin(0.05)
    finally:
        for _ in range(20):
            pub.publish(Twist())
            spin(0.05)
    spin(1.0)
    end = {k: v.pose.pose for k, v in last.items()}

    res = {}
    for k in ('enc', 'ekf'):
        p0, p1 = start[k], end[k]
        y0 = yaw_of(p0.orientation)
        dx, dy = p1.position.x - p0.position.x, p1.position.y - p0.position.y
        fwd = dx * math.cos(y0) + dy * math.sin(y0)
        left = -dx * math.sin(y0) + dy * math.cos(y0)
        d = yaw_of(p1.orientation) - y0
        res[k] = (fwd * 100, left * 100, math.degrees(math.atan2(math.sin(d), math.cos(d))))
    trial_id = time.strftime('%H%M%S')
    print(f'square {trial_id}: side {args.side} m at {args.speed} m/s (source {args.source})')
    for k, (f, l, y) in res.items():
        print(f'  {k}: end vs start  fwd {f:+.1f} cm  left {l:+.1f} cm  heading {y:+.1f} deg')
    print(f'measure (from the start mark), then: python3 tools/nav/odom_square_trial.py --measured '
          f'{trial_id} <fwd_cm> <left_cm> <yaw_deg, + = turned left>')
    os.makedirs('Log', exist_ok=True)
    new = not os.path.exists(CSV)
    with open(CSV, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow({'trial_id': trial_id, 'side': args.side, 'speed': args.speed, 'source': args.source,
                    'enc_fwd_cm': round(res['enc'][0], 1), 'enc_left_cm': round(res['enc'][1], 1),
                    'enc_yaw_deg': round(res['enc'][2], 1), 'ekf_fwd_cm': round(res['ekf'][0], 1),
                    'ekf_left_cm': round(res['ekf'][1], 1), 'ekf_yaw_deg': round(res['ekf'][2], 1),
                    'meas_fwd_cm': '', 'meas_left_cm': '', 'meas_yaw_deg': ''})
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
