# 한글: RRC 프레임을 직접 만들고 파싱하는 최소 헬퍼(부저, 버스 서보 등 jetrover_base가 아직 안 쓰는 FUNC를 raw로 시험할 때 사용).
"""RRC 프레임을 직접 만들고 파싱하는 최소 헬퍼. jetrover_base가 아직 안 쓰는
FUNC(부저 FUNC2, 버스 서보 FUNC5 등)를 raw로 시험할 때 쓴다.
CRC8-MAXIM은 src/jetrover_base/src/rrc_protocol.cpp의 crc8_maxim과 동일 알고리즘.
"""

import time

import serial

HEADER = b"\xAA\x55"
PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_596F003889-if00"
BAUD = 1_000_000


def crc8_maxim(data: bytes) -> int:
    crc = 0x00
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8C if (crc & 1) else (crc >> 1)
    return crc


def build_frame(func: int, data: bytes) -> bytes:
    body = bytes([func, len(data)]) + data
    return HEADER + body + bytes([crc8_maxim(body)])


class FrameReader:
    def __init__(self, ser: serial.Serial):
        self.ser = ser
        self.buf = bytearray()

    def poll(self):
        """읽을 수 있는 완전한 프레임을 전부 파싱해서 (func, data) 리스트로 반환."""
        chunk = self.ser.read(self.ser.in_waiting or 1)
        if chunk:
            self.buf.extend(chunk)
        frames = []
        while True:
            idx = self.buf.find(HEADER)
            if idx < 0:
                if self.buf.endswith(b"\xAA"):
                    self.buf[:] = b"\xAA"
                else:
                    self.buf.clear()
                break
            if len(self.buf) < idx + 4:
                break
            func = self.buf[idx + 2]
            length = self.buf[idx + 3]
            total = idx + 4 + length + 1
            if len(self.buf) < total:
                break
            data = bytes(self.buf[idx + 4: idx + 4 + length])
            crc = self.buf[idx + 4 + length]
            body = bytes(self.buf[idx + 2: idx + 4 + length])
            if crc8_maxim(body) == crc:
                frames.append((func, data))
                del self.buf[: total]
            else:
                del self.buf[: idx + 1]
        return frames


def open_main_port(timeout=0.1) -> serial.Serial:
    return serial.Serial(PORT, BAUD, timeout=timeout)
