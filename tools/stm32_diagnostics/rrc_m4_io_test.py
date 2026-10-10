#!/usr/bin/env python3
# 한글: 자체 펌웨어(rrc_m4) 보조 입출력 브링업 시험: 버튼(FUNC6), 부저(FUNC2), 게임패드(FUNC8), SBUS(FUNC9), PWM 서보(FUNC4).
#       바퀴·팔은 움직이지 않는다(PWM 서보 명령은 그 포트에 꽂힌 서보만 움직인다). base_node가 꺼져 있어야 한다(같은 포트).
"""Bring-up checks for the rrc_m4 auxiliary I/O. Does not drive wheels or the arm.

Usage: python3 tools/stm32_diagnostics/rrc_m4_io_test.py <mode> [options]
  buttons  [--secs 20]          print button events (FUNC6) while you press the board buttons
  buzzer   [--on 100 --off 100 --cycles 3 --freq 2000]   send a beep pattern (FUNC2)
  gamepad  [--secs 20]          print gamepad changes (FUNC8) and raw HID reports (0x23)
  sbus     [--secs 10]          print SBUS frames (FUNC9) if a receiver is connected
  pwm-servo --id 1 --pulse 1500 [--time 500]   move one PWM servo (FUNC4 sub 0x03); 500..2500 us
Needs base_node NOT running (it owns the serial port).
"""
import argparse
import os
import struct
import sys
import time

import serial

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rrc_m4_diag import frames  # noqa: E402
from rrc_m4_raw_pwm_test import frame, PORT  # noqa: E402

EVENTS = {0x01: 'PRESSED', 0x02: 'LONGPRESS', 0x20: 'CLICK', 0x40: 'DOUBLE_CLICK'}


def listen(ser, secs, want, show):
    buf, t0, seen = b'', time.time(), 0
    last = {}  # per function: two frame types interleave (gamepad 0x08 + raw HID 0x23) / 함수별 중복 제거
    while time.time() - t0 < secs:
        buf += ser.read(4096)
        cut = buf.rfind(b'\xAA\x55')
        if cut <= 0:
            continue
        chunk, buf = buf[:cut], buf[cut:]
        for f, d in frames(chunk):
            if f in want and d != last.get(f):
                show(time.time() - t0, f, d)
                last[f] = d
                seen += 1
    return seen


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('mode', choices=['buttons', 'buzzer', 'gamepad', 'sbus', 'pwm-servo'])
    ap.add_argument('--secs', type=float, default=20.0)
    ap.add_argument('--on', type=int, default=100)
    ap.add_argument('--off', type=int, default=100)
    ap.add_argument('--cycles', type=int, default=3)
    ap.add_argument('--freq', type=int, default=2000)
    ap.add_argument('--id', type=int, default=1)
    ap.add_argument('--pulse', type=int, default=1500)
    ap.add_argument('--time', type=int, default=500)
    args = ap.parse_args()
    ser = serial.Serial(PORT, 1_000_000, timeout=0.05)
    ser.reset_input_buffer()

    if args.mode == 'buttons':
        print(f'press the board buttons now ({args.secs:g} s)...')
        n = listen(ser, args.secs, {0x06}, lambda t, f, d: print(
            f'  {t:5.1f} s  button {d[0]}  {EVENTS.get(d[1], hex(d[1]))}'))
        print(f'{n} button events')
    elif args.mode == 'buzzer':
        ser.write(frame(0x02, struct.pack('<HHHH', args.freq, args.on, args.off, args.cycles)))
        print(f'sent beep: {args.cycles} x ({args.on} ms on, {args.off} ms off), {args.freq} Hz')
    elif args.mode == 'gamepad':
        print(f'press gamepad buttons / move sticks now ({args.secs:g} s)...')

        def show(t, f, d):
            if f == 0x08 and len(d) == 7:
                b, hat, lx, ly, rx, ry = struct.unpack('<HBbbbb', d)
                print(f'  {t:5.1f} s  buttons 0x{b:04x} hat {hat} '
                      f'L ({lx:+4d},{ly:+4d}) R ({rx:+4d},{ry:+4d})')
            elif f == 0x23:
                print(f'  {t:5.1f} s  raw HID {d[1:1 + d[0]].hex(" ")}')
        n = listen(ser, args.secs, {0x08, 0x23}, show)
        print(f'{n} gamepad changes')
    elif args.mode == 'sbus':
        n = listen(ser, args.secs, {0x09}, lambda t, f, d: print(
            f'  {t:5.1f} s  ch1-4 {struct.unpack("<4h", d[:8])} loss {d[34]} failsafe {d[35]}'))
        print(f'{n} SBUS frames' + ('' if n else ' (no receiver connected, or no signal)'))
    elif args.mode == 'pwm-servo':
        if not 500 <= args.pulse <= 2500:
            sys.exit('pulse must be 500..2500 us')
        payload = bytes([0x03]) + struct.pack('<H', args.time) + bytes([args.id])
        payload += struct.pack('<H', args.pulse)
        ser.write(frame(0x04, payload))
        print(f'sent PWM servo {args.id} -> {args.pulse} us in {args.time} ms')
    ser.close()


if __name__ == '__main__':
    main()
