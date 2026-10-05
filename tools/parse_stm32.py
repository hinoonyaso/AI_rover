#!/usr/bin/env python3
# 한글: STM32 시리얼 스트림을 RRC 프레임으로 파싱해 보여주는 초기 점검용 스크립트(CRC 확인). base_node가 포트를 쓰고 있으면 실행 불가.

import serial

PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_596F003889-if00"
BAUDRATE = 1_000_000

HEADER = b"\xAA\x55"


def main():
    ser = serial.Serial(
        PORT,
        BAUDRATE,
        timeout=0.1,
    )

    buffer = bytearray()

    print(f"Listening: {PORT} @ {BAUDRATE}")

    try:
        while True:
            chunk = ser.read(ser.in_waiting or 1)

            if not chunk:
                continue

            buffer.extend(chunk)

            while True:
                header_index = buffer.find(HEADER)

                if header_index < 0:
                    # 마지막 AA는 다음 55와 연결될 수도 있으므로 보존
                    if buffer.endswith(b"\xAA"):
                        buffer[:] = b"\xAA"
                    else:
                        buffer.clear()
                    break

                if header_index > 0:
                    del buffer[:header_index]

                # AA 55 FUNC LEN
                if len(buffer) < 4:
                    break

                function_id = buffer[2]
                payload_length = buffer[3]

                # header2 + func1 + len1 + payload + crc1
                frame_length = 2 + 1 + 1 + payload_length + 1

                if len(buffer) < frame_length:
                    break

                frame = bytes(buffer[:frame_length])
                del buffer[:frame_length]

                payload = frame[4:-1]
                crc = frame[-1]

                print(
                    f"FUNC=0x{function_id:02X} "
                    f"LEN={payload_length:2d} "
                    f"DATA={payload.hex(' ')} "
                    f"CRC=0x{crc:02X}"
                )

    except KeyboardInterrupt:
        pass

    finally:
        ser.close()


if __name__ == "__main__":
    main()
