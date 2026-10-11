#!/usr/bin/env python3
# 한글: 버스 서보 데드밴드 보정값 측정. 현재 위치 주변 목표들로 "이동 방향으로 목표를 N눈금 넘겨 명령"(N=0..4)을 시험하고
#       오차(읽은 값 - 목표)가 가장 작은 N을 고른다. 서보가 움직인다(±span 눈금). base_node가 꺼져 있어야 한다.
"""Measure each bus servo's dead band compensation: command the target N pulses beyond it in the travel direction.

Usage: python3 tools/stm32_diagnostics/servo_deadband.py --ids 5,10 [--span 25] [--load-first] [--offsets 0,1,2,3,4]
THE JOINT MOVES by about +-span pulses (0.24 deg each) around where it is. For limp joints (power-up state) pass
--load-first: the target is pinned to the current position, then torque is loaded; SUPPORT THE ARM (joints 2-4 hold it up).
Stops and releases torque for a cool-down if a servo is above the 75 C safety limit.
"""
import argparse
import os
import struct
import sys
import time

import serial

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rrc_m4_io_test import read_bus_servo, servo_temp, move_bus_servo, TEMP_LIMIT_C  # noqa: E402
from rrc_m4_raw_pwm_test import frame, PORT  # noqa: E402


def median_read(ser, sid):
    v = sorted(x for x in (read_bus_servo(ser, sid, tries=2) for _ in range(3)) if x is not None)
    return v[len(v) // 2] if v else None


def pin_and_load(ser, sid):
    p = median_read(ser, sid)
    if p is None:
        sys.exit(f'servo {sid}: no reading')
    ser.write(frame(0x05, bytes([0x01]) + struct.pack('<H', 500) + bytes([1, sid]) + struct.pack('<H', p)))
    time.sleep(0.8)
    ser.write(frame(0x05, bytes([0x0C, sid])))
    time.sleep(1.0)
    print(f'  servo {sid}: loaded at {median_read(ser, sid)}')


def cool(ser, sid):
    p = median_read(ser, sid)
    print(f'  servo {sid} hot: releasing torque to cool (support it)')
    ser.write(frame(0x05, bytes([0x0B, sid])))
    while True:
        t = servo_temp(ser, sid)
        print(f'    {t} C')
        if t is None or t <= 55:
            break
        time.sleep(15)
    p = median_read(ser, sid) or p
    ser.write(frame(0x05, bytes([0x01]) + struct.pack('<H', 500) + bytes([1, sid]) + struct.pack('<H', p)))
    time.sleep(0.8)
    ser.write(frame(0x05, bytes([0x0C, sid])))
    time.sleep(1.0)


def measure(ser, sid, span, offsets):
    centre = median_read(ser, sid)
    if centre is None:
        print(f'servo {sid}: no reading, skipped')
        return None
    targets = [centre + d for d in (span, -span, span // 2, -span, 0, span, -span // 2, 0)]
    result = {}
    for n in offsets:
        errs = []
        for tgt in targets:
            t = servo_temp(ser, sid)
            if t is not None and t >= TEMP_LIMIT_C:
                cool(ser, sid)
            cur = median_read(ser, sid)
            cmd = tgt + (n if tgt > cur else -n if tgt < cur else 0)
            move_bus_servo(ser, sid, cmd, 700)
            time.sleep(0.4)
            errs.append(median_read(ser, sid) - tgt)
        result[n] = errs
        print(f'  servo {sid} N={n}: errors {errs}  max|e| {max(map(abs, errs))}  '
              f'mean {sum(errs) / len(errs):+.1f}  temp {servo_temp(ser, sid)}', flush=True)
    move_bus_servo(ser, sid, centre, 700)
    best = min(result, key=lambda k: (max(map(abs, result[k])), sum(map(abs, result[k])), k))
    print(f'servo {sid}: best N={best} (max error {max(map(abs, result[best]))})')
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--ids', default='5,10')
    ap.add_argument('--span', type=int, default=25)
    ap.add_argument('--offsets', default='0,1,2,3,4')
    ap.add_argument('--load-first', action='store_true')
    args = ap.parse_args()
    ser = serial.Serial(PORT, 1_000_000, timeout=0.05)
    out = {}
    for sid in [int(x) for x in args.ids.split(',')]:
        if args.load_first:
            pin_and_load(ser, sid)
        out[sid] = measure(ser, sid, args.span, [int(x) for x in args.offsets.split(',')])
    print('summary (servo id -> overshoot pulses):', out)


if __name__ == '__main__':
    main()
