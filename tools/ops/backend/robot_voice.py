"""Robot-microphone voice control: R818 wake word -> command -> local STT -> restricted intents.

Flow: the R818 board detects "Hello Hiwonder" itself and reports it on its control serial
port. The worker beeps, records one command from the board's USB microphone, transcribes it
with the local Whisper, and handles only the dashboard's restricted intents (status,
document evidence, simulated mission start/cancel). Simulated mission writes need a separate
confirmation (next wake + "확인", or the dashboard button). Never moves the robot.

한글: 로봇 마이크 음성 관제. R818 보드가 "Hello Hiwonder"를 직접 감지해 시리얼로 알리면 비프음 후
보드 USB 마이크로 명령 한 개를 녹음하고 로컬 Whisper로 전사해, 대시보드의 제한된 의도(상태,
문서 근거, 모의 임무 시작·취소)만 처리한다. 모의 임무 쓰기는 별도 확인(다시 깨운 뒤 "확인" 또는
대시보드 버튼)이 필요하다. 로봇을 움직이지 않는다.
"""
import io
import math
import re
import os
from pathlib import Path
import struct
import subprocess
import sys
import threading
import time
import uuid
import wave

from voice_intent import classify

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/audio'))
from r818_doa import ack_frame, bearing_label, DEFAULT_PORT, FrameReader, robot_bearing, wake_angle  # noqa: E402
import json  # noqa: E402

CALIBRATION = ROOT / 'tools/audio/r818_wake_calibration.json'


def load_calibration(path=CALIBRATION):
    """Read the wake-angle calibration, or None. / 깨우기 각도 보정값을 읽는다."""
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        float(data['device_front_deg']), int(data['direction'])
        return data
    except (OSError, ValueError, KeyError, TypeError):
        return None

MIC_DEVICE = os.environ.get('JETROVER_MIC_DEVICE', 'plughw:CARD=XFMDPV0018,DEV=0')
SPEAKER_DEVICE = os.environ.get('JETROVER_AUDIO_DEVICE', 'plughw:CARD=Device,DEV=0')
SPEAK = ROOT / 'tools/audio/speak.sh'
PENDING_SECONDS = 30.0
RATE = 16000
FRAME = 320  # 20 ms


def beep_pcm(seconds=0.15, freq=1200.0, volume=0.3, rate=22050):
    """Short tone, mono S16LE. / 짧은 확인음 PCM."""
    count = int(rate * seconds)
    edge = int(rate * 0.01)
    return struct.pack('<%dh' % count, *(
        int(32767 * min(1.0, i / edge, (count - i) / edge) * volume
            * math.sin(2 * math.pi * freq * i / rate)) for i in range(count)))


def segment_command(frames, threshold=300.0, start_frames=3, end_frames=50,
                    max_frames=300, wait_frames=200, skip_frames=8, min_loud=12):
    """Cut one utterance from 20 ms int16 frames with an RMS gate.

    The first ``skip_frames`` are dropped (beep echo from the robot speaker), and a segment
    needs ``min_loud`` loud frames, so clicks and the beep tail are not sent to Whisper
    (it invents text such as "[구독]" for noise). Returns PCM bytes or None.
    한글: 20ms int16 프레임에서 RMS로 발화 하나를 자른다. 처음 ``skip_frames``는 버리고(스피커 비프 잔향),
    큰 프레임이 ``min_loud`` 이상이어야 발화로 본다(잡음에 Whisper가 "[구독]" 같은 문장을 지어냄).
    대기 시간 안에 말이 없으면 None.
    """
    lead, speech, loud, silent, waited, loud_total = [], [], 0, 0, 0, 0
    for index, frame in enumerate(frames):
        if index < skip_frames:
            continue
        count = len(frame) // 2
        if not count:
            continue
        values = struct.unpack('<%dh' % count, frame[:count * 2])
        rms = math.sqrt(sum(v * v for v in values) / count)
        if not speech:
            waited += 1
            lead.append(frame)
            lead = lead[-10:]
            loud = loud + 1 if rms >= threshold else 0
            if loud >= start_frames:
                speech = list(lead)
                loud_total = loud
            elif waited >= wait_frames:
                return None
            continue
        speech.append(frame)
        loud_total += rms >= threshold
        silent = silent + 1 if rms < threshold else 0
        if silent >= end_frames or len(speech) >= max_frames:
            break
    return b''.join(speech) if len(speech) >= 15 and loud_total >= min_loud else None


def hallucinated(text):
    """Detect typical Whisper output for non-speech. / 비발화에 대한 Whisper 환각 문장 판별."""
    stripped = text.strip()
    if not stripped or re.fullmatch(r'[\[(（].*[\])）]', stripped):
        return True
    parts = [p for p in re.split(r'[.!?。]\s*', stripped) if p.strip()]
    return len(parts) >= 3 and len(set(p.strip(' -') for p in parts)) == 1


def wav_bytes(pcm):
    """Wrap 16 kHz mono PCM in a WAV container. / 16kHz 모노 PCM을 WAV로 감싼다."""
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(pcm)
    return buffer.getvalue()


class ArecordFrames:
    """Iterate 20 ms frames from the board microphone. / 보드 마이크의 20ms 프레임."""

    def __init__(self, device=MIC_DEVICE, seconds=8):
        self.process = subprocess.Popen(
            ['arecord', '-q', '-D', device, '-f', 'S16_LE', '-c', '1', '-r', str(RATE),
             '-t', 'raw', '-d', str(seconds)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    def __iter__(self):
        while True:
            chunk = self.process.stdout.read(FRAME * 2)
            if not chunk:
                return
            yield chunk

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.kill()


class RobotVoice:
    """Own the serial port, the microphone and the restricted action flow.

    한글: 시리얼 포트·마이크와 제한된 동작 흐름을 소유한다.
    """

    def __init__(self, *, missions, status, knowledge, transcribe, motion=None,
                 open_serial=None, record=None, speak=None, beep=None, clock=time.monotonic):
        self.missions, self.status, self.knowledge = missions, status, knowledge
        # motion(mission_id, 'pause'|'resume') -> bool, forwarded to the Gazebo worker.
        # 한글: 일시정지·재개를 Gazebo 작업자에 전달하는 함수.
        self.motion = motion
        self.transcribe = transcribe
        self.open_serial = open_serial or self._open_serial
        self.record = record or (lambda: ArecordFrames())
        self.speak_text = speak or self._speak
        self.beep = beep or self._beep
        self.clock = clock
        self.calibration = load_calibration()
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = None
        self.stage = 'off'
        self.error = ''
        self.pending = None
        self.history = []

    # ---- state shared with the API / API와 공유하는 상태 ----
    def snapshot(self):
        with self.lock:
            pending = dict(self.pending) if self.pending else None
            if pending:
                pending['expires_in'] = max(0.0, round(pending.pop('deadline') - self.clock(), 1))
            return {'running': self.thread is not None and self.thread.is_alive(),
                    'stage': self.stage, 'error': self.error, 'pending': pending,
                    'history': list(self.history)}

    def _set(self, stage, error=None):
        with self.lock:
            self.stage = stage
            if error is not None:
                self.error = error

    def _log(self, **entry):
        entry['at'] = time.time()
        # Robot-frame bearing from the measured calibration (rough, see r818_wake_calibration.json).
        # 한글: 측정한 보정값으로 로봇 기준 방위를 덧붙인다(대략값).
        if self.calibration and entry.get('angle') is not None:
            bearing = robot_bearing(entry['angle'], self.calibration)
            entry['bearing'] = round(bearing)
            entry['direction'] = bearing_label(bearing)
        with self.lock:
            self.history = (self.history + [entry])[-20:]

    def start(self):
        with self.lock:
            if self.thread is not None and self.thread.is_alive():
                return False
            self.stop_event.clear()
            self.error = ''
            self.thread = threading.Thread(target=self._run, name='robot-voice', daemon=True)
            self.thread.start()
            return True

    def stop(self, timeout=5.0):
        self.stop_event.set()
        thread = self.thread
        if thread is not None:
            thread.join(timeout)
        with self.lock:
            self.pending = None
            if not (thread and thread.is_alive()):
                self.stage = 'off'

    # ---- hardware defaults / 하드웨어 기본 구현 ----
    @staticmethod
    def _open_serial():
        import serial
        port = serial.Serial(port=None, baudrate=115200, timeout=0.05, write_timeout=0.1,
                             dsrdtr=False, rtscts=False, exclusive=True)
        port.dtr = False
        port.rts = False
        port.port = DEFAULT_PORT
        port.open()
        return port

    @staticmethod
    def _beep():
        subprocess.run(['aplay', '-q', '-D', SPEAKER_DEVICE, '-t', 'raw', '-f', 'S16_LE',
                        '-c', '1', '-r', '22050'], input=beep_pcm(), check=False, timeout=5)

    @staticmethod
    def _speak(text):
        env = os.environ.copy()
        env.pop('PYTHONPATH', None)
        subprocess.run([str(SPEAK), text[:200]], env=env, check=False, timeout=60,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # ---- main loop / 주 반복 ----
    def _run(self):
        port = None
        try:
            port = self.open_serial()
            reader = FrameReader()
            self._set('waiting_wake', '')
            while not self.stop_event.is_set():
                self._expire_pending()
                for frame in reader.feed(port.read(4096)):
                    if frame[2] != 0xFF:
                        port.write(ack_frame(int.from_bytes(frame[5:7], 'little')))
                    angle = wake_angle(frame[7:-1])
                    if angle is None or self.stop_event.is_set():
                        continue
                    self._on_wake(angle)
                    # Drop wake events queued while we were recording/speaking (self-wake).
                    # 한글: 녹음·응답 중 쌓인 깨우기(자기 음성 재유입 포함)는 버린다.
                    port.reset_input_buffer()
                    reader = FrameReader()
                    self._set('waiting_wake')
                    break
        except Exception as exc:  # hardware errors must surface, not kill the server
            self._set('error', f'{type(exc).__name__}: {exc}'[:200])
        finally:
            if port is not None:
                try:
                    port.close()
                except Exception:
                    pass
            if self.stage != 'error':
                self._set('off')

    def _expire_pending(self):
        with self.lock:
            if self.pending and self.clock() > self.pending['deadline']:
                self.pending = None

    def _on_wake(self, angle):
        self.beep()
        self._set('recording')
        recorder = self.record()
        try:
            pcm = segment_command(recorder)
        finally:
            close = getattr(recorder, 'close', None)
            if close:
                close()
        if pcm is None:
            reply = '명령을 듣지 못했습니다. 다시 호출해 주세요.'
            self._log(angle=angle, transcript='', intent='no_speech', reply=reply)
            self._reply(reply)
            return
        self._set('transcribing')
        try:
            transcript = self.transcribe(wav_bytes(pcm)).strip()
        except Exception:
            self._log(angle=angle, transcript='', intent='stt_error', reply='')
            self._reply('음성 인식에 실패했습니다.')
            return
        if hallucinated(transcript):
            reply = '명령을 알아듣지 못했습니다. 다시 호출해 주세요.'
            self._log(angle=angle, transcript=transcript, intent='no_speech', reply=reply)
            self._reply(reply)
            return
        try:
            result = classify(transcript[:300])
        except ValueError:
            result = {'intent': 'unsupported', 'command': ''}
        reply = self.handle(result)
        self._log(angle=angle, transcript=transcript, intent=result['intent'], reply=reply)
        self._reply(reply)

    def _reply(self, text):
        if text:
            self._set('speaking')
            self.speak_text(text)

    # ---- restricted actions / 제한된 동작 ----
    def handle(self, result):
        """Return the spoken reply for one classified command. / 분류된 명령의 응답 문장."""
        intent, command = result['intent'], result.get('command', '')
        # Stopping comes first: "멈춰"/"정지"/"취소" pause a driving mission immediately.
        # 한글: 정지가 최우선이다. 주행 중이면 "멈춰"·"정지"·"취소"는 즉시 일시정지한다.
        if intent in ('pause', 'dismiss'):
            driving = self._gazebo_mission(('gazebo_navigation', 'gazebo_returning'))
            if driving is not None:
                if self.motion and self.motion(driving['id'], 'pause'):
                    return '정지했습니다. 계속하려면 계속해, 끝내려면 종료라고 말해 주세요.'
                return '정지 요청을 보내지 못했습니다. 화면에서 임무를 취소해 주세요.'
            if intent == 'pause':
                return '주행 중인 임무가 없습니다.'
        if intent == 'resume':
            paused = self._gazebo_mission(('gazebo_paused',))
            if paused is None:
                return '멈춰 있는 임무가 없습니다.'
            if self.motion and self.motion(paused['id'], 'resume'):
                return '주행을 계속합니다.'
            return '재개 요청을 보내지 못했습니다.'
        if intent == 'end':
            active = self._gazebo_mission(('gazebo_preparing', 'gazebo_navigation', 'gazebo_returning', 'gazebo_paused'))
            if active is None:
                return '종료할 주행 임무가 없습니다.'
            try:
                self.missions().cancel(active['id'])
            except Exception:
                return '종료 요청을 처리하지 못했습니다. 화면에서 확인해 주세요.'
            return '주행 임무를 종료합니다.'
        if intent == 'confirm':
            return self.confirm()
        if intent == 'dismiss':
            with self.lock:
                had = self.pending is not None
                self.pending = None
            return '대기 중인 요청을 취소했습니다.' if had else '취소할 요청이 없습니다.'
        if intent == 'wake':
            return '네, 말씀하세요. 다시 호출한 뒤 요청해 주세요.'
        with self.lock:
            busy = self.pending is not None
        if busy and intent in ('simulation_start', 'simulation_cancel', 'return_home'):
            return '먼저 대기 중인 요청을 확인하거나 취소해 주세요.'
        if intent == 'status':
            return self._status_reply()
        if intent == 'knowledge':
            return self._knowledge_reply(command)
        if intent == 'mission_status':
            active = self._active_simulations()
            if active is None:
                return '임무 저장소에 연결되지 않았습니다.'
            return f'진행 가능한 모의 임무가 {len(active)}개 있습니다.' if active else '진행 중인 모의 임무가 없습니다.'
        if intent == 'return_home':
            if self._gazebo_mission(('gazebo_preparing', 'gazebo_navigation', 'gazebo_returning', 'gazebo_paused')):
                return '이미 진행 중인 주행 임무가 있습니다.'
            self._set_pending({'kind': 'gazebo_return', 'label': 'Gazebo 출발점 복귀 임무 생성 및 실행'})
            return ('Gazebo에서 출발점 복귀 임무를 시작할까요? 다시 호출한 뒤 확인이라고 말하거나 '
                    '화면에서 확인해 주세요. 실제 로봇은 움직이지 않습니다.')
        if intent == 'simulation_start':
            self._set_pending({'kind': 'start', 'label': '모의 점검 임무 생성 및 실행'})
            return '모의 점검을 시작할까요? 다시 호출한 뒤 확인이라고 말하거나 화면에서 확인해 주세요.'
        if intent == 'simulation_cancel':
            active = self._active_simulations()
            if active is None:
                return '임무 저장소에 연결되지 않았습니다.'
            if len(active) != 1:
                return '취소할 모의 임무가 한 개로 확인되지 않습니다. 화면에서 직접 선택해 주세요.'
            self._set_pending({'kind': 'cancel', 'id': active[0]['id'],
                               'label': f"모의 임무 {active[0]['id'][:8]} 취소"})
            return '모의 임무를 취소할까요? 다시 호출한 뒤 확인이라고 말하거나 화면에서 확인해 주세요.'
        return '지원하지 않는 요청입니다. 상태 조회, 문서 질문, 모의 점검만 할 수 있습니다.'

    def _set_pending(self, action):
        action['deadline'] = self.clock() + PENDING_SECONDS
        with self.lock:
            self.pending = action

    def confirm(self):
        """Execute the pending simulated mission action once. / 대기 중인 모의 임무 동작을 한 번 실행."""
        with self.lock:
            action, self.pending = self.pending, None
        if not action or self.clock() > action['deadline']:
            return '확인할 요청이 없습니다.'
        manager = self.missions()
        if manager is None:
            return '임무 저장소에 연결되지 않았습니다.'
        try:
            if action['kind'] == 'gazebo_return':
                row, _ = manager.create({'request_id': str(uuid.uuid4()), 'mode': 'gazebo',
                                         'kind': 'return_to_start', 'parameters': {}})
                manager.start(row['id'])
                return (f"Gazebo 출발점 복귀 임무를 시작했습니다. 임무 번호 {row['id'][:8]}. "
                        '멈추려면 호출한 뒤 멈춰라고 말해 주세요.')
            if action['kind'] == 'start':
                row, _ = manager.create({'request_id': str(uuid.uuid4()), 'mode': 'simulation',
                                         'kind': 'inspection_demo', 'parameters': {}})
                manager.start(row['id'])
                return f"모의 점검을 시작했습니다. 임무 번호 {row['id'][:8]}. 실제 로봇은 움직이지 않습니다."
            row = manager.get(action['id'])
            if row['mode'] != 'simulation' or row['state'] not in ('created', 'queued', 'running'):
                return '모의 임무 상태가 바뀌어 취소하지 않았습니다.'
            manager.cancel(action['id'])
            return '모의 임무 취소를 요청했습니다.'
        except Exception:
            return '모의 임무 요청을 처리하지 못했습니다. 화면에서 상태를 확인해 주세요.'

    def dismiss(self):
        with self.lock:
            had, self.pending = self.pending is not None, None
        return had

    def _gazebo_mission(self, stages):
        """The running Gazebo mission in one of ``stages``, or None. / 해당 단계의 Gazebo 임무."""
        manager = self.missions()
        if manager is None:
            return None
        try:
            rows = manager.list_recent(limit=20)
        except Exception:
            return None
        return next((r for r in rows if r['mode'] == 'gazebo' and r['state'] == 'running'
                     and r.get('stage') in stages), None)

    def _active_simulations(self):
        manager = self.missions()
        if manager is None:
            return None
        try:
            rows = manager.list_recent(limit=100)
        except Exception:
            return None
        return [r for r in rows if r['mode'] == 'simulation'
                and r['state'] in ('created', 'queued', 'running')]

    def _status_reply(self):
        robot = (self.status() or {}).get('robot') or {}
        voltage = robot.get('battery_voltage')
        battery = '배터리 전압은 미확인' if voltage is None else f'배터리 전압은 {voltage:.1f} 볼트'
        names = (('imu', 'IMU'), ('scan', '라이다'), ('camera', '카메라'))
        streams = ', '.join(
            f"{label} {'수신 중' if (robot.get('streams') or {}).get(key, {}).get('age_seconds') is not None else '수신 미확인'}"
            for key, label in names)
        return f'{battery}입니다. {streams}입니다.'

    def _knowledge_reply(self, question):
        """Speak a short answer: EXAONE text when it answered, else the local source name.

        한글: EXAONE이 답하면 그 답을 짧게, 아니면 로컬 근거 문서 이름을 말한다.
        """
        # EXAONE answers take ~20-35 s (mandatory reasoning); announce the wait while it runs.
        # 한글: EXAONE 답변은 필수 추론 때문에 약 20~35초 걸려 그동안 대기 안내를 먼저 말한다.
        notice = threading.Thread(target=self.speak_text,
                                  args=('문서를 확인하고 있습니다. 잠시만 기다려 주세요.',), daemon=True)
        self._set('answering')
        notice.start()
        try:
            result = self.knowledge(question)
        except Exception:
            result = None
        finally:
            notice.join(15)  # never overlap the final reply / 최종 응답과 겹치지 않게 한다
        if result is None:
            return '문서 검색을 사용할 수 없습니다.'
        if isinstance(result, list):  # plain search rows (tests/older callers)
            result = {'provider': 'local', 'results': result}
        rows = result.get('results') or []
        if not rows:
            return '관련 문서 근거를 찾지 못했습니다.'
        if result.get('provider') == 'exaone' and result.get('answer'):
            return spoken_summary(result['answer'])
        source = rows[0]['source'].rsplit('/', 1)[-1]
        return f'문서 근거를 찾았습니다. {source}. 화면에서 원문을 확인해 주세요.'


def spoken_summary(text, limit=180):
    """Make a generated answer speakable: drop citations/markdown, keep the first sentences.

    한글: 생성 답변을 말하기 좋게 출처 번호·마크다운을 빼고 앞 문장만 남긴다.
    """
    text = re.sub(r'\[\d+(?:[,\s]*\d+)*\]', '', text)
    text = re.sub(r'[*#`>|_]+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\s+([.,!?])', r'\1', text)
    out = ''
    for sentence in re.split(r'(?<=[.!?다요])\s+', text):
        if out and len(out) + len(sentence) + 1 > limit:
            break
        out = (out + ' ' + sentence).strip()
    return out[:limit] or '답변을 화면에서 확인해 주세요.'
