#!/usr/bin/env python3
"""UART1(ISP 포트, 추정 /dev/ttyACM1)의 DTR이 STM32 NRST를 때리는지 시험한다.

안전 원칙: UART1에는 어떤 바이트도 쓰지 않는다 (ISP 부트로더 프로토콜을 건드리지 않기 위해).
RTS는 계속 False로 고정해서(ISP 진입 안 함) 리셋이 걸려도 항상 정상 앱으로 부팅하게 한다.
검증은 메인 포트(UART2, /dev/ttyACM0)의 IMU 프레임 스트림이 그 순간 끊기는지로 한다
(NRST는 칩 전체를 리셋하므로 진짜 리셋이면 UART2 IMU 스트림도 동시에 끊겨야 한다).
"""

import argparse
import threading
import time

import serial

MAIN_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_596F003889-if00"  # UART2, 알려진 IMU 포트
ISP_PORT = "/dev/ttyACM1"  # UART1, 이번에 새로 연결한 포트
MAIN_BAUD = 1_000_000
ISP_BAUD = 115200  # 제어선만 쓸 거라 baud는 사실 안 중요하지만 문서 값으로 맞춤
HEADER = b"\xAA\x55"


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


def pulse_dtr(isp_ser: serial.Serial, reader: FrameReader, low_ms: int, settle_s: float = 2.5):
    print(f"\n--- UART1 DTR LOW {low_ms}ms -> HIGH (RTS는 계속 False, UART1에 데이터 쓰기 없음) ---")
    reader.snapshot_reset()
    t0 = time.monotonic()
    isp_ser.dtr = False
    time.sleep(low_ms / 1000.0)
    isp_ser.dtr = True
    t1 = time.monotonic()
    time.sleep(settle_s)
    with reader.lock:
        count = reader.frame_count
        max_gap = reader.max_gap
        gaps = list(reader.gap_log)
    print(f"  펄스 구간: {t1 - t0:.3f}s / 이후 {settle_s}s간 메인포트(UART2) 관찰: {count}프레임, 최대 gap={max_gap*1000:.0f}ms")
    for t, g in gaps:
        print(f"    끊김 감지: {g*1000:.0f}ms (펄스 시작+{t - t0:.2f}s 시점)")
    if max_gap > 0.15:
        print("  => 의미있는 끊김 있음! UART1 DTR이 실제로 STM32를 리셋시켰을 가능성이 높다.")
    else:
        print("  => 끊김 없음")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()

    print(f"메인 포트(UART2, 모니터 전용) 여는 중: {MAIN_PORT} @ {MAIN_BAUD}")
    main_ser = serial.Serial(MAIN_PORT, MAIN_BAUD, timeout=0.05)
    main_ser.rts = True
    main_ser.dtr = True  # 메인 포트는 건드리지 않는다 (이미 검증됨, 여기는 영향 없어야 정상)

    print(f"ISP 포트(UART1, 시험 대상) 여는 중: {ISP_PORT} @ {ISP_BAUD}")
    isp_ser = serial.Serial(ISP_PORT, ISP_BAUD, timeout=0.1)
    isp_ser.rts = False  # ISP 진입 방지, 시종일관 고정
    isp_ser.dtr = True
    time.sleep(0.3)

    main_ser.reset_input_buffer()
    reader = FrameReader(main_ser)
    reader.start()

    print("\n=== 기준선 (2초, 메인포트 IMU 스트림 정상 확인) ===")
    time.sleep(2.0)
    with reader.lock:
        print(f"기준 프레임: {reader.frame_count}개, 최대 gap={reader.max_gap*1000:.0f}ms")
        if reader.frame_count == 0:
            print("!! 메인 포트에서 프레임이 안 들어옵니다. STM32가 이미 hang 상태이거나 base_node가 포트를 잡고 있는지 확인하세요.")

    if args.yes:
        print("\nOLED/부저도 지켜봐 주세요. 3초 뒤 시작합니다...")
        time.sleep(3)
    else:
        input("\nOLED/부저도 지켜봐 주세요. Enter를 누르면 시작합니다...")

    for low_ms in (50, 200, 500, 1000):
        pulse_dtr(isp_ser, reader, low_ms)
        time.sleep(1.5)

    reader.stop_flag.set()
    reader.join(timeout=1)
    main_ser.close()
    isp_ser.close()
    print("\n=== 끝 ===")


if __name__ == "__main__":
    main()
