#!/usr/bin/env python3
# 한글: 자체 펌웨어(rrc_m4, MOTOR_ENABLE=ON) 바퀴 하나씩 개방 루프 PWM 시험. 바퀴가 실제로 돈다 — 바퀴를 띄우고 사람이 전원 스위치 옆에.
#       각 모터에 +PWM, -PWM을 SECS초씩 걸고(0.1초마다 재전송, 펌웨어는 0.5초 끊기면 자동 0) 엔코더 카운터 변화와 rps를 출력한다.
#       결과로 PINMAP의 모터 PWM 핀 배정(M2~M4 추정)과 엔코더 부호(MOTOR_ENCODER_SIGN)를 확정한다.
"""Open-loop per-wheel PWM test for the rrc_m4 firmware (DIAG RAW_PWM). THE WHEELS SPIN.

Usage: python3 tools/stm32_diagnostics/rrc_m4_raw_pwm_test.py [--motors 0 1 2 3] [--pulse 400] [--secs 1.0]
Needs: rrc_m4 built with MOTOR_ENABLE=ON, wheels lifted, motor switch ON, a person at the power switch,
base_node NOT running (this script owns the serial port).
For each motor index (firmware order 0..3 = board ports 1..4): +pulse for SECS, pause, -pulse for SECS, pause.
Prints the encoder counter change of all four channels (to see which encoder belongs to the driven wheel)
and the peak rps. Watch which physical wheel turns and in which direction.
E-stop is cleared only during each step and set again right after it (the PID must not act on a
coasting wheel), and the board is left e-stopped on exit (also on Ctrl+C). Needs the firmware with the
e-stop hold (2026-10-10); older builds keep running the PID while e-stopped.
"""
import argparse
import struct
import threading
import time

import serial

PORT = '/dev/serial/by-id/usb-1a86_USB_Single_Serial_596F003889-if00'
FUNC_DIAG, DIAG_RAW_PWM, FUNC_WHEEL, FUNC_STATUS = 0x22, 0x05, 0x21, 0x20
DIAG_CLEAR_ESTOP, DIAG_ESTOP = 0x01, 0x02


def crc8(data):
    c = 0
    for b in data:
        c ^= b
        for _ in range(8):
            c = (c >> 1) ^ 0x8C if c & 1 else c >> 1
    return c


def frame(func, data):
    body = bytes([func, len(data)]) + data
    return b'\xAA\x55' + body + bytes([crc8(body)])


def raw_pwm(motor, pulse):
    return frame(FUNC_DIAG, bytes([DIAG_RAW_PWM, motor]) + struct.pack('<h', pulse))


class Reader(threading.Thread):
    """Parses WHEEL (rps[4] f32, counter[4] i32) and STATUS frames in the background."""

    def __init__(self, ser):
        super().__init__(daemon=True)
        self.ser, self.stop = ser, False
        self.rps, self.counter, self.status = [0.0] * 4, [0] * 4, None
        self.peak = [0.0] * 4

    def run(self):
        buf = b''
        while not self.stop:
            buf += self.ser.read(1024)
            while True:
                i = buf.find(b'\xAA\x55')
                if i < 0 or len(buf) < i + 4:
                    buf = buf[max(i, 0):] if i >= 0 else b''
                    break
                f, n = buf[i + 2], buf[i + 3]
                if len(buf) < i + 5 + n:
                    buf = buf[i:]
                    break
                d = buf[i + 4:i + 4 + n]
                if crc8(bytes([f, n]) + d) != buf[i + 4 + n]:
                    buf = buf[i + 1:]
                    continue
                if f == FUNC_WHEEL and n == 32:
                    self.rps = list(struct.unpack('<4f', d[:16]))
                    self.counter = list(struct.unpack('<4i', d[16:32]))
                    self.peak = [max(p, abs(r)) for p, r in zip(self.peak, self.rps)]
                elif f == FUNC_STATUS and n == 16:
                    self.status = d
                buf = buf[i + 5 + n:]


def drive(ser, rd, motor, pulse, secs):
    # E-stop is held between steps so the speed PID never acts on a coasting wheel (2026-10-10: with a
    # wrong encoder sign it drove the right front wheel to full PWM after a step). Clear it only for the step.
    # 한글: 단계 사이에는 e-stop으로 PID를 막고, 단계 동안만 해제한다.
    ser.write(frame(FUNC_DIAG, bytes([DIAG_CLEAR_ESTOP])))
    time.sleep(0.05)
    c0 = list(rd.counter)
    rd.peak = [0.0] * 4
    t0 = time.time()
    while time.time() - t0 < secs:
        ser.write(raw_pwm(motor, pulse))
        time.sleep(0.1)
    ser.write(raw_pwm(motor, 0))
    ser.write(frame(FUNC_DIAG, bytes([DIAG_ESTOP])))
    time.sleep(0.8)  # coast down with the PID held off / PID 정지 상태로 관성 정지
    d = [b - a for a, b in zip(c0, rd.counter)]
    st = rd.status
    faults = list(st[4:8]) if st else '?'
    print(f'  motor {motor} pulse {pulse:+5d}: counter delta {d}  peak |rps| '
          f'{[round(p, 2) for p in rd.peak]}  fault {faults}')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--motors', type=int, nargs='+', default=[0, 1, 2, 3])
    ap.add_argument('--pulse', type=int, default=400, help='0..1000 (PWM dead zone ~250)')
    ap.add_argument('--secs', type=float, default=1.0)
    ap.add_argument('--gap', type=float, default=2.0, help='pause between steps (s)')
    args = ap.parse_args()
    if not 0 < args.pulse <= 600:
        raise SystemExit('pulse must be 1..600 for this test')
    ser = serial.Serial(PORT, 1_000_000, timeout=0.05)
    rd = Reader(ser)
    rd.start()
    time.sleep(0.5)
    if rd.status is None:
        raise SystemExit('no STATUS frames: rrc_m4 firmware not running?')
    try:
        for m in args.motors:
            for sign in (1, -1):
                print(f'>>> motor {m} {"+" if sign > 0 else "-"}{args.pulse} for {args.secs} s')
                drive(ser, rd, m, sign * args.pulse, args.secs)
                time.sleep(args.gap)
    finally:
        ser.write(frame(FUNC_DIAG, bytes([DIAG_ESTOP])))  # leave the board e-stopped / e-stop 상태로 끝냄
        for m in range(4):
            ser.write(raw_pwm(m, 0))
        time.sleep(0.2)
        rd.stop = True
        ser.close()
        print('all motors 0')


if __name__ == '__main__':
    main()
