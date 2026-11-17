# Frame and wake-angle parsing tests use synthetic data; no device access.
# 한글: 프레임 및 각도 파싱은 합성 데이터만 사용하며 장치에 접근하지 않는다.
import json

from r818_doa import ack_frame, FrameReader, HANDSHAKE, wake_angle


def frame(kind, msg_id, payload):
    body = (bytes((0xa5, 1, kind)) + len(payload).to_bytes(2, 'little') +
            msg_id.to_bytes(2, 'little') + payload)
    return body + bytes((-sum(body) & 255,))


def test_handshake_ack_and_id():
    assert ack_frame(0) == bytes.fromhex('a5 01 ff 04 00 00 00 a5 00 00 00 b2')
    assert ack_frame(0x1234)[5:7] == b'\x34\x12'
    assert sum(ack_frame(0x1234)) % 256 == 0


def test_fragmented_multiple_frames_and_noise():
    parser = FrameReader()
    assert parser.feed(b'\x00' + HANDSHAKE[:5]) == []
    assert parser.feed(HANDSHAKE[5:] + HANDSHAKE) == [HANDSHAKE, HANDSHAKE]


def test_bad_checksum_and_oversized_prefix_resynchronise():
    parser = FrameReader()
    bad = bytearray(HANDSHAKE)
    bad[-1] ^= 1
    assert parser.feed(bytes(bad) + b'\xa5\x01\x01\xff\xff\x00\x00' + HANDSHAKE) == [HANDSHAKE]


def test_only_valid_wake_event_angle():
    def event(kind, angle):
        data = {'type': 'aiui_event', 'content': {'eventType': kind, 'info': {'angle': angle}}}
        return json.dumps(data).encode()
    assert wake_angle(event(4, 270)) == 270
    assert wake_angle(event(4, 360)) == 0
    for kind, value in ((1, 30), (4, -1), (4, 361), (4, True), (4, '30')):
        assert wake_angle(event(kind, value)) is None
    assert wake_angle(b'{') is None
    assert wake_angle(b'[]') is None


def test_json_string_info():
    data = {'type': 'aiui_event', 'content': {'eventType': 4, 'info': '{"angle": 45}'}}
    payload = json.dumps(data).encode()
    assert wake_angle(frame(2, 7, payload)[7:-1]) == 45
