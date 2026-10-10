#!/usr/bin/env python3
# 한글: 자체 펌웨어(rrc_m4)에 진단 요청(DIAG 0x06)을 보내 상태(0x20)와 진단(0x24: 태스크별 최소 여유 스택, IMU 샘플/오류,
#       거부된 이동 명령 수)을 출력한다. 모터는 움직이지 않는다. base_node가 꺼져 있어야 한다(같은 시리얼 포트).
"""Request and print the rrc_m4 status (0x20) and diagnostics (0x24). Does not move anything.

Usage: python3 tools/stm32_diagnostics/rrc_m4_diag.py
Needs the rrc_m4 firmware with the 0x24 frame (2026-10-10) and base_node NOT running.
Free stack is the FreeRTOS high-water mark: the least free stack the task ever had, in words (4 bytes).
"""
import os
import struct
import sys
import time

import serial

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rrc_m4_raw_pwm_test import crc8, frame, FUNC_DIAG, PORT  # noqa: E402

TASKS = {0: 'control', 1: 'imu', 2: 'comm_rx', 3: 'comm_tx', 4: 'ui', 5: 'lcd', 6: 'sbus', 7: 'usb',
         8: 'bt', 9: 'supervisor', 10: 'uros', 11: 'host_tx', 12: 'idle'}
STACK_WORDS = {'control': 512, 'imu': 512, 'comm_rx': 768, 'comm_tx': 384, 'ui': 768, 'lcd': 640,
               'sbus': 384, 'usb': 640, 'bt': 384, 'supervisor': 384, 'uros': 3072, 'host_tx': 384}
DIAG_REQUEST_STATUS = 0x06


def frames(buf):
    i = 0
    while i + 4 <= len(buf):
        if buf[i] == 0xAA and buf[i + 1] == 0x55:
            f, n = buf[i + 2], buf[i + 3]
            if i + 5 + n > len(buf):
                break
            d = buf[i + 4:i + 4 + n]
            if crc8(bytes([f, n]) + d) == buf[i + 4 + n]:
                yield f, d
                i += 5 + n
                continue
        i += 1


def main():
    ser = serial.Serial(PORT, 1_000_000, timeout=0.05)
    ser.reset_input_buffer()
    ser.write(frame(FUNC_DIAG, bytes([DIAG_REQUEST_STATUS])))
    buf, t0 = b'', time.time()
    while time.time() - t0 < 1.0:
        buf += ser.read(4096)
    ser.close()
    status = diag = None
    for f, d in frames(buf):
        if f == 0x20 and len(d) == 16:
            status = d
        elif f == 0x24:
            diag = d
    if status:
        up, rc = struct.unpack('<II', status[8:16])
        print(f'status: flags 0x{status[0]:02x} stop_reason {status[1]} imu_kind {status[2]} '
              f'fault {list(status[4:8])} uptime {up / 1000:.1f} s reset_cause 0x{rc:x}')
    if not diag:
        sys.exit('no 0x24 diag frame (firmware older than 2026-10-10, or base_node holds the port?)')
    n = diag[0]
    print('task         min free / stack (words)')
    for k in range(n):
        tid = diag[1 + 3 * k]
        free = diag[2 + 3 * k] | (diag[3 + 3 * k] << 8)
        name = TASKS.get(tid, f'#{tid}')
        size = STACK_WORDS.get(name)
        warn = '  <-- under 20 %' if size and free < 0.2 * size else ''
        print(f'  {name:11s} {free:5d} / {size if size else "?":>5}{warn}')
    samples, errors, rejected = struct.unpack('<III', diag[1 + 3 * n:1 + 3 * n + 12])
    print(f'imu samples {samples}, imu errors {errors}, rejected motion commands {rejected}')


if __name__ == '__main__':
    main()
