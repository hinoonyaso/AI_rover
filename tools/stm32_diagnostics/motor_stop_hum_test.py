#!/usr/bin/env python3
# 한글: 정지 후 바퀴 "웅" 소리(멈춘 바퀴에 PWM이 남는 현상) 재현/해결 시험 (troubleshooting/032).
#       바퀴를 띄우고 사람이 전원 스위치 옆에 있을 때만. base_node가 꺼져 있어야 한다(같은 시리얼 포트).
"""Reproduce / fix the wheel hum after stop (troubleshooting/032). WHEELS LIFTED ONLY.

base_node must NOT be running (it owns the serial port). One phase per run, so the
operator can listen between phases (the STM32 keeps its motor state between runs):

  hum      : drive all wheels at --rps (default 0.02 rev/s, below the motor dead zone) for
             --seconds, then send speed 0 (subcommand 0x01) -- exactly what base_node does today
  zero     : send speed 0 again (0x01) only
  stopall  : send the documented "stop several motors" frame (subcommand 0x03, mask 0x0F)
  spin     : visible check that motors still respond after stopall: --rps for --seconds, then 0
Every phase ends by sending speed 0 in a finally block, and checks that the STM32 is alive
(battery/IMU frames) before and after.
"""
import argparse
import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rrc_raw import BAUD, build_frame, FrameReader, PORT  # noqa: E402
import serial  # noqa: E402

FUNC_MOTOR = 0x03


def speed_frame(rps):
    # ids 0..3 = LF, LB, RF, RB; right side negative for forward (AGENTS.md "확정된 사실")
    # 한글: 오른쪽 모터(ID 2,3)는 전진이 음수
    data = bytes([0x01, 4])
    for mid, sign in ((0, 1), (1, 1), (2, -1), (3, -1)):
        data += bytes([mid]) + struct.pack('<f', sign * rps)
    return build_frame(FUNC_MOTOR, data)


def stop_all_frame(mask=0x0F):
    return build_frame(FUNC_MOTOR, bytes([0x03, mask]))


def alive(ser, secs=1.0):
    reader = FrameReader(ser)
    t0, n = time.time(), 0
    while time.time() - t0 < secs:
        n += len(reader.poll())
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('phase', choices=['hum', 'zero', 'stopall', 'spin'])
    ap.add_argument('--rps', type=float, default=0.02)
    ap.add_argument('--seconds', type=float, default=15.0)
    args = ap.parse_args()
    if abs(args.rps) > 0.5:
        sys.exit('refusing |rps| > 0.5 for this test')

    ser = serial.Serial(PORT, BAUD, timeout=0.02)
    done = False
    try:
        n = alive(ser)
        print(f'STM32 frames in 1 s before: {n}')
        if n == 0:
            sys.exit('STM32 silent -- not sending anything')
        if args.phase in ('hum', 'spin'):
            print(f'driving all wheels at {args.rps} rps for {args.seconds} s ...', flush=True)
            t0 = time.time()
            while time.time() - t0 < args.seconds:
                ser.write(speed_frame(args.rps))
                time.sleep(0.1)
            ser.write(speed_frame(0.0))
            print('sent speed 0 (subcommand 0x01) -- listen now')
        elif args.phase == 'zero':
            ser.write(speed_frame(0.0))
            print('sent speed 0 (subcommand 0x01)')
        else:
            f = stop_all_frame()
            ser.write(f)
            print('sent stop-all ' + f.hex(' '))
        time.sleep(0.3)
        print(f'STM32 frames in 1 s after: {alive(ser)}')
        done = True
    finally:
        # Safety stop on any error. Not after a clean stopall: speed 0 (0x01) would re-arm the speed
        # loop and defeat what is being tested. 한글: 오류 시엔 항상 속도 0. 정상 stopall 뒤엔 보내지 않음(시험 무효화 방지).
        if not (done and args.phase == 'stopall'):
            ser.write(speed_frame(0.0))
        ser.flush()
        ser.close()


if __name__ == '__main__':
    main()
