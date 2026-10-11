#!/usr/bin/env python3
# 한글: E3 안전 시험(펌웨어 쪽): 명령 timeout 정지, 비정상(NaN) 명령 거부 카운트, e-stop 래치 중 명령 무시. 바퀴가 돈다(바퀴를 띄울 것).
#       base_node가 꺼져 있어야 한다(같은 포트). 호스트 강제 종료(SIGKILL) 시험은 이 스크립트가 아니라 별도(README의 E3 절).
"""E3 firmware-side safety checks. THE WHEELS SPIN (lift them, hand at the motor switch).

Usage: python3 tools/stm32_diagnostics/rrc_m4_e3_test.py [--rps 0.5]
  A  command timeout   drive 2 s, then send nothing (no stop frame): wheels must stop within --limit s (CMD_TIMEOUT_MS 1000)
  B  NaN command       a NaN wheel speed must be rejected and counted (diag rejected_cmds +1), wheels stay still
  C  e-stop latch      e-stop while moving stops the wheels; motion commands during the e-stop do not move them;
                       after clearing it motion works again
Aborts when the battery is below 10.0 V. Always ends with zero speed + e-stop.
"""
import argparse
import os
import struct
import sys
import threading
import time

import serial

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rrc_m4_raw_pwm_test import DIAG_CLEAR_ESTOP, DIAG_ESTOP, FUNC_DIAG, PORT, crc8, frame  # noqa: E402

DIAG_REQUEST_STATUS = 0x06


class Log(threading.Thread):
    def __init__(self, ser):
        super().__init__(daemon=True)
        self.ser, self.stop = ser, False
        self.rps, self.rps_t = [0.0] * 4, 0.0
        self.batt_mv, self.status, self.rejected = None, None, None

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
                if f == 0x21 and n == 32:
                    self.rps, self.rps_t = list(struct.unpack('<4f', d[:16])), time.time()
                elif f == 0x00 and n == 3 and d[0] == 4:
                    self.batt_mv = struct.unpack('<H', d[1:3])[0]
                elif f == 0x20 and n == 16:
                    self.status = d
                elif f == 0x24 and n >= 13:
                    k = d[0]
                    self.rejected = struct.unpack('<I', d[1 + 3 * k + 8:1 + 3 * k + 12])[0]
                buf = buf[i + 5 + n:]


def drive_cmd(rps):
    return frame(0x03, bytes([0x01, 4]) + b''.join(bytes([m]) + struct.pack('<f', rps) for m in range(4)))


def nan_cmd():
    return frame(0x03, bytes([0x01, 1, 0]) + struct.pack('<f', float('nan')))


def peak(lg):
    return max(abs(r) for r in lg.rps)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--rps', type=float, default=0.5)
    ap.add_argument('--limit', type=float, default=1.5)
    args = ap.parse_args()
    if not 0 < args.rps <= 1.0:
        sys.exit('0 < rps <= 1.0 for this test')
    ser = serial.Serial(PORT, 1_000_000, timeout=0.05)
    lg = Log(ser)
    lg.start()
    time.sleep(1.0)
    if lg.status is None:
        sys.exit('no STATUS frames: rrc_m4 not running or base_node holds the port')
    if lg.batt_mv is not None and lg.batt_mv < 10000:
        sys.exit(f'battery {lg.batt_mv} mV < 10 V: charge first')
    print(f'battery {lg.batt_mv} mV')
    ok = {}
    try:
        # A: command timeout
        ser.write(frame(FUNC_DIAG, bytes([DIAG_CLEAR_ESTOP])))
        time.sleep(0.1)
        t0 = time.time()
        while time.time() - t0 < 2.0:
            ser.write(drive_cmd(args.rps))
            time.sleep(0.1)
        run_peak = peak(lg)
        t_last = time.time()
        stopped = None
        while time.time() - t_last < 4.0:
            if peak(lg) < 0.05 and stopped is None:
                stopped = time.time() - t_last
            time.sleep(0.02)
        print(f'A  timeout: running peak {run_peak:.2f} rps; after the last command stopped in '
              f'{"never" if stopped is None else f"{stopped:.2f} s"} (limit {args.limit} s)')
        ok['A'] = run_peak > 0.2 and stopped is not None and stopped <= args.limit

        # B: NaN rejection
        ser.write(frame(FUNC_DIAG, bytes([DIAG_REQUEST_STATUS])))
        time.sleep(0.5)
        r0 = lg.rejected
        for _ in range(3):
            ser.write(nan_cmd())
            time.sleep(0.1)
        ser.write(frame(FUNC_DIAG, bytes([DIAG_REQUEST_STATUS])))
        time.sleep(0.5)
        r1 = lg.rejected
        print(f'B  NaN: rejected_cmds {r0} -> {r1}, wheel peak now {peak(lg):.3f} rps')
        ok['B'] = r0 is not None and r1 is not None and r1 >= r0 + 3 and peak(lg) < 0.05

        # C: e-stop latch
        ser.write(frame(FUNC_DIAG, bytes([DIAG_CLEAR_ESTOP])))
        t0 = time.time()
        while time.time() - t0 < 1.5:
            ser.write(drive_cmd(args.rps))
            time.sleep(0.1)
        moving = peak(lg)
        ser.write(frame(FUNC_DIAG, bytes([DIAG_ESTOP])))
        t_e = time.time()
        e_stop_t = None
        while time.time() - t_e < 2.0:
            ser.write(drive_cmd(args.rps))  # keep commanding: must be ignored
            if peak(lg) < 0.05 and e_stop_t is None:
                e_stop_t = time.time() - t_e
            time.sleep(0.05)
        still = peak(lg)
        print(f'C  e-stop: moving {moving:.2f} rps; stopped in '
              f'{"never" if e_stop_t is None else f"{e_stop_t:.2f} s"}; still {still:.3f} rps at the end '
              f'with commands still arriving')
        ser.write(frame(FUNC_DIAG, bytes([DIAG_CLEAR_ESTOP])))
        t0 = time.time()
        again = 0.0
        while time.time() - t0 < 1.5:
            ser.write(drive_cmd(args.rps))
            again = max(again, peak(lg))
            time.sleep(0.1)
        print(f'C  after clearing the e-stop: peak {again:.2f} rps')
        ok['C'] = moving > 0.2 and e_stop_t is not None and e_stop_t < 1.0 and still < 0.05 and again > 0.2
    finally:
        ser.write(drive_cmd(0.0))
        ser.write(frame(FUNC_DIAG, bytes([DIAG_ESTOP])))
        time.sleep(0.8)
        lg.stop = True
        ser.close()
    print('RESULT', {k: 'PASS' if v else 'FAIL' for k, v in ok.items()})


if __name__ == '__main__':
    main()
