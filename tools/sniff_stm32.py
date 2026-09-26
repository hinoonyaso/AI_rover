#!/usr/bin/env python3

import time
import serial

PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_596F003889-if00"
BAUDRATE = 1_000_000


def main():
    ser = serial.Serial(
        port=PORT,
        baudrate=BAUDRATE,
        timeout=0.1,
    )

    print(f"OPEN: {ser.name}")
    print(f"BAUD: {BAUDRATE}")
    print("수신만 수행한다. Ctrl+C 종료")

    try:
        while True:
            data = ser.read(ser.in_waiting or 1)

            if data:
                print(
                    f"{time.monotonic():.3f}  "
                    f"{len(data):3d} bytes  "
                    f"{data.hex(' ')}"
                )

    except KeyboardInterrupt:
        print("\nSTOP")

    finally:
        ser.close()


if __name__ == "__main__":
    main()
