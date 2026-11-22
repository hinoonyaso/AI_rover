#!/usr/bin/env python3
"""Play a short beep on the robot speaker each time the R818 board reports a wake event.

The board itself gives no sound or LED feedback, so this makes wake detection audible.
Prints the device-frame angle and score. Never moves the robot and does not record audio.

한글: R818 보드가 깨우기를 알릴 때마다 로봇 스피커로 짧은 비프음을 낸다. 보드 자체에는 소리·LED
반응이 없어서 인식 여부를 귀로 확인하기 위한 도구다. 기기 기준 각도와 점수를 출력하며 로봇을 움직이지
않고 녹음하지 않는다.
"""
import argparse
import json
import math
import os
import struct
import subprocess
import sys
import time

from r818_doa import ack_frame, DEFAULT_PORT, FrameReader, HANDSHAKE, wake_angle

RATE = 22050


def beep(seconds=0.15, freq=1200.0, volume=0.3):
    """Return mono S16LE PCM for a short tone with soft edges. / 부드러운 짧은 톤 PCM."""
    count = int(RATE * seconds)
    edge = int(RATE * 0.01)
    samples = []
    for i in range(count):
        gain = min(1.0, i / edge, (count - i) / edge) * volume
        samples.append(int(32767 * gain * math.sin(2 * math.pi * freq * i / RATE)))
    return struct.pack('<%dh' % count, *samples)


def wake_score(payload):
    """Return the wake score if present. / 깨우기 점수를 반환한다."""
    try:
        info = json.loads(json.loads(payload.decode('utf-8'))['content']['info'])
        return float(info['ivw']['score'])
    except (ValueError, KeyError, TypeError, UnicodeDecodeError):
        return None


def main():
    """Listen for wake events and beep. / 깨우기 이벤트를 듣고 비프음을 낸다."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', default=DEFAULT_PORT)
    parser.add_argument('--seconds', type=float, default=300.0)
    parser.add_argument('--device', default=os.environ.get('JETROVER_AUDIO_DEVICE',
                                                           'plughw:CARD=Device,DEV=0'))
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or not 0 < args.seconds <= 3600:
        parser.error('--seconds must be within (0, 3600]')
    import serial
    port = serial.Serial(port=None, baudrate=115200, timeout=0.05, write_timeout=0.1,
                         dsrdtr=False, rtscts=False, exclusive=True)
    port.dtr = False
    port.rts = False
    port.port = args.port
    tone = beep()
    reader = FrameReader()
    events = 0
    port.open()
    print(f'대기 중({args.seconds:.0f}초): "Hello Hiwonder"라고 말하면 비프음이 납니다.', flush=True)
    end = time.monotonic() + args.seconds
    try:
        while time.monotonic() < end:
            for frame in reader.feed(port.read(4096)):
                msg_id = int.from_bytes(frame[5:7], 'little')
                if frame[2] != 0xFF:
                    port.write(ack_frame(msg_id))
                if frame == HANDSHAKE:
                    continue
                angle = wake_angle(frame[7:-1])
                if angle is None:
                    continue
                events += 1
                score = wake_score(frame[7:-1])
                print(f'깨우기 {events}: 각도 {angle:.0f}° (기기 기준), 점수 {score}', flush=True)
                subprocess.run(['aplay', '-q', '-D', args.device, '-t', 'raw', '-f', 'S16_LE',
                                '-c', '1', '-r', str(RATE)], input=tone, check=False, timeout=5)
    except KeyboardInterrupt:
        pass
    finally:
        port.close()
    print(f'종료: 깨우기 {events}회', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
