#!/usr/bin/env python3
"""Display verified R818 wake-angle events; not continuous sound-source tracking.

한글: R818 깨우기 각도 이벤트를 표시하며 모든 소리의 연속 방향 추정은 아니다.
"""
import argparse
import json
import math
import sys
import time

SYNC = 0xA5
MAX_PAYLOAD = 8192
HANDSHAKE = bytes.fromhex('a5 01 01 04 00 00 00 a5 00 00 00 b0')
DEFAULT_PORT = '/dev/serial/by-path/platform-3610000.usb-usb-0:2.1.1.1:1.0-port0'


def ack_frame(message_id):
    """Build the documented acknowledgement, preserving the incoming message ID.

    한글: 수신 메시지 ID를 유지하는 문서상 확인 응답을 만든다.
    """
    if (not isinstance(message_id, int) or isinstance(message_id, bool) or
            not 0 <= message_id <= 65535):
        raise ValueError('invalid message ID')
    body = bytes((SYNC, 1, 0xFF, 4, 0)) + message_id.to_bytes(2, 'little') + bytes((SYNC, 0, 0, 0))
    return body + bytes((-sum(body) & 0xff,))


class FrameReader:
    """Parse bounded, checksummed serial frames without trusting partial input.

    한글: 부분 입력과 손상 프레임을 검증하며 크기가 제한된 프레임만 반환한다.
    """

    def __init__(self):
        self.buffer = bytearray()

    def feed(self, data):
        """Return complete valid frames, retaining incomplete trailing data.

        한글: 유효한 완성 프레임만 반환하고 미완성 데이터는 보관한다.
        """
        self.buffer.extend(data)
        frames = []
        while len(self.buffer) >= 8:
            if self.buffer[0] != SYNC or self.buffer[1] != 1:
                del self.buffer[0]
                continue
            length = int.from_bytes(self.buffer[3:5], 'little')
            if length > MAX_PAYLOAD:
                del self.buffer[0]
                continue
            total = length + 8
            if len(self.buffer) < total:
                break
            frame = bytes(self.buffer[:total])
            if sum(frame) & 0xff:
                del self.buffer[0]
                continue
            del self.buffer[:total]
            frames.append(frame)
        return frames


def wake_angle(payload):
    """Extract only a valid wake event angle in device degrees, or return None.

    한글: 정상적인 깨우기 이벤트의 기기 기준 각도만 추출하고 아니면 None을 반환한다.
    """
    try:
        obj = json.loads(payload.decode('utf-8'))
        if not isinstance(obj, dict) or obj.get('type') != 'aiui_event':
            return None
        content = obj.get('content')
        if not isinstance(content, dict) or content.get('eventType') != 4:
            return None
        info = content.get('info')
        if isinstance(info, str):
            info = json.loads(info)
        if not isinstance(info, dict):
            return None
        angle = info.get('angle')
        if isinstance(angle, bool) or not isinstance(angle, (int, float)):
            return None
        if not math.isfinite(angle) or not 0 <= angle <= 360:
            return None
        return float(angle) % 360
    except (UnicodeDecodeError, ValueError, TypeError, RecursionError):
        return None


def main():
    """Run an explicit, time-limited device test and print device-frame angles only.

    한글: 명시적으로 실행한 시간 제한 장치 시험에서 기기 기준 각도만 출력한다.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', default=DEFAULT_PORT)
    parser.add_argument('--seconds', type=float, default=60.0)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds <= 0:
        parser.error('--seconds must be finite and positive')
    try:
        import serial
    except ImportError:
        print('pyserial이 필요합니다.', file=sys.stderr)
        return 2
    port = serial.Serial(port=None, baudrate=115200, timeout=0.02, write_timeout=0.1,
                         dsrdtr=False, rtscts=False, exclusive=True)
    port.dtr = False
    port.rts = False
    port.port = args.port
    decoder = FrameReader()
    identified = False
    events = 0
    try:
        port.open()
        print('대기 중: 깨우기 단어가 인식되면 기기 기준 각도를 출력합니다.', flush=True)
        end = time.monotonic() + args.seconds
        while time.monotonic() < end:
            for frame in decoder.feed(port.read(512)):
                if not identified:
                    if frame != HANDSHAKE:
                        continue
                    identified = True
                    print('마이크 핸드셰이크 확인', flush=True)
                msg_type = frame[2]
                if msg_type != 0xff:
                    port.write(ack_frame(int.from_bytes(frame[5:7], 'little')))
                if msg_type != 1 and msg_type != 0xff:
                    angle = wake_angle(frame[7:-1])
                    if angle is not None:
                        events += 1
                        print(f'깨우기 각도: {angle:.1f}° (기기 기준, 로봇 방향 미보정)', flush=True)
                    else:
                        print(f'각도 없는 장치 메시지: type=0x{msg_type:02x}, '
                              f'size={len(frame) - 8}', flush=True)
    except (serial.SerialException, OSError) as exc:
        print(f'시리얼 오류: {exc}', file=sys.stderr)
        return 1
    finally:
        if port.is_open:
            port.close()
    if not identified:
        print('마이크 핸드셰이크를 확인하지 못했습니다.', file=sys.stderr)
        return 1
    print(f'수신 종료: 각도 이벤트 {events}개', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
