#!/usr/bin/env python3
"""v4의 개선판. 4가지 (DTR,RTS) 조합을 각각 걸기 '직전'에 UART2가 살아있는지 매번 확인하고,
죽어있으면(자연 hang이든 뭐든) RST를 눌러달라고 기다렸다가 살아난 뒤에만 그 조합을 시험한다.
이렇게 해야 "조합 때문에 죽었다"와 "마침 그때 자연 hang이 났다"를 구분할 수 있다.

각 조합마다:
  1. baseline 확인 (죽어있으면 RST 기다림, 최대 30초 폴링)
  2. 그 조합을 0.5초 유지하며 gap 관찰
  3. 안전 상태(DTR=1,RTS=0)로 복귀 후 자동으로 다시 살아나는지 확인
     (안 살아나면 다시 RST 기다림 — 이 경우 "이 조합이 hang을 유발했을 가능성" 플래그)
"""

import argparse
import threading
import time

import serial

MAIN_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_596F003889-if00"
ISP_PORT = "/dev/ttyACM1"
MAIN_BAUD = 1_000_000
ISP_BAUD = 115200
HEADER = b"\xAA\x55"
ALIVE_MIN_HZ = 30  # 정상은 ~130Hz, 이보다 낮으면 죽은 걸로 판정

COMBOS = [(True, True)]


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

    def rate_over(self, seconds: float) -> float:
        self.snapshot_reset()
        time.sleep(seconds)
        with self.lock:
            return self.frame_count / seconds


def wait_for_alive(reader: FrameReader, isp_ser: serial.Serial, context: str, timeout: float = 30.0) -> bool:
    """살아있으면 바로 True. 죽어있으면 RST를 기다리며 폴링, timeout 넘으면 False."""
    rate = reader.rate_over(1.0)
    if rate >= ALIVE_MIN_HZ:
        print(f"  [{context}] 살아있음 ({rate:.0f} Hz)")
        return True

    print(f"  [{context}] !! UART2가 죽어있습니다 ({rate:.0f} Hz). RST 버튼을 눌러주세요. "
          f"(최대 {timeout:.0f}초 대기)")
    # 시험 대상 포트를 안전 상태로 되돌려둔다 (RST를 누르면 정상 앱으로 부팅하도록)
    isp_ser.dtr = True
    isp_ser.rts = False
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        rate = reader.rate_over(1.0)
        if rate >= ALIVE_MIN_HZ:
            print(f"  [{context}] RST 이후 복구됨 ({rate:.0f} Hz)")
            return True
        print(f"    ...아직 죽어있음 ({time.monotonic()-t0:.0f}s 경과, {rate:.0f} Hz)")
    print(f"  [{context}] !! {timeout:.0f}초 넘도록 복구 안 됨. 시험 중단.")
    return False


def test_combo(isp_ser: serial.Serial, reader: FrameReader, dtr: bool, rts: bool, hold_s: float = 0.5):
    label = f"DTR={int(dtr)} RTS={int(rts)}"
    print(f"\n=== 조합 {label} ===")

    if not wait_for_alive(reader, isp_ser, f"{label} 시작 전 baseline"):
        return {"combo": label, "baseline_ok": False, "aborted": True}

    reader.snapshot_reset()
    isp_ser.dtr = dtr
    isp_ser.rts = rts
    time.sleep(hold_s)
    with reader.lock:
        during_count = reader.frame_count
        during_max_gap = reader.max_gap
        during_gaps = list(reader.gap_log)

    print(f"  유지 중({hold_s}s): {during_count}프레임, 최대 gap={during_max_gap*1000:.0f}ms")
    for t, g in during_gaps:
        print(f"    끊김: {g*1000:.0f}ms")

    # 안전 상태로 복귀 + 복구 확인
    isp_ser.dtr = True
    isp_ser.rts = False
    time.sleep(0.3)
    recovered_auto = wait_for_alive(reader, isp_ser, f"{label} 종료 후 복귀 확인", timeout=15.0)

    caused_hang = during_max_gap > 0.15 or not recovered_auto
    verdict = "이 조합이 hang을 유발했을 가능성 있음" if caused_hang else "영향 없음"
    print(f"  => {verdict}")

    return {
        "combo": label,
        "baseline_ok": True,
        "during_count": during_count,
        "during_max_gap_ms": during_max_gap * 1000,
        "recovered_auto": recovered_auto,
        "caused_hang": caused_hang,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()

    print(f"메인 포트(UART2, 모니터 전용) 여는 중: {MAIN_PORT} @ {MAIN_BAUD}")
    main_ser = serial.Serial(MAIN_PORT, MAIN_BAUD, timeout=0.05)
    main_ser.rts = True
    main_ser.dtr = True

    print(f"ISP 포트(UART1, 시험 대상) 여는 중: {ISP_PORT} @ {ISP_BAUD}")
    isp_ser = serial.Serial(ISP_PORT, ISP_BAUD, timeout=0.1)
    isp_ser.dtr = True
    isp_ser.rts = False
    time.sleep(0.3)

    main_ser.reset_input_buffer()
    reader = FrameReader(main_ser)
    reader.start()

    if not wait_for_alive(reader, isp_ser, "시작 전 초기 baseline", timeout=10.0):
        print("초기 baseline부터 죽어있어 시험을 진행할 수 없습니다.")
        reader.stop_flag.set()
        return

    if args.yes:
        print("\nOLED/부저 지켜봐 주세요. 3초 뒤 시작합니다...")
        time.sleep(3)
    else:
        input("\nOLED/부저 지켜봐 주세요. Enter를 누르면 시작합니다...")

    results = []
    for dtr, rts in COMBOS:
        r = test_combo(isp_ser, reader, dtr, rts)
        results.append(r)
        if r.get("aborted"):
            print("이전 조합 복구 대기 중 시험이 중단됐습니다. 이후 조합은 건너뜁니다.")
            break
        time.sleep(1.0)

    isp_ser.dtr = True
    isp_ser.rts = False

    reader.stop_flag.set()
    reader.join(timeout=1)
    main_ser.close()
    isp_ser.close()

    print("\n=== 최종 요약 ===")
    for r in results:
        if r.get("aborted"):
            print(f"{r['combo']}: baseline부터 죽어있어서 시험 못 함")
        else:
            print(f"{r['combo']}: baseline OK, 유지 중 {r['during_count']}프레임/최대gap {r['during_max_gap_ms']:.0f}ms, "
                  f"종료후 자동복구={'O' if r['recovered_auto'] else 'X'} -> {'의심' if r['caused_hang'] else '무관'}")


if __name__ == "__main__":
    main()
