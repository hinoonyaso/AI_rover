#!/usr/bin/env python3
"""Set the R818 voice board wake word over its control serial port.

The board firmware (``/data/build/demo_vtn``) handles a ``wakeup_keywords`` JSON message by
running ``ivw71_keyword_demo -content "<keyword>;nCM:<threshold>" -out vtn/res.bin``, i.e. it
regenerates the on-board wake resource. Back up ``vtn/res.bin`` before using this.
Never moves the robot and does not record audio.

한글: R818 음성 보드의 호출어를 제어 시리얼로 설정한다. 보드 펌웨어는 ``wakeup_keywords``
JSON을 받으면 ``ivw71_keyword_demo``로 ``vtn/res.bin``을 다시 만든다. 사용 전에 ``vtn/res.bin``을
백업한다. 로봇을 움직이지 않고 음성을 녹음하지 않는다.
"""
import argparse
import json
import sys
import time

from r818_doa import ack_frame, DEFAULT_PORT, FrameReader, HANDSHAKE, SYNC

HOST_MESSAGE = 0x05  # host -> board control JSON / 한글: 호스트→보드 제어 JSON


def message_frame(msg_type, msg_id, payload):
    """Build a checksummed frame. / 체크섬을 포함한 프레임을 만든다."""
    body = (bytes((SYNC, 0x01, msg_type)) + len(payload).to_bytes(2, 'little')
            + msg_id.to_bytes(2, 'little') + payload)
    return body + bytes((-sum(body) & 0xFF,))


def wake_keyword_payload(keyword, threshold):
    """Validate and encode the wake-word message. / 호출어 메시지를 검증해 만든다."""
    if not keyword or len(keyword) > 64 or any(c in keyword for c in ';|"\\\n'):
        raise ValueError('invalid keyword')
    if not 1 <= threshold <= 3000:
        raise ValueError('threshold out of range')
    return json.dumps({'type': 'wakeup_keywords',
                       'content': {'keyword': keyword, 'threshold': str(threshold)}},
                      ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def main():
    """Send one wake-word update and print the board's replies. / 호출어 변경 1회와 응답 출력."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', default=DEFAULT_PORT)
    parser.add_argument('--keyword', default='hello hiwonder')
    parser.add_argument('--threshold', type=int, default=900)
    parser.add_argument('--listen', type=float, default=10.0, help='seconds to print replies')
    args = parser.parse_args()
    payload = wake_keyword_payload(args.keyword, args.threshold)
    import serial
    port = serial.Serial(port=None, baudrate=115200, timeout=0.05, write_timeout=0.5,
                         dsrdtr=False, rtscts=False, exclusive=True)
    port.dtr = False
    port.rts = False
    port.port = args.port
    reader = FrameReader()
    port.open()
    try:
        sent = False
        end = time.monotonic() + max(args.listen, 3.0)
        msg_id = 1
        while time.monotonic() < end:
            for frame in reader.feed(port.read(4096)):
                incoming_id = int.from_bytes(frame[5:7], 'little')
                if frame == HANDSHAKE:
                    port.write(ack_frame(incoming_id))
                    if not sent:
                        port.write(message_frame(HOST_MESSAGE, msg_id, payload))
                        sent = True
                        print('보냄:', payload.decode(), flush=True)
                    continue
                if frame[2] != 0xFF:
                    port.write(ack_frame(incoming_id))
                reply = frame[7:-1][:300]
                print(f'응답 type=0x{frame[2]:02x} id={incoming_id} {reply!r}', flush=True)
            if not sent and time.monotonic() > end - max(args.listen, 3.0) + 2.0:
                # Already acknowledged by an earlier session: send without waiting.
                # 한글: 이전 세션에서 핸드셰이크가 끝난 경우 기다리지 않고 보낸다.
                port.write(message_frame(HOST_MESSAGE, msg_id, payload))
                sent = True
                print('보냄(핸드셰이크 없음):', payload.decode(), flush=True)
    finally:
        port.close()
    return 0 if sent else 1


if __name__ == '__main__':
    sys.exit(main())
