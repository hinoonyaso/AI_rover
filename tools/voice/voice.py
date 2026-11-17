#!/usr/bin/env python3
"""Manual local speech and local/cloud text tests; no robot control.

한글: 수동 로컬 음성 및 로컬·클라우드 텍스트 시험이며 로봇을 제어하지 않는다.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import wave

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
DATA = Path.home() / '.local/share/jetrover-voice'
WHISPER = DATA / 'src/whisper.cpp/build/bin/whisper-cli'
WHISPER_MODEL = DATA / 'models/ggml-base.bin'
LLAMA = DATA / 'src/llama.cpp/build/bin/llama-completion'
LLAMA_MODEL = DATA / 'models/Qwen3-1.7B-Q4_K_M.gguf'
SPEAK = ROOT / 'tools/audio/speak.sh'
ENV_FILE = Path(__file__).with_name('.env')


def transcribe(path):
    """Transcribe a 16 kHz mono WAV locally; keep the output temporary.

    한글: 16kHz 모노 WAV를 로컬에서 인식하며 결과 파일은 임시로만 둔다.
    """
    with wave.open(str(path), 'rb') as f:
        if (f.getnchannels() != 1 or f.getsampwidth() != 2 or
                f.getframerate() != 16000 or f.getcomptype() != 'NONE'):
            raise ValueError('STT 입력은 16kHz 16비트 모노 PCM WAV여야 합니다')
    with tempfile.TemporaryDirectory(prefix='jetrover-stt-') as directory:
        output = Path(directory) / 'result'
        subprocess.run([str(WHISPER), '-m', str(WHISPER_MODEL), '-f', str(path),
                        '-l', 'ko', '-t', '4', '-otxt', '-of', str(output), '-np'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True,
                       timeout=180)
        return output.with_suffix('.txt').read_text(encoding='utf-8').strip()


def local_reply(prompt):
    """Generate a short response locally without invoking any robot tools.

    한글: 로봇 도구를 호출하지 않고 로컬에서 짧은 응답을 생성한다.
    """
    formatted = ('<|im_start|>system\n한국어로 간결하고 정확하게 답하세요. '
                 '로봇을 조작했다고 말하지 마세요. /no_think<|im_end|>\n'
                 '<|im_start|>user\n' + prompt + '<|im_end|>\n'
                 '<|im_start|>assistant\n<think>\n\n</think>\n\n')
    p = subprocess.run([str(LLAMA), '-m', str(LLAMA_MODEL), '-p', formatted,
                        '-n', '128', '-t', '4', '-c', '1024', '--temp', '0.3',
                        '--no-display-prompt', '--no-warmup', '--no-conversation',
                        '--simple-io'], capture_output=True, text=True, check=True,
                       timeout=240)
    result = p.stdout.strip().removesuffix('[end of text]').strip()
    result = result.removesuffix('<|im_end|>').strip()
    if not result:
        raise RuntimeError('로컬 모델이 빈 응답을 반환했습니다')
    return result


def cloud_reply(prompt):
    """Call only the explicitly requested cloud endpoint with the configured key.

    한글: 명시적으로 선택한 클라우드에만 설정된 키로 요청한다.
    """
    from openai import OpenAI
    key = os.environ.get('VOICE_CLOUD_API_KEY', '').strip()
    if not key:
        raise ValueError(f'클라우드 키가 없습니다. {ENV_FILE}에 입력해 주세요')
    url = os.environ.get('VOICE_CLOUD_BASE_URL', 'https://api.groq.com/openai/v1').strip()
    model = os.environ.get('VOICE_CLOUD_MODEL', 'openai/gpt-oss-20b').strip()
    if not url.startswith('https://') or not model:
        raise ValueError('클라우드 주소는 HTTPS, 모델 이름은 비어 있지 않아야 합니다')
    client = OpenAI(api_key=key, base_url=url, timeout=30, max_retries=0)
    result = client.chat.completions.create(model=model, messages=[
        {'role': 'system', 'content': '한국어로 간결하게 답하세요. 로봇을 직접 제어하지 않습니다.'},
        {'role': 'user', 'content': prompt}], max_completion_tokens=256)
    text = result.choices[0].message.content
    if not text or not text.strip():
        raise RuntimeError('클라우드 모델이 빈 응답을 반환했습니다')
    return text.strip()


def speak(text):
    """Play Korean text through the existing Piper speaker setup.

    한글: 기존 Piper 스피커 환경으로 한국어 문장을 재생한다.
    """
    subprocess.run([str(SPEAK), text], check=True, timeout=120)


def auto_reply(text, options):
    """Route a text request through LangGraph with explicit upload permissions.

    한글: 전송 허용 조건을 적용해 텍스트 요청을 LangGraph로 분기한다.
    """
    from router import build_graph
    def classify_local(request):
        # A strict label prevents generated text from becoming an executable action.
        # 한글: 정해진 분류값만 허용하여 생성된 문장을 실행 명령으로 쓰지 않는다.
        prompt = ('다음 요청을 분류하세요. 간단한 대화면 local, 복잡한 추론이면 cloud, '
                  '현재 카메라 영상이 필요하면 vision. 영문 분류값 하나만 출력하세요. 요청: ' + request)
        return local_reply(prompt)
    state = build_graph(local_reply, cloud_reply, classify_local).invoke({
        'text': text, 'route': options.route, 'allow_cloud': options.allow_cloud,
        'allow_images': options.allow_images, 'image': str(options.image) if options.image else '',
        'camera': options.camera})
    print(f"처리 경로: {state['route']}", flush=True)
    return state['reply']


def main():
    """Run a local component or explicitly selected cloud conversation.

    한글: 로컬 구성 요소 또는 명시적으로 선택한 클라우드 대화를 실행한다.
    """
    load_dotenv(ENV_FILE, override=False)
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest='command', required=True)
    stt = commands.add_parser('stt', help='transcribe a 16 kHz mono WAV')
    stt.add_argument('wav', type=Path)
    chat = commands.add_parser('chat', help='generate one text reply')
    chat.add_argument('prompt')
    chat.add_argument('--backend', choices=('local', 'cloud', 'auto'), default='local')
    say = commands.add_parser('tts', help='speak a sentence with Piper')
    say.add_argument('text')
    once = commands.add_parser('once', help='record once, transcribe, reply and speak')
    once.add_argument('--backend', choices=('local', 'cloud', 'auto'), default='local')
    once.add_argument('--seconds', type=int, default=5, choices=range(1, 16))
    once.add_argument('--device', default='hw:CARD=XFMDPV0018,DEV=0')
    for command in (chat, once):
        command.add_argument('--allow-cloud', action='store_true', help='allow auto routing to cloud')
        command.add_argument('--allow-images', action='store_true', help='allow image upload in auto routing')
        source = command.add_mutually_exclusive_group()
        source.add_argument('--image', type=Path, help='local JPEG or PNG for vision')
        source.add_argument('--camera', action='store_true', help='capture a ROS camera frame for vision')
        command.add_argument('--route', choices=('auto', 'local', 'cloud', 'vision'), default='auto')
    a = p.parse_args()
    if a.command == 'stt':
        print(transcribe(a.wav))
    elif a.command == 'chat':
        print(auto_reply(a.prompt, a) if a.backend == 'auto' else cloud_reply(a.prompt) if a.backend == 'cloud' else local_reply(a.prompt))
    elif a.command == 'tts':
        speak(a.text)
    else:
        if a.backend == 'cloud' and not os.environ.get('VOICE_CLOUD_API_KEY', '').strip():
            raise ValueError(f'클라우드 키가 없습니다. {ENV_FILE}에 입력해 주세요')
        with tempfile.TemporaryDirectory(prefix='jetrover-voice-') as directory:
            audio = Path(directory) / 'voice.wav'
            print(f'{a.seconds}초 녹음 중...', flush=True)
            subprocess.run(['arecord', '-q', '-D', a.device, '-f', 'S16_LE', '-c', '1',
                            '-r', '16000', '-d', str(a.seconds), str(audio)],
                           check=True, timeout=a.seconds + 10)
            text = transcribe(audio)
        if not text:
            raise ValueError('인식된 음성이 없습니다')
        print(f'인식: {text}', flush=True)
        reply = auto_reply(text, a) if a.backend == 'auto' else cloud_reply(text) if a.backend == 'cloud' else local_reply(text)
        print(f'응답: {reply}', flush=True)
        speak(reply)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, wave.Error, subprocess.SubprocessError) as exc:
        print(f'음성 시험 오류: {exc}', file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        # Never print remote errors that might contain credentials or user content.
        # 한글: 인증 정보나 사용자 내용이 포함될 수 있는 원격 오류는 출력하지 않는다.
        print(f'클라우드 또는 실행 오류: {type(exc).__name__}', file=sys.stderr)
        raise SystemExit(1)
