#!/usr/bin/env python3
"""STM32 ROM 부트로더(AN3155, UART1 = /dev/ttyACM1)로 flash를 읽고 쓰는 도구.

서브커맨드:
  backup   - 전체 flash(512KB, STM32F407VET6)를 읽어 .bin으로 저장 (읽기 전용, 안전)
  compare  - 저장된 backup .bin과 vendor .hex를 바이트 단위로 비교
  flash    - .hex를 파싱해 mass erase 후 write, 다시 읽어서 검증까지 (쓰기, 되돌릴 수 없음)

Write/Erase는 RDP(옵션 바이트)는 절대 건드리지 않는다. mass erase + write만 한다.
"""

import argparse
import sys
import time

import serial

ISP_PORT = "/dev/ttyACM1"
BAUD = 115200
FLASH_BASE = 0x08000000
FLASH_SIZE = 512 * 1024  # STM32F407VET6

ACK = 0x79
NACK = 0x1F

CMD_GET = 0x00
CMD_GET_VERSION_RO = 0x01
CMD_GET_ID = 0x02
CMD_READ_MEMORY = 0x11
CMD_GO = 0x21
CMD_WRITE_MEMORY = 0x31
CMD_EXT_ERASE = 0x44


def enter_bootloader(ser: serial.Serial):
    ser.rts = True
    ser.dtr = True
    time.sleep(0.1)
    ser.dtr = False
    time.sleep(0.2)
    ser.dtr = True
    time.sleep(0.3)
    ser.reset_input_buffer()
    ser.write(bytes([0x7F]))
    ser.flush()
    resp = ser.read(1)
    if not resp or resp[0] != ACK:
        raise RuntimeError(f"부트로더 진입 실패, 응답: {resp.hex() if resp else '(없음)'}")


def exit_bootloader_to_app(ser: serial.Serial):
    ser.rts = False
    ser.dtr = True
    time.sleep(0.1)
    ser.dtr = False
    time.sleep(0.2)
    ser.dtr = True
    time.sleep(0.3)


def wait_ack(ser: serial.Serial, what: str):
    r = ser.read(1)
    if not r or r[0] != ACK:
        raise RuntimeError(f"{what}: ACK 못 받음, 응답={r.hex() if r else '(없음)'}")


def send_cmd(ser: serial.Serial, cmd: int, what: str):
    ser.write(bytes([cmd, cmd ^ 0xFF]))
    ser.flush()
    wait_ack(ser, what)


def read_memory_chunk(ser: serial.Serial, addr: int, length: int) -> bytes:
    assert 1 <= length <= 256
    send_cmd(ser, CMD_READ_MEMORY, "READ cmd")
    addr_bytes = addr.to_bytes(4, "big")
    chk = 0
    for b in addr_bytes:
        chk ^= b
    ser.write(addr_bytes + bytes([chk]))
    ser.flush()
    wait_ack(ser, "READ addr")
    n = length - 1
    ser.write(bytes([n, n ^ 0xFF]))
    ser.flush()
    wait_ack(ser, "READ len")
    data = b""
    deadline = time.monotonic() + 2.0
    while len(data) < length and time.monotonic() < deadline:
        chunk = ser.read(length - len(data))
        if chunk:
            data += chunk
    if len(data) != length:
        raise RuntimeError(f"READ 데이터 부족: {len(data)}/{length}")
    return data


def write_memory_chunk(ser: serial.Serial, addr: int, data: bytes):
    assert 1 <= len(data) <= 256
    send_cmd(ser, CMD_WRITE_MEMORY, "WRITE cmd")
    addr_bytes = addr.to_bytes(4, "big")
    chk = 0
    for b in addr_bytes:
        chk ^= b
    ser.write(addr_bytes + bytes([chk]))
    ser.flush()
    wait_ack(ser, "WRITE addr")
    n = len(data) - 1
    payload = bytes([n]) + data
    chk = 0
    for b in payload:
        chk ^= b
    ser.write(payload + bytes([chk]))
    ser.flush()
    wait_ack(ser, "WRITE data")


def mass_erase(ser: serial.Serial):
    send_cmd(ser, CMD_EXT_ERASE, "ERASE cmd")
    ser.write(bytes([0xFF, 0xFF, 0x00]))
    ser.flush()
    r = ser.read(1)
    deadline = time.monotonic() + 20.0
    while (not r or r[0] != ACK) and time.monotonic() < deadline:
        r = ser.read(1)
    if not r or r[0] != ACK:
        raise RuntimeError(f"ERASE ACK 못 받음, 응답={r.hex() if r else '(없음)'}")


def parse_ihex(path: str) -> bytes:
    """Intel HEX -> 0x08000000 기준 flat binary (빈 곳은 0xFF)."""
    image = bytearray([0xFF] * FLASH_SIZE)
    upper = 0
    touched = False
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line.startswith(":"):
                continue
            raw = bytes.fromhex(line[1:])
            length = raw[0]
            addr16 = (raw[1] << 8) | raw[2]
            rtype = raw[3]
            data = raw[4:4 + length]
            if rtype == 0x04:  # extended linear address
                upper = ((data[0] << 8) | data[1]) << 16
            elif rtype == 0x00:  # data
                full_addr = upper + addr16
                if FLASH_BASE <= full_addr < FLASH_BASE + FLASH_SIZE:
                    off = full_addr - FLASH_BASE
                    image[off:off + len(data)] = data
                    touched = True
            elif rtype == 0x01:  # EOF
                break
    if not touched:
        raise RuntimeError("hex에서 flash 범위(0x08000000+) 데이터를 못 찾음")
    return bytes(image)


def cmd_backup(args):
    print(f"부트로더 진입 중 ({ISP_PORT})...")
    ser = serial.Serial(ISP_PORT, BAUD, parity=serial.PARITY_EVEN, timeout=1.0)
    enter_bootloader(ser)
    print(f"전체 flash 읽기 시작: 0x{FLASH_BASE:08X} ~ 0x{FLASH_BASE+FLASH_SIZE-1:08X} ({FLASH_SIZE} bytes)")
    out = bytearray()
    chunk_size = 256
    t0 = time.monotonic()
    addr = FLASH_BASE
    while addr < FLASH_BASE + FLASH_SIZE:
        n = min(chunk_size, FLASH_BASE + FLASH_SIZE - addr)
        data = read_memory_chunk(ser, addr, n)
        out.extend(data)
        addr += n
        done = addr - FLASH_BASE
        if (done // chunk_size) % 64 == 0:
            print(f"  {done}/{FLASH_SIZE} bytes ({100*done/FLASH_SIZE:.0f}%)")
    elapsed = time.monotonic() - t0
    with open(args.out, "wb") as f:
        f.write(out)
    print(f"완료: {args.out} ({len(out)} bytes, {elapsed:.1f}s)")
    exit_bootloader_to_app(ser)
    ser.close()
    print("리셋 펄스 보냄 (RTS=0). UART2가 안 살아나면 RST 버튼을 눌러주세요.")


def cmd_compare(args):
    with open(args.backup, "rb") as f:
        backup = f.read()
    heximg = parse_ihex(args.hexfile)
    if len(backup) != len(heximg):
        print(f"길이 다름: backup={len(backup)} hex={len(heximg)}")
    n = min(len(backup), len(heximg))
    diffs = [i for i in range(n) if backup[i] != heximg[i]]
    print(f"비교 범위: {n} bytes, 다른 바이트 수: {len(diffs)}")
    if diffs:
        for i in diffs[:20]:
            print(f"  0x{FLASH_BASE+i:08X}: backup=0x{backup[i]:02X} hex=0x{heximg[i]:02X}")
        if len(diffs) > 20:
            print(f"  ... 외 {len(diffs)-20}개")
    else:
        print("완전히 동일함 (지금 보드에 이미 이 .hex가 올라가 있음).")


def cmd_flash(args):
    heximg = parse_ihex(args.hexfile)
    print(f"부트로더 진입 중 ({ISP_PORT})...")
    ser = serial.Serial(ISP_PORT, BAUD, parity=serial.PARITY_EVEN, timeout=1.0)
    enter_bootloader(ser)

    print("Mass erase 중... (최대 20초)")
    t0 = time.monotonic()
    mass_erase(ser)
    print(f"  erase 완료 ({time.monotonic()-t0:.1f}s)")

    print(f"Write 시작: {len(heximg)} bytes")
    chunk_size = 256
    addr = FLASH_BASE
    off = 0
    t0 = time.monotonic()
    while off < len(heximg):
        n = min(chunk_size, len(heximg) - off)
        write_memory_chunk(ser, addr, heximg[off:off + n])
        addr += n
        off += n
        if (off // chunk_size) % 64 == 0:
            print(f"  {off}/{len(heximg)} bytes ({100*off/len(heximg):.0f}%)")
    print(f"Write 완료 ({time.monotonic()-t0:.1f}s)")

    print("검증을 위해 다시 읽는 중...")
    verify = bytearray()
    addr = FLASH_BASE
    while addr < FLASH_BASE + len(heximg):
        n = min(chunk_size, FLASH_BASE + len(heximg) - addr)
        verify.extend(read_memory_chunk(ser, addr, n))
        addr += n
    if bytes(verify) == heximg[:len(verify)]:
        print(f"검증 성공: {len(verify)} bytes 일치")
    else:
        diffs = sum(1 for a, b in zip(verify, heximg) if a != b)
        print(f"!! 검증 실패: {diffs}바이트 불일치")

    exit_bootloader_to_app(ser)
    ser.close()
    print("리셋 펄스 보냄 (RTS=0). UART2가 안 살아나면 RST 버튼을 눌러주세요.")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)

    pb = sub.add_parser("backup")
    pb.add_argument("--out", default="firmware_source/RosRobotControllerM4_dumped_backup.bin")
    pb.set_defaults(func=cmd_backup)

    pc = sub.add_parser("compare")
    pc.add_argument("--backup", default="firmware_source/RosRobotControllerM4_dumped_backup.bin")
    pc.add_argument("--hexfile", required=True)
    pc.set_defaults(func=cmd_compare)

    pf = sub.add_parser("flash")
    pf.add_argument("--hexfile", required=True)
    pf.set_defaults(func=cmd_flash)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
