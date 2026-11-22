#!/usr/bin/env python3
"""Log every frame the R818 voice board sends, to find the real wake-event format.

Passive by default: the vendor examples never write to this port. ``--ack`` sends the
acknowledgement used by r818_doa.py so both behaviours can be compared.
Does not record audio and never moves the robot.

한글: R818 음성 보드가 보내는 모든 프레임을 기록해 실제 깨우기 이벤트 형식을 찾는다.
기본은 수신만 한다(제조사 예제는 이 포트에 쓰지 않는다). ``--ack``는 r818_doa.py의 확인 응답을
보내 두 동작을 비교한다. 음성을 녹음하지 않고 로봇을 움직이지 않는다.
"""
import argparse
import json
import math
import sys
import time

from r818_doa import ack_frame, DEFAULT_PORT, FrameReader, HANDSHAKE


def describe(frame):
    """Summarise one checksummed frame. / 검증된 프레임 하나를 요약한다."""
    msg_type = frame[2]
    msg_id = int.from_bytes(frame[5:7], 'little')
    payload = frame[7:-1]
    text = None
    try:
        decoded = payload.decode('utf-8')
        start = decoded.find('{')
        if start >= 0:
            text = json.loads(decoded[start:decoded.rfind('}') + 1])
    except (UnicodeDecodeError, ValueError):
        pass
    return msg_type, msg_id, payload, text


def main():
    """Run a bounded passive capture. / 시간 제한 수신 기록을 실행한다."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', default=DEFAULT_PORT)
    parser.add_argument('--seconds', type=float, default=60.0)
    parser.add_argument('--ack', action='store_true', help='answer handshake/event frames')
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or not 0 < args.seconds <= 600:
        parser.error('--seconds must be within (0, 600]')
    import serial
    port = serial.Serial(port=None, baudrate=115200, timeout=0.05, write_timeout=0.1,
                         dsrdtr=False, rtscts=False, exclusive=True)
    port.dtr = False
    port.rts = False
    port.port = args.port
    reader = FrameReader()
    start = time.monotonic()
    handshakes = 0
    raw_bytes = 0
    port.open()
    print(f'수신 시작({"ack" if args.ack else "수신 전용"}), {args.seconds:.0f}초', flush=True)
    try:
        while time.monotonic() - start < args.seconds:
            data = port.read(4096)
            raw_bytes += len(data)
            for frame in reader.feed(data):
                t = time.monotonic() - start
                if frame == HANDSHAKE:
                    handshakes += 1
                    if args.ack:
                        port.write(ack_frame(int.from_bytes(frame[5:7], 'little')))
                    continue
                msg_type, msg_id, payload, obj = describe(frame)
                if args.ack and msg_type != 0xFF:
                    port.write(ack_frame(msg_id))
                if obj is not None:
                    print(f'{t:7.2f}s type=0x{msg_type:02x} id={msg_id} JSON {json.dumps(obj, ensure_ascii=False)[:1500]}', flush=True)
                else:
                    print(f'{t:7.2f}s type=0x{msg_type:02x} id={msg_id} len={len(payload)} hex={payload[:48].hex(" ")}', flush=True)
    finally:
        port.close()
        print(f'종료: 수신 {raw_bytes}바이트, 핸드셰이크 {handshakes}회, 남은 미완성 {len(reader.buffer)}바이트', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
