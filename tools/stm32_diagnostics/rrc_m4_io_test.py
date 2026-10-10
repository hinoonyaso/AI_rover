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
  gripper-range [--step 40]                    THE GRIPPER OPENS/CLOSES FULLY (keep it empty, hands off):
                                               --step pulses at a time each way until it stops following (end stop)
  bus-torque --id 5 [--hold 4]                 THE JOINT GOES LIMP for --hold s (support it): release torque, read,
                                               move to the current position, load torque, read again (FUNC5 0x0B/0x0C)
  bus-servo --id 1 --delta 20 [--time 1000]    THE ARM MOVES: read the position, move by +delta pulses
                                               (0.24 deg each), read back, move back, read back (FUNC5)
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


def read_bus_servo(ser, sid, tries=4):
    """FUNC5 read-position request [05, id] -> response [id, 05, success, pulse i16 LE]. None on failure."""
    for _ in range(tries):
        ser.reset_input_buffer()
        ser.write(frame(0x05, bytes([0x05, sid])))
        buf, t0 = b'', time.time()
        while time.time() - t0 < 0.4:
            buf += ser.read(512)
            for f, d in frames(buf):
                if f == 0x05 and len(d) == 5 and d[1] == 0x05 and d[0] == sid and d[2] == 0:
                    return struct.unpack('<h', d[3:5])[0]
    return None


def bus_servo_test(ser, args):
    if not 1 <= args.id <= 5 and args.id != 10:
        sys.exit('servo id must be 1..5 (arm) or 10 (gripper)')
    if abs(args.delta) > 40 or not 200 <= args.time <= 5000:
        sys.exit('|delta| <= 40 pulses (about 10 deg), time 200..5000 ms')
    p0 = read_bus_servo(ser, args.id)
    if p0 is None:
        sys.exit(f'servo {args.id}: no position reading (bus servo direction pins? servo powered?)')
    target = p0 + args.delta
    if not 100 <= target <= 900:
        sys.exit(f'target {target} outside the safe 100..900 pulse range')
    print(f'servo {args.id}: position {p0} -> moving to {target} in {args.time} ms')

    def move(pulse):
        payload = bytes([0x01]) + struct.pack('<H', args.time) + bytes([1, args.id])
        payload += struct.pack('<H', pulse)
        ser.write(frame(0x05, payload))
        time.sleep(args.time / 1000 + 0.6)
    move(target)
    p1 = read_bus_servo(ser, args.id)
    print(f'  after move: {p1} (moved {None if p1 is None else p1 - p0:+d})')
    print(f'servo {args.id}: moving back to {p0}')
    move(p0)
    p2 = read_bus_servo(ser, args.id)
    print(f'  after return: {p2} (off the start by {None if p2 is None else p2 - p0:+d})')


def move_bus_servo(ser, sid, pulse, ms):
    payload = bytes([0x01]) + struct.pack('<H', ms) + bytes([1, sid]) + struct.pack('<H', pulse)
    ser.write(frame(0x05, payload))
    time.sleep(ms / 1000 + 0.5)


def gripper_range(ser, args):
    """Walk the gripper (ID 10) away from its start in one direction in small steps until it stops following
    (end stop or an object), then do the other direction, then return. 한글: 한계(막히는 지점)를 단계적으로 찾는다."""
    sid, step = 10, min(max(args.step, 10), 50)
    start = read_bus_servo(ser, sid)
    if start is None:
        sys.exit('gripper: no position reading')
    print(f'gripper start {start}; steps of {step} pulses ({step * 0.24:.0f} deg), safe range 100..900')
    limits = {}
    for name, direction in (('close (+)', 1), ('open (-)', -1)):
        pos = start
        for i in range(25):
            target = pos + direction * step
            if not 100 <= target <= 900:
                limits[name] = (pos, 'safety clamp reached, not a mechanical limit')
                break
            move_bus_servo(ser, sid, target, 1000)
            now = read_bus_servo(ser, sid)
            if now is None:
                sys.exit(f'lost the reading after step {i + 1}; stopping where it is')
            moved = (now - pos) * direction
            print(f'  {name} step {i + 1}: commanded {target}, read {now} (moved {moved:+d} of {step})')
            if moved < step * 0.5:  # not following: end stop or an object
                limits[name] = (now, 'stopped following')
                move_bus_servo(ser, sid, now - direction * 8, 600)  # relax the push
                break
            pos = now
        else:
            limits[name] = (pos, 'no stop within 25 steps')
        print(f'  -> {name} limit: {limits[name][0]} ({limits[name][1]})')
        move_bus_servo(ser, sid, start, 1500)
        back = read_bus_servo(ser, sid)
        print(f'  back at start: {back} (start was {start})')
    print('RESULT', {k: v[0] for k, v in limits.items()}, 'start', start)


def bus_torque_test(ser, args):
    """Release (0x0B) -> limp for --hold s -> move to the CURRENT position (overwrites the stored target, otherwise
    the servo jumps to its old target when loaded, 2026-10-05) -> load (0x0C). 한글: 해제 → 현재 위치로 이동 → 걸기."""
    if not 1 <= args.id <= 5 and args.id != 10:
        sys.exit('servo id must be 1..5 (arm) or 10 (gripper)')
    p0 = read_bus_servo(ser, args.id)
    if p0 is None:
        sys.exit(f'servo {args.id}: no position reading')
    print(f'servo {args.id}: holding at {p0}; releasing torque for {args.hold:g} s (support the joint)...')
    ser.write(frame(0x05, bytes([0x0B, args.id])))
    series, t0 = [], time.time()
    while time.time() - t0 < args.hold:  # sample while limp: a joint moved by hand must show up here
        series.append(read_bus_servo(ser, args.id, tries=1))
        time.sleep(0.3)
    p2 = read_bus_servo(ser, args.id)
    print(f'  while limp ({len(series)} reads): {series}')
    ok = [x for x in series if x is not None]
    print(f'  last: {p2} (min {min(ok) if ok else None}, max {max(ok) if ok else None})')
    if p2 is None or not 100 <= p2 <= 900:
        sys.exit('no safe reading while limp; leaving the servo limp -- hold it and re-run')
    payload = bytes([0x01]) + struct.pack('<H', 500) + bytes([1, args.id]) + struct.pack('<H', p2)
    ser.write(frame(0x05, payload))  # pin the target at the current position before loading
    time.sleep(0.9)
    ser.write(frame(0x05, bytes([0x0C, args.id])))
    print(f'servo {args.id}: torque loaded at {p2}')
    time.sleep(1.5)
    p3 = read_bus_servo(ser, args.id)
    print(f'  after loading: {p3} (held {None if p3 is None else p3 - p2:+d} pulses from where it was loaded)')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    modes = ['buttons', 'buzzer', 'gamepad', 'sbus', 'pwm-servo', 'bus-servo', 'bus-torque', 'gripper-range']
    ap.add_argument('mode', choices=modes)
    ap.add_argument('--secs', type=float, default=20.0)
    ap.add_argument('--on', type=int, default=100)
    ap.add_argument('--off', type=int, default=100)
    ap.add_argument('--cycles', type=int, default=3)
    ap.add_argument('--freq', type=int, default=2000)
    ap.add_argument('--id', type=int, default=1)
    ap.add_argument('--pulse', type=int, default=1500)
    ap.add_argument('--time', type=int, default=500)
    ap.add_argument('--step', type=int, default=40, help='gripper-range: pulses per step (<= 50)')
    ap.add_argument('--hold', type=float, default=4.0, help='bus-torque: seconds the joint stays limp')
    ap.add_argument('--delta', type=int, default=20, help='bus-servo: pulses (0.24 deg each), |delta| <= 40')
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
    elif args.mode == 'bus-servo':
        bus_servo_test(ser, args)
    elif args.mode == 'bus-torque':
        bus_torque_test(ser, args)
    elif args.mode == 'gripper-range':
        gripper_range(ser, args)
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
