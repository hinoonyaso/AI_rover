#!/usr/bin/env python3
"""DTR-only STM32 reset test, v2 (RTS held inactive throughout, per-frame gap detection).

Hiwonder 문서: "Reset@DTR Low, ISP@RTS High" -> 일반 리셋만 원하면 RTS는 계속 False(비활성)로
두고 DTR만 Low->High 펄스를 준다. v1은 RTS를 True로 남겨둔 채 DTR을 토글해서 ISP 조합과
섞였을 가능성이 있었고, 2초 창 합계만 봐서 짧은 끊김을 놓쳤을 수 있다. 이 버전은:
- RTS를 시작부터 끝까지 False로 고정
- 별도 리더 스레드가 프레임마다 타임스탬프를 찍어 실시간 gap을 감지
- DTR 펄스 폭을 50/200/500/1000ms로 바꿔가며 시도
"""

import argparse
import threading
import time

import serial

PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_596F003889-if00"
BAUDRATE = 1_000_000
HEADER = b"\xAA\x55"


class FrameReader(threading.Thread):
    def __init__(self, ser: serial.Serial):
        super().__init__(daemon=True)
        self.ser = ser
        self.stop_flag = threading.Event()
        self.last_frame_t = None
        self.frame_count = 0
        self.max_gap = 0.0
        self.gap_log = []  # (t, gap) for gaps > 0.05s
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


def pulse_dtr(ser: serial.Serial, reader: FrameReader, low_ms: int, settle_s: float = 2.0):
    print(f"\n--- DTR LOW {low_ms}ms -> HIGH (RTS는 계속 False) ---")
    reader.snapshot_reset()
    t0 = time.monotonic()
    ser.dtr = False
    time.sleep(low_ms / 1000.0)
    ser.dtr = True
    t1 = time.monotonic()
    time.sleep(settle_s)
    with reader.lock:
        count = reader.frame_count
        max_gap = reader.max_gap
        gaps = list(reader.gap_log)
    print(f"  펄스 구간: {t1 - t0:.3f}s / 이후 {settle_s}s 관찰: {count}프레임, 최대 gap={max_gap*1000:.0f}ms")
    if gaps:
        for t, g in gaps:
            print(f"    끊김 감지: {g*1000:.0f}ms (펄스 시작+{t - t0:.2f}s 시점)")
    if max_gap > 0.15:
        print("  => 의미있는 끊김 있음. 리셋 가능성 있음 (OLED/부저 확인 필요)")
    else:
        print("  => 끊김 없음 (또는 50ms 미만)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()

    print(f"포트 여는 중: {PORT} @ {BAUDRATE}")
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=0.05)
    except serial.SerialException as e:
        print(f"포트 열기 실패: {e}")
        return

    ser.rts = False  # ISP 아님, 계속 비활성으로 고정
    ser.dtr = True   # 리셋 비활성(정상 동작) 상태에서 시작
    time.sleep(0.3)
    ser.reset_input_buffer()

    reader = FrameReader(ser)
    reader.start()

    print("\n=== 기준선 (2초) ===")
    time.sleep(2.0)
    with reader.lock:
        print(f"기준 프레임: {reader.frame_count}개, 최대 gap={reader.max_gap*1000:.0f}ms")

    if args.yes:
        print("\nOLED/부저 지켜봐 주세요. 3초 뒤 시작합니다...")
        time.sleep(3)
    else:
        input("\nOLED/부저 지켜봐 주세요. Enter를 누르면 시작합니다...")

    for low_ms in (50, 200, 500, 1000):
        pulse_dtr(ser, reader, low_ms)
        time.sleep(1.0)

    reader.stop_flag.set()
    reader.join(timeout=1)
    ser.close()
    print("\n=== 끝 ===")


if __name__ == "__main__":
    main()
