#!/usr/bin/env python3
# 한글: 버스 서보 토크 상태(0x0D 읽기)를 확인하고 해제(0x0C)/설정(0x0B) 명령이 먹는지 시험한다. base_node가 포트를 열고 있으면 안 된다.
"""Probe bus servo torque: read state (sub 0x0D), optionally send OFF (0x0C) / ON (0x0B), read again.

Usage: python3 arm_torque_probe.py off|on|read   (base_node must NOT be running)
Official board.cpp: enable ? 0x0B : 0x0C ; read torque state = 0x0D -> reply [id, 0x0D, ok, state],
state 1 = limp (unloaded), 0 = loaded (observed 2026-10-05, checklist 14).
"""
import sys
import time

from rrc_raw import FrameReader, build_frame, open_main_port

IDS = [1, 2, 3, 4, 5, 10]


def read_state(ser, rd, sid):
    ser.write(build_frame(0x05, bytes([0x0D, sid])))
    t0 = time.time()
    while time.time() - t0 < 0.3:
        for func, data in rd.poll():
            if func == 0x05 and len(data) >= 4 and data[0] == sid and data[1] == 0x0D:
                return data[3] if data[2] == 0 else None
    return None


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "read"
    ser = open_main_port()
    ser.dtr = True
    ser.rts = False
    rd = FrameReader(ser)
    time.sleep(0.3)
    print("before:", {i: read_state(ser, rd, i) for i in IDS})
    if mode in ("off", "on"):
        sub = 0x0C if mode == "off" else 0x0B
        for i in IDS:
            ser.write(build_frame(0x05, bytes([sub, i])))
            time.sleep(0.05)
        time.sleep(0.3)
        print("after :", {i: read_state(ser, rd, i) for i in IDS})
    ser.close()


if __name__ == "__main__":
    main()
