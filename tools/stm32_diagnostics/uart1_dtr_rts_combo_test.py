#!/usr/bin/env python3
"""UART1(ISP 포트, /dev/ttyACM1)에서 DTR/RTS 4가지 조합을 각각 0.5초씩 유지하며
STM32가 리셋되는지 최종 확인한다.

이전 시험(v1/v2/v3)은 DTR 단독 펄스만 봤다. Hiwonder ISP 회로가 DTR/RTS를 동시에 조합해서
쓰는 구조일 가능성이 있어, (DTR,RTS) = (0,0)(0,1)(1,0)(1,1) 네 조합을 순서대로 걸어보고
각 상태에서 메인 포트(UART2)의 IMU 프레임 gap을 실시간으로 관찰한다.
UART1에는 여전히 어떤 바이트도 쓰지 않는다 (부트로더 프로토콜 회피).
0 = not asserted(False), 1 = asserted(True) — pyserial의 .dtr/.rts 불리언 그대로.
"""

import argparse
import threading
import time

import serial

MAIN_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_596F003889-if00"  # UART2, 알려진 IMU 포트
ISP_PORT = "/dev/ttyACM1"  # UART1
MAIN_BAUD = 1_000_000
ISP_BAUD = 115200
HEADER = b"\xAA\x55"

COMBOS = [(False, False), (False, True), (True, False), (True, True)]


class FrameReader(threading.Thread):
    def __init__(self, ser: serial.Serial):
        super().__init__(daemon=True)
        self.ser = ser
        self.stop_flag = threading.Event()
        self.last_frame_t = None
        self.frame_count = 0
        self.max_gap = 0.0
        self.gap_log = []
        self.lock = threading.Lock()

    def run(self):
        buffer = bytearray()
        while not self.stop_flag.is_set():
            chunk = self.ser.read(self.ser.in_waiting or 1)
            now = time.monotonic()
            if not chunk:
                continue
            buffer.extend(chunk)
            while True:
                idx = buffer.find(HEADER)
                if idx < 0:
                    if buffer.endswith(b"\xAA"):
                        buffer[:] = b"\xAA"
                    else:
                        buffer.clear()
                    break
                with self.lock:
                    if self.last_frame_t is not None:
                        gap = now - self.last_frame_t
                        if gap > self.max_gap:
                            self.max_gap = gap
                        if gap > 0.05:
                            self.gap_log.append((now, gap))
                    self.last_frame_t = now
                    self.frame_count += 1
                del buffer[: idx + len(HEADER)]

    def snapshot_reset(self):
        with self.lock:
            self.frame_count = 0
            self.max_gap = 0.0
            self.gap_log = []


def hold_combo(isp_ser: serial.Serial, reader: FrameReader, dtr: bool, rts: bool, hold_s: float = 0.5):
    label = f"DTR={int(dtr)} RTS={int(rts)}"
    print(f"\n--- {label} 를 {hold_s}s 유지 ---")
    reader.snapshot_reset()
    t0 = time.monotonic()
    isp_ser.dtr = dtr
    isp_ser.rts = rts
    time.sleep(hold_s)
    with reader.lock:
        count = reader.frame_count
        max_gap = reader.max_gap
        gaps = list(reader.gap_log)
    print(f"  {hold_s}s간 메인포트(UART2) 관찰: {count}프레임, 최대 gap={max_gap*1000:.0f}ms")
    for t, g in gaps:
        print(f"    끊김 감지: {g*1000:.0f}ms (전환+{t - t0:.2f}s 시점)")
    if max_gap > 0.15:
        print(f"  => {label}에서 의미있는 끊김! 이 조합이 리셋/BOOT 트리거일 수 있다.")
    else:
        print("  => 끊김 없음")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--hold", type=float, default=0.5)
    args = parser.parse_args()

    print(f"메인 포트(UART2, 모니터 전용) 여는 중: {MAIN_PORT} @ {MAIN_BAUD}")
    main_ser = serial.Serial(MAIN_PORT, MAIN_BAUD, timeout=0.05)
    main_ser.rts = True
    main_ser.dtr = True

    print(f"ISP 포트(UART1, 시험 대상) 여는 중: {ISP_PORT} @ {ISP_BAUD}")
    isp_ser = serial.Serial(ISP_PORT, ISP_BAUD, timeout=0.1)
    isp_ser.dtr = True
    isp_ser.rts = True
    time.sleep(0.3)

    main_ser.reset_input_buffer()
    reader = FrameReader(main_ser)
    reader.start()

    print("\n=== 기준선 (2초) ===")
    time.sleep(2.0)
    with reader.lock:
        print(f"기준 프레임: {reader.frame_count}개, 최대 gap={reader.max_gap*1000:.0f}ms")
        if reader.frame_count == 0:
            print("!! 메인 포트에서 프레임이 안 들어옵니다. 확인 필요.")

    if args.yes:
        print("\nOLED/부저 지켜봐 주세요. 3초 뒤 시작합니다...")
        time.sleep(3)
    else:
        input("\nOLED/부저 지켜봐 주세요. Enter를 누르면 시작합니다...")

    for dtr, rts in COMBOS:
        hold_combo(isp_ser, reader, dtr, rts, args.hold)
        time.sleep(1.0)

    # 안전하게 정상 상태(리셋 비활성, BOOT0 low)로 복귀
    isp_ser.dtr = True
    isp_ser.rts = False
    time.sleep(0.3)

    reader.stop_flag.set()
    reader.join(timeout=1)
    main_ser.close()
    isp_ser.close()
    print("\n=== 끝 (ISP 포트는 DTR=1(리셋 비활성)/RTS=0(ISP 아님)으로 복귀시킴) ===")


if __name__ == "__main__":
    main()
