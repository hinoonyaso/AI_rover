#!/usr/bin/env python3
# 한글: 팔 서보 폴링 속도(arm_poll_hz) 벤치마크(T1, prd/arm-control-path.md). 읽기 전용 — 팔을 움직이지 않는다.
#       base_node를 `arm_command_enabled:=false arm_move_home_on_start:=false`로 띄운 상태에서, 속도를 바꿔 가며 구간마다
#       서보별 응답 수·누락·요청→응답 지연·응답 간격(서보 응답 프레임이 실제로 도착한 시각 기준, arm/servo_stats)과
#       IMU 수신률·최대 간격, odom_raw(50 Hz 타이머) 최대 간격(base_node 루프 지연의 대리 지표)을 잰다.
#       채택 판정(judge_rate)은 5 Hz 기준과 비교한다: 응답이 안정적이고 IMU에 영향이 없을 때만 채택.
"""Poll-rate benchmark for the arm servos (READ ONLY: base_node must run with arm commands and home move off).

Usage: python3 tools/stm32_diagnostics/arm_poll_bench.py [--rates 5,12,20,30,5] [--window 30] [--warmup 3]
Each rate is set at runtime (ros2 param arm_poll_hz), the servo stats are reset, then --window seconds are measured.
The last rate repeating the first one shows drift between windows (order effect).
Adoption rule (judge_rate), compared with the FIRST rate (the baseline). The servo bus loses some replies even at 5 Hz, so
"zero misses" is not a usable rule; a faster rate must simply not be worse than the baseline:
  - requests go out at >= 95 % of the expected per-servo rate (the poll timer keeps up);
  - the success ratio (replies / requests) is not more than SUCCESS_TOL below the baseline's (default 5 points: the
    spread seen between two identical 5 Hz windows) and the failure+loss ratio of no servo exceeds LOSS_MAX;
  - max request->reply latency not larger than max(1.5 x baseline, baseline + 20 ms);
  - IMU rate within 1 % of the baseline and its max gap not larger than max(1.5 x baseline, baseline + 20 ms);
  - odom_raw (the base_node loop timer) max gap not larger than max(1.5 x baseline, baseline + 20 ms).
The absolute loss numbers are always reported; a rate is "adopted" only when none of these fails.
"""
import argparse
import json
import os
import statistics as st
import sys
import time

SUCCESS_TOL = 0.05
LOSS_MAX = 0.15
REQ_BYTES, REPLY_BYTES = 7, 10   # AA 55 FUNC LEN [05 id] CRC / AA 55 FUNC LEN [id 05 ok pulse16] CRC


def window_stats(first, last, duration):
    """first/last: {servo_id: {requests, replies, misses, unmatched_replies, mean_latency_s, max_latency_s,
    mean_period_s, max_period_s}} read from arm/servo_stats (reset at the window start)."""
    out = {}
    for sid, b in last.items():
        out[sid] = {
            'requests': b['requests'], 'replies': b['replies'], 'misses': b['misses'],
            'failed': b.get('failed_replies', 0), 'unmatched': b['unmatched_replies'],
            'requests_per_s': b['requests'] / duration, 'replies_per_s': b['replies'] / duration,
            'mean_latency_ms': b['mean_latency_s'] * 1e3, 'max_latency_ms': b['max_latency_s'] * 1e3,
            'mean_period_s': b['mean_period_s'], 'max_period_s': b['max_period_s'],
        }
    return out


def gaps(stamps):
    d = [b - a for a, b in zip(stamps, stamps[1:])]
    return {'n': len(stamps), 'max_gap_s': max(d) if d else 0.0, 'mean_gap_s': st.mean(d) if d else 0.0}


def success_ratio(row):
    req = sum(s['requests'] for s in row['servos'].values())
    ok = sum(s['replies'] for s in row['servos'].values())
    return ok / req if req else 0.0


def judge_rate(baseline, row, n_servos=6):
    """(adopt, [reasons]) for one measured rate versus the baseline row. Pure; see the module docstring."""
    why = []
    if not row['servos']:
        return False, ['no servo stats received']
    expected = row['hz'] / n_servos
    for sid, s in row['servos'].items():
        if s['requests_per_s'] < 0.95 * expected:
            why.append(f"servo {sid}: only {s['requests_per_s']:.2f} requests/s of {expected:.2f}/s (timer cannot keep up)")
        loss = 1.0 - s['replies'] / s['requests'] if s['requests'] else 1.0
        if loss > LOSS_MAX:
            why.append(f"servo {sid}: {loss * 100:.0f} % of reads without a reading (> {LOSS_MAX * 100:.0f} %)")
    b_ok, r_ok = success_ratio(baseline), success_ratio(row)
    if r_ok < b_ok - SUCCESS_TOL:
        why.append(f"success ratio {r_ok * 100:.1f} % vs baseline {b_ok * 100:.1f} % "
                   f"(more than {SUCCESS_TOL * 100:.0f} points worse)")
    b_lat = max((s['max_latency_ms'] for s in baseline['servos'].values()), default=0.0) / 1e3
    r_lat = max((s['max_latency_ms'] for s in row['servos'].values()), default=0.0) / 1e3
    if r_lat > max(1.5 * b_lat, b_lat + 0.02):
        why.append(f"max latency {r_lat * 1e3:.0f} ms vs baseline {b_lat * 1e3:.0f} ms")
    bi, ri = baseline['imu'], row['imu']
    b_rate, r_rate = bi['n'] / baseline['duration'], ri['n'] / row['duration']
    if b_rate > 0 and abs(r_rate - b_rate) / b_rate > 0.01:
        why.append(f"IMU rate {r_rate:.1f} Hz vs baseline {b_rate:.1f} Hz (> 1 %)")
    if ri['max_gap_s'] > max(1.5 * bi['max_gap_s'], bi['max_gap_s'] + 0.02):
        why.append(f"IMU max gap {ri['max_gap_s'] * 1e3:.0f} ms vs baseline {bi['max_gap_s'] * 1e3:.0f} ms")
    bo, ro = baseline['odom'], row['odom']
    if ro['max_gap_s'] > max(1.5 * bo['max_gap_s'], bo['max_gap_s'] + 0.02):
        why.append(f"odom_raw max gap {ro['max_gap_s'] * 1e3:.0f} ms vs baseline {bo['max_gap_s'] * 1e3:.0f} ms")
    return (not why), why


def run(args):
    import rclpy
    from diagnostic_msgs.msg import DiagnosticArray
    from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue
    from rcl_interfaces.srv import SetParameters
    from sensor_msgs.msg import Imu
    from nav_msgs.msg import Odometry
    from rclpy.qos import qos_profile_sensor_data
    from std_srvs.srv import Trigger

    rclpy.init()
    n = rclpy.create_node('arm_poll_bench')
    stats = {}
    imu_t, odom_t = [], []

    def on_stats(m):
        for s in m.status:
            kv = {k.key: float(k.value) for k in s.values}
            stats[int(s.hardware_id)] = kv

    n.create_subscription(DiagnosticArray, 'arm/servo_stats', on_stats, 10)
    n.create_subscription(Imu, 'imu/data_raw', lambda m: imu_t.append(time.monotonic()), qos_profile_sensor_data)
    n.create_subscription(Odometry, 'odom_raw', lambda m: odom_t.append(time.monotonic()), 100)
    set_cli = n.create_client(SetParameters, '/base_node/set_parameters')
    reset_cli = n.create_client(Trigger, '/arm/servo_stats_reset')

    def spin(sec):
        t0 = time.monotonic()
        while time.monotonic() - t0 < sec:
            rclpy.spin_once(n, timeout_sec=0.02)

    def call(cli, req):
        if not cli.wait_for_service(timeout_sec=3.0):
            sys.exit(f'service {cli.srv_name} not available (is base_node running?)')
        fut = cli.call_async(req)
        rclpy.spin_until_future_complete(n, fut, timeout_sec=3.0)
        return fut.result()

    spin(1.5)
    if not stats:
        sys.exit('no arm/servo_stats: base_node not running, or built before the stats topic existed')
    rows = []
    for hz in [float(x) for x in args.rates.split(',')]:
        p = Parameter(name='arm_poll_hz', value=ParameterValue(type=ParameterType.PARAMETER_DOUBLE, double_value=hz))
        res = call(set_cli, SetParameters.Request(parameters=[p]))
        if not res or not res.results[0].successful:
            sys.exit(f'could not set arm_poll_hz={hz}: {res.results[0].reason if res else "no answer"}')
        spin(args.warmup)
        call(reset_cli, Trigger.Request())
        stats.clear()
        imu_t.clear()
        odom_t.clear()
        t0 = time.monotonic()
        spin(args.window)
        dur = time.monotonic() - t0
        spin(1.2)   # the stats topic is 1 Hz: make sure the last snapshot of the window has arrived
        last = {sid: dict(kv) for sid, kv in stats.items()}
        servos = window_stats(None, {sid: {'requests': kv['requests'], 'replies': kv['replies'], 'misses': kv['misses'],
                                           'failed_replies': kv['failed_replies'],
                                           'unmatched_replies': kv['unmatched_replies'],
                                           'mean_latency_s': kv['mean_latency_s'], 'max_latency_s': kv['max_latency_s'],
                                           'mean_period_s': kv['mean_period_s'], 'max_period_s': kv['max_period_s']}
                                     for sid, kv in last.items()}, dur + 1.2)
        reqs = sum(s['requests'] for s in servos.values())
        reps = sum(s['replies'] for s in servos.values())
        rows.append({'hz': hz, 'duration': dur, 'servos': servos, 'imu': gaps(imu_t), 'odom': gaps(odom_t),
                     'serial_bytes_per_s_est': (reqs * REQ_BYTES + reps * REPLY_BYTES) / (dur + 1.2)})
        print(f'{hz:g} Hz measured ({dur:.0f} s)', flush=True)
    n.destroy_node()
    rclpy.shutdown()
    return rows


def report(rows):
    base = rows[0]
    head = ['arm_poll_hz', '서보당 기대 [1/s]', '요청률 최소 [1/s]', '성공률 [%]', '서보 무응답(STM32 실패 프레임)', '프레임 유실',
            '지연 평균/최대 [ms]', '응답 간격 최대 [s]', 'IMU [Hz] / 최대 간격 [ms]', 'odom_raw 최대 간격 [ms]',
            '시리얼 추정 [B/s]', '판정']
    lines = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
    for i, r in enumerate(rows):
        ok, why = judge_rate(base, r) if i else (True, ['baseline'])
        sv = list(r['servos'].values())
        lat_mean = st.mean(s['mean_latency_ms'] for s in sv) if sv else 0
        lat_max = max((s['max_latency_ms'] for s in sv), default=0)
        lines.append('| %g | %.2f | %.2f | %.1f | %d | %d | %.1f / %.1f | %.2f | %.1f / %.0f | %.0f | %.0f | %s |' % (
            r['hz'], r['hz'] / 6, min((s['requests_per_s'] for s in sv), default=0), success_ratio(r) * 100,
            sum(s['failed'] for s in sv), sum(s['misses'] for s in sv), lat_mean, lat_max,
            max((s['max_period_s'] for s in sv), default=0), r['imu']['n'] / r['duration'], r['imu']['max_gap_s'] * 1e3,
            r['odom']['max_gap_s'] * 1e3, r['serial_bytes_per_s_est'],
            '기준' if i == 0 else ('채택 가능' if ok else '불가: ' + '; '.join(why))))
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--rates', default='5,12,20,30,5')
    ap.add_argument('--window', type=float, default=30.0)
    ap.add_argument('--warmup', type=float, default=3.0)
    args = ap.parse_args()
    rows = run(args)
    os.makedirs('Log', exist_ok=True)
    path = 'Log/arm_poll_bench_%s.json' % time.strftime('%Y%m%d_%H%M%S')
    json.dump(rows, open(path, 'w'), indent=1)
    print(report(rows))
    print('raw data:', path)


if __name__ == '__main__':
    main()
