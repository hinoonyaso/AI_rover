"""LangGraph voice routing without actuator access.

한글: 구동기 접근 없이 음성 요청을 LangGraph로 분기한다.
"""
import base64
import os
from pathlib import Path
import subprocess
import tempfile
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class VoiceState(TypedDict, total=False):
    """Keep one request's transient routing state. / 한 요청의 임시 분기 상태."""
    text: str
    route: str
    reply: str
    allow_cloud: bool
    allow_images: bool
    image: str
    camera: bool


def classify(text, classify_local):
    """Use explicit visual/complex cues, then ask the local classifier.

    한글: 명시적인 시각·복잡 요청을 우선 판별하고 나머지는 로컬 분류기에 묻는다.
    """
    visual = ('카메라', '사진', '이미지', '화면', '보여', '보이는', '보여줘', '보이니', '보여요', '무엇이 있', '뭐가 있', '뭐가 보여', '무엇이 보여', '앞에 뭐', '앞에 무엇', '어떤 물체', '물체를 찾아', '물건을 찾아', '색깔을 확인', '색을 확인', '읽어줘', '찍어')
    complex_cues = ('자세히', '자세하게', '심층', '비교해', '분석해', '계획을 세', '단계별', '장단점', '복잡한', '설명해 줘', '설명해줘')
    simple = ('안녕', '고마워', '감사합니다', '반가워', '잘 가', '잘자', '잘 자')
    if any(word in text for word in visual):
        return 'vision'
    if any(word in text for word in complex_cues) or len(text) > 100:
        return 'cloud'
    if len(text.strip()) <= 20 and any(word in text for word in simple):
        return 'local'
    try:
        label = classify_local(text).strip().lower()
    except (OSError, RuntimeError, subprocess.SubprocessError):
        return 'local'
    return label if label in ('local', 'cloud', 'vision') else 'local'


def vision_reply(text, image_path):
    """Send one bounded local JPEG or PNG to the configured vision endpoint.

    한글: 제한된 로컬 JPEG 또는 PNG 한 장을 설정된 비전 엔드포인트에 전송한다.
    """
    from openai import OpenAI
    key = os.environ.get('VOICE_VISION_API_KEY', '').strip() or os.environ.get('VOICE_CLOUD_API_KEY', '').strip()
    url = os.environ.get('VOICE_VISION_BASE_URL', '').strip() or os.environ.get('VOICE_CLOUD_BASE_URL', 'https://api.groq.com/openai/v1').strip()
    model = os.environ.get('VOICE_VISION_MODEL', 'qwen/qwen3.8-27b').strip()
    if not key:
        raise ValueError('VLM 또는 클라우드 API 키가 없습니다')
    if not url.startswith('https://') or not model:
        raise ValueError('VLM 주소는 HTTPS, 모델 이름은 비어 있지 않아야 합니다')
    with open(image_path, 'rb') as f:
        data = f.read(4_000_001)
    if len(data) > 4_000_000:
        raise ValueError('이미지는 4MB 이하여야 합니다')
    if data.startswith(b'\xff\xd8\xff'):
        mime = 'image/jpeg'
    elif data.startswith(b'\x89PNG\r\n\x1a\n'):
        mime = 'image/png'
    else:
        raise ValueError('이미지는 JPEG 또는 PNG여야 합니다')
    encoded = base64.b64encode(data).decode('ascii')
    client = OpenAI(api_key=key, base_url=url, timeout=30, max_retries=0)
    response = client.chat.completions.create(model=model, messages=[
        {'role': 'system', 'content': '한국어로 보이는 것만 설명하세요. 불확실하면 불확실하다고 말하세요. 로봇을 제어하지 않습니다.'},
        {'role': 'user', 'content': [{'type': 'text', 'text': text},
         {'type': 'image_url', 'image_url': {'url': f'data:{mime};base64,{encoded}'}}]}], max_completion_tokens=256)
    result = response.choices[0].message.content
    if not result or not result.strip():
        raise RuntimeError('VLM이 빈 응답을 반환했습니다')
    return result.strip()


def capture_camera(path):
    """Capture one fresh ROS camera frame in a separate system Python process.

    한글: 별도의 시스템 Python 프로세스에서 ROS 카메라 최신 프레임을 한 장 수신한다.
    """
    script = Path(__file__).with_name('camera_snapshot.py')
    subprocess.run(['bash', '-c', 'source /opt/ros/jazzy/setup.bash && exec /usr/bin/python3 "$@"',
                    'voice-camera', str(script), str(path)], check=True, timeout=15,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def build_graph(local_reply, cloud_reply, classifier, vision=vision_reply, capture=capture_camera):
    """Build a transient graph with explicit cloud and image gates.

    한글: 클라우드 및 이미지 전송 허용 조건이 있는 임시 그래프를 만든다.
    """
    def route(state):
        chosen = state.get('route', 'auto')
        return {'route': classify(state['text'], classifier) if chosen == 'auto' else chosen}

    def local(state):
        return {'reply': local_reply(state['text'])}

    def cloud(state):
        if not state.get('allow_cloud'):
            return {'reply': '이 요청은 클라우드 처리가 필요합니다. 클라우드 사용을 허용해 주세요.'}
        try:
            return {'reply': cloud_reply(state['text'])}
        except Exception:
            return {'reply': '클라우드 요청에 실패했습니다. API 키와 연결, 사용 한도를 확인해 주세요.'}

    def visual(state):
        if not state.get('allow_cloud') or not state.get('allow_images'):
            return {'reply': '이미지 분석에는 클라우드와 이미지 전송 허용이 모두 필요합니다.'}
        try:
            if state.get('image'):
                result = vision(state['text'], state['image'])
            elif state.get('camera'):
                with tempfile.TemporaryDirectory(prefix='jetrover-camera-') as directory:
                    path = Path(directory) / 'frame.jpg'
                    capture(path)
                    result = vision(state['text'], path)
            else:
                return {'reply': '이미지 분석을 위해 카메라 또는 이미지 파일을 지정해 주세요.'}
            return {'reply': result}
        except Exception:
            return {'reply': '이미지 분석에 실패했습니다. 카메라와 VLM 설정, 연결을 확인해 주세요.'}

    graph = StateGraph(VoiceState)
    graph.add_node('route', route)
    graph.add_node('local', local)
    graph.add_node('cloud', cloud)
    graph.add_node('vision', visual)
    graph.add_edge(START, 'route')
    graph.add_conditional_edges('route', lambda state: state['route'], {'local': 'local', 'cloud': 'cloud', 'vision': 'vision'})
    for name in ('local', 'cloud', 'vision'):
        graph.add_edge(name, END)
    return graph.compile()
