#!/usr/bin/env python3
"""UART1(/dev/ttyACM1)이 진짜 STM32 ROM 부트로더(AN3155)로 응답하는지 읽기 전용으로 확인한다.

절차:
1. RTS=True(BOOT0 high) 상태를 유지한 채 DTR을 Low->High 펄스해서 리셋 (지난 세션에서
   DTR=0&RTS=1이 STM32를 멈추게 한다는 것까지는 확인했지만, 그게 진짜 ROM 부트로더인지는
   아직 검증 안 됐다 — 이번이 그 검증이다).
2. 0x7F 동기화 바이트를 보내고 ACK(0x79)를 기다린다.
3. GET(0x00) 명령으로 부트로더 버전과 지원 명령 목록을 읽는다.
4. GET ID(0x02) 명령으로 칩 PID를 읽는다 (STM32F407이면 0x0413이어야 함).
5. Read-out protection 상태는 GET 응답의 지원 명령 목록에 RDU(0x92)/RDP-related 커맨드가
   있는지로 간접 추정한다(정확한 RDP 레벨은 별도 커맨드 필요, 여기선 하지 않음).

Write/Erase/Go 커맨드는 전혀 보내지 않는다 (읽기 전용). 끝나면 안전 상태로 되돌리고,
정상 앱으로 돌아오려면 RST를 눌러야 할 수 있다고 안내한다.
"""

import sys
import time

import serial

ISP_PORT = "/dev/ttyACM1"
BAUD = 115200

SYNC = 0x7F
ACK = 0x79
NACK = 0x1F

CMD_GET = 0x00
CMD_GET_VERSION_RO = 0x01
CMD_GET_ID = 0x02


def send_cmd(ser: serial.Serial, cmd: int) -> bytes:
    ser.reset_input_buffer()
    ser.write(bytes([cmd, cmd ^ 0xFF]))
    ser.flush()
    return ser.read(1)


def read_exact(ser: serial.Serial, n: int) -> bytes:
    data = b""
    deadline = time.monotonic() + 1.0
    while len(data) < n and time.monotonic() < deadline:
        chunk = ser.read(n - len(data))
        if chunk:
            data += chunk
    return data


def main():
    print(f"포트 여는 중: {ISP_PORT} @ {BAUD}")
    ser = serial.Serial(ISP_PORT, BAUD, parity=serial.PARITY_EVEN, timeout=0.5)

    print("리셋 진입: RTS=1(BOOT0 high) 고정, DTR pulse (reset)")
    ser.rts = True
    ser.dtr = True
    time.sleep(0.1)
    ser.dtr = False
    time.sleep(0.2)
    ser.dtr = True
    time.sleep(0.3)  # 부트로더 초기화 대기

    print("\n0x7F 동기화 바이트 전송...")
    ser.reset_input_buffer()
    ser.write(bytes([SYNC]))
    ser.flush()
    resp = ser.read(1)
    if not resp:
        print("!! 응답 없음 (timeout). ROM 부트로더가 아니거나 baud/타이밍이 안 맞을 수 있음.")
        cleanup(ser)
        return
    if resp[0] == ACK:
        print(f"  ACK (0x{resp[0]:02X}) 받음 -> ROM 부트로더로 보인다!")
    elif resp[0] == NACK:
        print(f"  NACK (0x{resp[0]:02X}) 받음 -> 부트로더는 맞는데 이미 동기화된 상태였을 수 있음.")
    else:
        print(f"  예상 밖 응답: 0x{resp[0]:02X} -> ROM 부트로더가 아닐 가능성이 높다.")
        cleanup(ser)
        return

    print("\nGET(0x00) 명령 전송...")
    r = send_cmd(ser, CMD_GET)
    if r and r[0] == ACK:
        n = read_exact(ser, 1)
        if n:
            count = n[0]
            body = read_exact(ser, count + 1)  # version byte + command bytes
            final_ack = read_exact(ser, 1)
            if len(body) >= 1:
                version = body[0]
                cmds = body[1:]
                print(f"  부트로더 버전: 0x{version:02X}")
                print(f"  지원 명령: {[hex(c) for c in cmds]}")
            print(f"  최종 ACK: {final_ack.hex() if final_ack else '(없음)'}")
    else:
        print(f"  GET 실패, 응답: {r.hex() if r else '(없음)'}")

    print("\nGET ID(0x02) 명령 전송...")
    r = send_cmd(ser, CMD_GET_ID)
    if r and r[0] == ACK:
        n = read_exact(ser, 1)
        if n:
            count = n[0]
            pid_bytes = read_exact(ser, count + 1)
            final_ack = read_exact(ser, 1)
            if len(pid_bytes) >= 2:
                pid = (pid_bytes[0] << 8) | pid_bytes[1]
                print(f"  칩 PID: 0x{pid:04X}" + (" (STM32F40x/41x, 예상과 일치!)" if pid == 0x0413 else " (예상(0x0413)과 다름)"))
            print(f"  최종 ACK: {final_ack.hex() if final_ack else '(없음)'}")
    else:
        print(f"  GET ID 실패, 응답: {r.hex() if r else '(없음)'}")

    cleanup(ser)


def cleanup(ser: serial.Serial):
    print("\n안전 상태로 복귀 시도: RTS=0, DTR pulse (정상 앱 부팅 시도)")
    ser.rts = False
    ser.dtr = True
    time.sleep(0.1)
    ser.dtr = False
    time.sleep(0.2)
    ser.dtr = True
    time.sleep(0.3)
    ser.close()
    print("STM32는 여전히 부트로더에 있을 수 있습니다. UART2가 안 살아나면 RST 버튼을 눌러주세요.")


if __name__ == "__main__":
    main()
