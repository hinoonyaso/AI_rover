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
  gripper-goto --pulse 200 [--time 2000]       move the gripper (ID 10) to a position (125..693 only)
  grasp-cube [--step 12] [--width-mm 30]        THE GRIPPER CLOSES on an object you hold between the open jaws:
                                               small steps until the reading stops following (contact), squeeze, reopen
  grasp-levels [--levels 8,14,20] [--swing]    contact, then squeeze each level 5 s (1/2/3 beeps);
                                               --swing: also swing joint 1 by +-10 deg at the last level
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


TEMP_LIMIT_C = 60  # stop and cool down above this (2026-10-11: gripper 53 C / joint 1 61 C after repeated squeezes + swings)


def servo_temp(ser, sid):
    """FUNC5 temperature read [09, id] -> [id, 09, success, deg C]. None on failure. 한글: 서보 온도."""
    for _ in range(3):
        ser.reset_input_buffer()
        ser.write(frame(0x05, bytes([0x09, sid])))
        buf, t0 = b'', time.time()
        while time.time() - t0 < 0.4:
            buf += ser.read(256)
            for f, d in frames(buf):
                if f == 0x05 and len(d) >= 4 and d[0] == sid and d[1] == 0x09 and d[2] == 0:
                    return d[3]
    return None


def cool_down(ser, ids=(10, 1), limit=TEMP_LIMIT_C - 10):
    """Wait (up to 3 min) until every listed servo is below `limit` deg C."""
    t0 = time.time()
    while time.time() - t0 < 180:
        temps = {i: servo_temp(ser, i) for i in ids}
        if all(v is None or v < limit for v in temps.values()):
            return temps
        print(f'  waiting to cool down: {temps}')
        time.sleep(10)
    return temps


def check_temps(ser, ids=(10, 1), label=''):
    temps = {i: servo_temp(ser, i) for i in ids}
    print(f'  servo temperatures {label}: ' + ', '.join(f'ID {i} {v} C' for i, v in temps.items()))
    if any(v is not None and v >= TEMP_LIMIT_C for v in temps.values()):
        print(f'  >= {TEMP_LIMIT_C} C: cooling down before going on')
        cool_down(ser, ids)
    return temps


def move_bus_servo(ser, sid, pulse, ms):
    payload = bytes([0x01]) + struct.pack('<H', ms) + bytes([1, sid]) + struct.pack('<H', pulse)
    ser.write(frame(0x05, payload))
    time.sleep(ms / 1000 + 0.5)


def find_contact(ser, args):
    """Close from the open position until the jaws are blocked; returns (start, contact). 한글: 접촉 눈금 찾기."""
    sid, step, closed_end, dead_band = 10, min(max(args.step, 6), 16), 693, 8
    start = read_bus_servo(ser, sid)
    if start is None:
        sys.exit('gripper: no position reading')
    if start > 450:
        sys.exit(f'gripper is at {start}; open it first (gripper-goto --pulse 200), object between the jaws')
    print(f'start {start}; closing in steps of {step} pulses ({step * 0.24:.1f} deg); blocked = lag > {dead_band} and '
          f'a repeat of the command does not move it')
    target, now, contact = start, start, None
    for i in range(80):
        target = now + step
        if target > min(args.max_pulse, closed_end - 6):
            print(f'  reached the limit {args.max_pulse} without contact')
            break
        move_bus_servo(ser, sid, target, 350)
        now = read_bus_servo(ser, sid)
        if now is None:
            sys.exit('lost the reading; stopping')
        lag = target - now
        if args.verbose:
            print(f'  step {i + 1}: commanded {target}, read {now} (lag {lag})')
        if lag > dead_band:  # candidate: send the same target again and see if it gives
            move_bus_servo(ser, sid, target, 350)
            again = read_bus_servo(ser, sid)
            if again is not None and abs(again - now) <= 1:
                contact = again
                print(f'  step {i + 1}: commanded {target}, read {now} then {again} -> BLOCKED at {contact} '
                      f'(lag {target - again})')
                break
            now = again if again is not None else now
    else:
        print('  no contact within 80 steps')
    if contact is None:
        move_bus_servo(ser, sid, start, 2000)
        sys.exit('no contact found; reopened')
    return start, contact


def grasp_cube(ser, args):
    """Find the contact, squeeze a little, hold 2 s, reopen. Prints pulses/mm from the closed end 693."""
    closed_end = 693
    start, contact = find_contact(ser, args)
    squeeze = contact + 4
    move_bus_servo(ser, 10, squeeze, 500)
    time.sleep(2.0)
    held = read_bus_servo(ser, 10)
    print(f'squeeze target {squeeze} (contact + 4), read after 2 s: {held}')
    per_mm = (closed_end - contact) / args.width_mm
    print(f'RESULT contact {contact} for {args.width_mm:g} mm -> {per_mm:.2f} pulses/mm; '
          f'closed end {closed_end} = 0 mm; open end 125 = about {(closed_end - 125) / per_mm:.0f} mm '
          f'(linear estimate)')
    print('opening again (take the object)...')
    move_bus_servo(ser, 10, start, 2000)
    print(f'back at {read_bus_servo(ser, 10)}')


def beep(ser, n):
    """n short beeps as an audible cue (FUNC2). 한글: 사용자에게 단계를 알리는 부저."""
    ser.write(frame(0x02, struct.pack('<HHHH', 2000, 150, 150, n)))


def grasp_levels(ser, args):
    """Contact, then squeeze +8, +14, +20 pulses for 5 s each (1/2/3 beeps at the start of each level) while the user
    pulls on the object; with --swing the same squeeze is also held while joint 1 swings +-40 pulses (about 10 deg)."""
    check_temps(ser, label='before')
    start, contact = find_contact(ser, args)
    levels = [int(x) for x in args.levels.split(',')]
    print(f'contact {contact}; levels {levels}; each held {args.hold_s:g} s (beeps = level number)')
    for k, extra in enumerate(levels, 1):
        if not args.no_beep:
            beep(ser, k)
            time.sleep(0.6 + 0.3 * k)
        move_bus_servo(ser, 10, contact + extra, 400)
        held = read_bus_servo(ser, 10)
        print(f'  level {k}: +{extra} -> target {contact + extra}, read {held}')
        if args.swing and k == len(levels):
            # long cue: let go of the object now (keep a hand under it); the swing starts 4 s later
            ser.write(frame(0x02, struct.pack('<HHHH', 1500, 900, 100, 1)))
            time.sleep(4.0)
            swing_joint1(ser)
        else:
            time.sleep(args.hold_s)
    print('opening again (take the object)...')
    move_bus_servo(ser, 10, start, 2000)
    print(f'back at {read_bus_servo(ser, 10)}')
    check_temps(ser, label='after')


def swing_joint1(ser):
    """Joint 1 (base yaw) +-40 pulses (about 10 deg) twice at 0.8 s per leg while the gripper keeps squeezing."""
    p0 = read_bus_servo(ser, 1)
    if p0 is None:
        print('  joint 1: no reading, no swing')
        return
    print(f'  swinging joint 1 around {p0}: +40, -40 twice')
    for target in (p0 + 40, p0 - 40, p0 + 40, p0 - 40, p0):
        move_bus_servo(ser, 1, target, 800)
    print(f'  joint 1 back at {read_bus_servo(ser, 1)}; gripper still at {read_bus_servo(ser, 10)}')


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
    modes = ['buttons', 'buzzer', 'gamepad', 'sbus', 'pwm-servo', 'bus-servo', 'bus-torque', 'gripper-range',
             'gripper-goto', 'grasp-cube', 'grasp-levels']
    ap.add_argument('mode', choices=modes)
    ap.add_argument('--secs', type=float, default=20.0)
    ap.add_argument('--on', type=int, default=100)
    ap.add_argument('--off', type=int, default=100)
    ap.add_argument('--cycles', type=int, default=3)
    ap.add_argument('--freq', type=int, default=2000)
    ap.add_argument('--id', type=int, default=1)
    ap.add_argument('--pulse', type=int, default=1500)
    ap.add_argument('--time', type=int, default=500)
    ap.add_argument('--step', type=int, default=40,
                    help='gripper-range: pulses per step (<= 50); grasp-cube: 6..16 (use 12)')
    ap.add_argument('--verbose', action='store_true', help='grasp-cube: print every step')
    ap.add_argument('--max-pulse', type=int, default=687, help='grasp-cube: never close beyond this pulse')
    ap.add_argument('--levels', default='8,14,20', help='grasp-levels: squeeze pulses beyond contact, comma separated')
    ap.add_argument('--hold-s', type=float, default=5.0, help='grasp-levels: seconds per level')
    ap.add_argument('--no-beep', action='store_true', help='grasp-levels: silent (no buzzer cues), to hear the servo itself')
    ap.add_argument('--swing', action='store_true', help='grasp-levels: swing joint 1 +-10 deg at the last level')
    ap.add_argument('--width-mm', type=float, default=30.0, help='grasp-cube: width of the object between the jaws')
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
    elif args.mode == 'gripper-goto':
        if not 125 <= args.pulse <= 693:
            sys.exit('gripper-goto: pulse must be 125..693 (measured range 2026-10-11)')
        before = read_bus_servo(ser, 10)
        move_bus_servo(ser, 10, args.pulse, max(args.time, 1500))
        print(f'gripper {before} -> {read_bus_servo(ser, 10)} (asked {args.pulse})')
    elif args.mode == 'grasp-cube':
        grasp_cube(ser, args)
    elif args.mode == 'grasp-levels':
        grasp_levels(ser, args)
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
