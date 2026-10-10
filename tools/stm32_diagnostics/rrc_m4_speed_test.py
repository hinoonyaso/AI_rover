#!/usr/bin/env python3
# 한글: 자체 펌웨어(rrc_m4) 바퀴 하나 속도 제어(PID) 시험. vendor와 같은 FUNC3 속도 명령(rps)을 0.1초마다 보내고
#       엔코더로 잰 rps 추종과 카운트 변화를 출력한다. 바퀴가 실제로 돈다 — 바퀴를 띄우고 사람이 모터 스위치 옆에.
#       바퀴에 표시를 하고 실제 회전 수를 세면 한 바퀴당 카운트(ticks_per_circle)를 구할 수 있다.
"""Closed-loop speed test for one wheel on the rrc_m4 firmware (FUNC3, vendor format). THE WHEEL SPINS.

Usage: python3 tools/stm32_diagnostics/rrc_m4_speed_test.py --motor 0 --rps 0.5 --secs 10
Command convention = vendor: left wheels (0, 1) +rps roll forward, right wheels (2, 3) +rps roll backward.
Prints the measured rps (firmware estimate from MOTOR_TICKS_PER_CIRCLE, 3996 measured 2026-10-10), its mean/std over the second
half, and the encoder counter change. Count the real revolutions of a marked wheel:
    ticks_per_rev = counter_delta / revolutions
Clears e-stop to start, and sets e-stop at the end (also on Ctrl+C) so the PID stops acting.
"""
import argparse
import statistics
import struct
import sys
import time
import os

import serial

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rrc_m4_raw_pwm_test import DIAG_CLEAR_ESTOP, DIAG_ESTOP, FUNC_DIAG, PORT, frame, Reader  # noqa: E402

FUNC_MOTOR = 0x03


def speed_cmd(motor, rps):
    return frame(FUNC_MOTOR, bytes([0x01, 1, motor]) + struct.pack('<f', rps))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--motor', type=int, required=True, choices=[0, 1, 2, 3])
    ap.add_argument('--rps', type=float, default=0.5)
    ap.add_argument('--secs', type=float, default=10.0)
    args = ap.parse_args()
    if abs(args.rps) > 2.0:
        raise SystemExit('|rps| <= 2.0 for this test')
    ser = serial.Serial(PORT, 1_000_000, timeout=0.05)
    rd = Reader(ser)
    rd.start()
    time.sleep(0.5)
    if rd.status is None:
        raise SystemExit('no STATUS frames: rrc_m4 firmware not running?')
    samples = []
    try:
        ser.write(frame(FUNC_DIAG, bytes([DIAG_CLEAR_ESTOP])))
        time.sleep(0.1)
        c0 = rd.counter[args.motor]
        t0 = time.time()
        next_print = 0.0
        while (t := time.time() - t0) < args.secs:
            ser.write(speed_cmd(args.motor, args.rps))
            r = rd.rps[args.motor]
            if t > args.secs / 2:
                samples.append(r)
            if t >= next_print:
                st = rd.status
                print(f'  t {t:5.1f} s  rps {r:+.3f}  fault {list(st[4:8])} flags 0x{st[0]:02x}')
                next_print += 1.0
            time.sleep(0.1)
        delta = rd.counter[args.motor] - c0
    finally:
        ser.write(speed_cmd(args.motor, 0.0))
        ser.write(frame(FUNC_DIAG, bytes([DIAG_ESTOP])))
        time.sleep(0.8)
        delta_end = rd.counter[args.motor] - c0
        rd.stop = True
        ser.close()
    if samples:
        print(f'target {args.rps:+.3f} rps: second-half mean {statistics.mean(samples):+.3f}, '
              f'std {statistics.pstdev(samples):.3f} (n {len(samples)})')
    print(f'counter delta during the command {delta}, incl. stop {delta_end}; '
          f'= {delta / 3996:.2f} rev at 3996 ticks/rev (measured 2026-10-10)')
    print('e-stop set')


if __name__ == '__main__':
    main()
