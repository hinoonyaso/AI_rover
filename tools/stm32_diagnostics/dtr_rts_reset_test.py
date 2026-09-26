#!/usr/bin/env python3
"""DTR/RTS로 STM32를 리셋시킬 수 있는지 시험한다.

전제: base_node 등 시리얼 포트를 쓰는 노드가 꺼져 있어야 한다(포트 단독 점유 필요).
동작: 기준 프레임 수신을 확인한 뒤, RTS/DTR을 여러 조합으로 토글하면서
프레임 스트림이 끊겼다가 "새로 부팅한 것처럼" 다시 시작되는지 관찰한다.
STM32가 실제로 리셋되면 보통 1) 프레임이 잠깐(수백ms~수초) 끊기고,
2) OLED/부저가 부팅 동작을 보인다(육안 확인 필요 — 이 스크립트는 시리얼만 본다).
"""

import argparse
import sys
import time

import serial

PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_596F003889-if00"
BAUDRATE = 1_000_000
HEADER = b"\xAA\x55"


def count_frames(ser: serial.Serial, duration: float) -> tuple[int, float, float]:
    """duration초 동안 헤더 개수를 센다. (개수, 첫 프레임까지 걸린 시간 또는 -1, 총 걸린 시간)"""
    buffer = bytearray()
    count = 0
    first_frame_delay = -1.0
    start = time.monotonic()
    while time.monotonic() - start < duration:
        chunk = ser.read(ser.in_waiting or 1)
        if chunk:
            buffer.extend(chunk)
            while True:
                idx = buffer.find(HEADER)
                if idx < 0:
                    if buffer.endswith(b"\xAA"):
                        buffer[:] = b"\xAA"
                    else:
                        buffer.clear()
                    break
                if count == 0 and first_frame_delay < 0:
                    first_frame_delay = time.monotonic() - start
                count += 1
                del buffer[: idx + len(HEADER)]
    return count, first_frame_delay, time.monotonic() - start


def try_reset(ser: serial.Serial, label: str, apply_fn, settle: float = 2.0):
    print(f"\n--- 시도: {label} ---")
    apply_fn()
    print(f"  (신호 인가함, {settle}s 대기하며 프레임 관찰...)")
    frames, first_delay, elapsed = count_frames(ser, settle)
    rate = frames / elapsed if elapsed > 0 else 0
    print(f"  결과: {frames}프레임 / {elapsed:.2f}s ({rate:.1f} Hz)"
          + (f", 첫 프레임까지 {first_delay:.2f}s" if first_delay >= 0 else ", 프레임 없음(끊김)"))
    return frames, first_delay


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes", action="store_true", help="Enter 확인 없이 바로 시작 (OLED는 사용자가 직접 지켜봐야 함)")
    args = parser.parse_args()

    print(f"포트 여는 중: {PORT} @ {BAUDRATE}")
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)
    except serial.SerialException as e:
        print(f"포트 열기 실패: {e}")
        print("base_node 등 다른 프로세스가 포트를 쓰고 있지 않은지 확인하세요.")
        sys.exit(1)

    # 기본적으로 pyserial은 open 시 DTR/RTS를 활성화(True)한다.
    ser.dtr = True
    ser.rts = True
    time.sleep(0.3)
    ser.reset_input_buffer()

    print("\n=== 0단계: 기준선 (아무 신호도 안 건드림, 2초) ===")
    frames, _, elapsed = count_frames(ser, 2.0)
    print(f"기준 프레임: {frames}개 / {elapsed:.2f}s ({frames/elapsed:.1f} Hz)")
    if frames == 0:
        print("!! 기준선에서부터 프레임이 없습니다. STM32가 이미 hang 상태이거나 배선 문제일 수 있습니다.")
        print("   (hang 상태에서 리셋 시험을 하는 것도 의미 있습니다 — 계속 진행합니다.)")

    if args.yes:
        print("\n로봇 OLED/부저를 지금부터 지켜봐 주세요. 3초 뒤 RTS 펄스 시험을 시작합니다...")
        time.sleep(3)
    else:
        input("\n로봇 OLED/부저를 지금부터 지켜봐 주세요. 준비되면 Enter를 눌러 RTS 펄스 시험을 시작합니다...")

    try_reset(ser, "RTS LOW 200ms -> HIGH", lambda: (setattr(ser, "rts", False), time.sleep(0.2), setattr(ser, "rts", True)))
    time.sleep(1.0)

    try_reset(ser, "DTR LOW 200ms -> HIGH", lambda: (setattr(ser, "dtr", False), time.sleep(0.2), setattr(ser, "dtr", True)))
    time.sleep(1.0)

    try_reset(ser, "RTS+DTR 동시 LOW 200ms -> HIGH",
              lambda: (setattr(ser, "rts", False), setattr(ser, "dtr", False), time.sleep(0.2),
                       setattr(ser, "rts", True), setattr(ser, "dtr", True)))
    time.sleep(1.0)

    try_reset(ser, "RTS LOW 유지 1초 (긴 펄스)", lambda: (setattr(ser, "rts", False), time.sleep(1.0), setattr(ser, "rts", True)))

    ser.close()
    print("\n=== 끝 ===")
    print("판정 기준: 신호 인가 직후 프레임이 한동안(수백ms 이상) 끊겼다가 다시 시작됐고,")
    print("동시에 OLED/부저가 부팅처럼 움직였다면 -> 그 신호가 STM32 리셋 라인일 가능성이 높습니다.")
    print("아무 변화도 없었다면(프레임이 끊기지 않고 계속 흐름) -> 그 신호선은 리셋과 무관합니다.")


if __name__ == "__main__":
    main()
