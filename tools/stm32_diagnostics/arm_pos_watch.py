#!/usr/bin/env python3
# 한글: 버스 서보 위치(0x05)를 일정 시간 샘플링해 사람이 팔을 손으로 움직일 때 값이 변하는지 본다. base_node가 포트를 열고 있으면 안 된다.
"""Sample bus servo positions (sub 0x05) for N seconds. Usage: arm_pos_watch.py [seconds]"""
import sys
import time

from rrc_raw import FrameReader, build_frame, open_main_port

IDS = [1, 2, 3, 4, 5, 10]


def main():
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 15
    ser = open_main_port()
    ser.dtr = True
    ser.rts = False
    rd = FrameReader(ser)
    t0 = time.time()
    while time.time() - t0 < dur:
        pos = {}
        for sid in IDS:
            ser.write(build_frame(0x05, bytes([0x05, sid])))
            t1 = time.time()
            while time.time() - t1 < 0.15 and sid not in pos:
                for func, data in rd.poll():
                    if func == 0x05 and len(data) >= 5 and data[1] == 0x05 and data[2] == 0:
                        pos[data[0]] = int.from_bytes(data[3:5], "little", signed=True)
        print("%5.1fs %s" % (time.time() - t0, pos), flush=True)
    ser.close()


if __name__ == "__main__":
    main()
