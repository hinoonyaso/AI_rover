# Jetson 로컬 음성·클라우드 LLM 시험 환경

2026-11-12 Jetson Orin Nano 8GB, 25W 모드에서 준비한 수동 시험 환경이다. 한국어 Whisper base STT와 Qwen3 1.7B Q4 로컬 LLM은 CPU 실행, 한국어 TTS는 기존 Piper 환경을 재사용한다. CUDA 빌드, DOA·ROS·주행/팔 제어 통합, 자동 상시 청취는 포함하지 않는다. 고정 길이 녹음이며 VAD는 아직 없다.

## 클라우드 키 입력

기본 제공자는 무료 등급이 있는 [Groq](https://console.groq.com/)이고 모델은 `openai/gpt-oss-20b`다. 가입한 계정에서 API 키를 발급한 뒤 이 파일을 열어 키를 직접 넣는다.

```bash
nano ~/jetrover_ws/tools/voice/.env
```

```dotenv
VOICE_CLOUD_BASE_URL=https://api.groq.com/openai/v1
VOICE_CLOUD_MODEL=openai/gpt-oss-20b
VOICE_CLOUD_API_KEY=여기에_직접_입력
```

`.env`는 Git 제외 및 권한 600으로 생성되며, `.env.example`에는 비밀값을 넣지 않는다. 무료 한도·모델 접근과 정책은 계정 및 시점에 따라 달라지므로 [Groq 한도 안내](https://console.groq.com/docs/rate-limits)와 계정 화면에서 직접 확인한다. 유료 플랜으로 전환하면 과금 조건이 바뀔 수 있다. 다른 OpenAI 호환 Chat Completions 제공자는 URL·모델·해당 제공자 키를 함께 변경하되 호환성은 각기 확인해야 한다. OpenAI 계정의 키를 Groq에 넣지 않는다.

## 실행

```bash
# 16kHz 모노 16비트 WAV 전사
~/jetrover_ws/tools/voice/voice stt /path/to/audio.wav

# 텍스트 대화: 로컬 또는 명시적 클라우드
~/jetrover_ws/tools/voice/voice chat '안녕하세요' --backend local
~/jetrover_ws/tools/voice/voice chat '안녕하세요' --backend cloud

# Piper로 한국어 문장 재생
~/jetrover_ws/tools/voice/voice tts '안녕하세요'

# 5초 녹음 → 한국어 STT → LLM → Piper 재생
~/jetrover_ws/tools/voice/voice once --backend local --seconds 5
~/jetrover_ws/tools/voice/voice once --backend cloud --seconds 5
```

`--backend cloud`를 선택하면 입력한 텍스트 또는 인식된 발화 텍스트가 설정된 제공자에게 전송된다. 기존 `local`/`cloud` 모드에서는 자동 클라우드 전환이 없다. 아래 `auto` 모드는 명시적으로 전송을 허용한 경우에만 클라우드로 분기한다. 단발 녹음 WAV와 STT 임시 파일은 종료 시 삭제한다. `--device`로 녹음 장치를 바꿀 수 있다. 기존 Piper 출력·음량 설정은 `tools/audio/README.md` 참조. 실제 음성·답변 내용을 터미널에 표시하므로 공유 화면과 로그에 주의한다. 언어 모델의 응답은 로봇 명령으로 실행되지 않는다.

## 현재 설치와 재현 정보

설치 위치는 `~/.local/share/jetrover-voice/`다. 재설치는 `tools/voice/setup.sh`를 실행하며 git·cmake·컴파일러·curl·Python venv와 네트워크가 필요하다. 이미 다른 버전의 소스가 있으면 덮어쓰지 않고 중단한다. Python 3.12 가상환경 패키지 복원은 `env -u PYTHONPATH ~/.local/share/jetrover-voice/venv/bin/pip install -r tools/voice/requirements.txt`. 기존 Piper 복원은 `tools/audio/README.md`를 따른다.

- whisper.cpp 소스 `d2c6f05a46dacf663e357bcf0ed40f542a72825d`, CPU 빌드 `whisper-cli`, 모델 `ggerganov/whisper.cpp` revision `5359861c739e955e79d9a303bcbc70fb988958b1`의 `ggml-base.bin`, SHA-256 `60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe`.
- llama.cpp 소스 `956591f4570aa6636895d90439892fef7c075b17`, CPU 빌드 `llama-completion`, `second-state/Qwen3-1.7B-GGUF` revision `9bcdc2d703843e5e820383fe115eb0f7ad586643`의 `Qwen3-1.7B-Q4_K_M.gguf`, SHA-256 `a7f6720f68f4a4567ebf7e3257041dd0b72077b518efe56890aec3516b59b9de`. 가중치는 서드파티 양자화 버전이다.
- 로컬 Qwen3와 Whisper는 Apache-2.0. Piper 엔진은 GPL-3.0, 설치된 한국어 KSS 음성의 학습 데이터는 비상업 라이선스이므로 상용 이용 전 조건을 확인한다.

```bash
env -u PYTHONPATH ~/.local/share/jetrover-voice/venv/bin/python -m unittest discover -s tools/voice -p 'test_*.py' -v
```

클라우드 실제 호출은 키 발급 후 따로 시험해야 한다. 메모리·실행 시간은 구동 조건에 따라 달라지므로 Nav2·카메라·DOA 동시 부하 시험 없이 실제 임무 성능을 보장할 수 없다.

## 초기 단독 검증 (2026-11-12)

CPU, 25W, ROS 전체 통합 없이: Piper 합성 문장 “안녕하세요. 로봇이 한국어 음성을 인식합니다.”를 16kHz 모노로 변환해 Whisper base로 전사한 결과 문장과 일치, 프로세스 실행 포함 2.33초, 최대 RSS 약 284MiB. Qwen3 1.7B Q4에 한국어 한 문장 인사를 요청했을 때 “안녕하세요.”, 실행 포함 5.87초, 최대 RSS 약 2.28GiB. 이 수치는 단일 요청·현재 부하 기준이며 문장 길이와 상태에 따라 달라진다. 실제 마이크 음성·다른 발화 및 로봇의 다른 기능과 동시 실행한 성능은 이 결과로 판단하지 않는다. 클라우드 요청은 SDK 모의 전송 4개 항목으로만 검사했고 실제 무료 등급 접근은 키 발급 후 확인해야 한다.

2026-11-12 실제 마이크 단발 시험: 8초 녹음에서 “안녕하세요?”를 인식하고 로컬 LLM이 “안녕하세요. 어떻게 도와드릴 수 있나요?”를 생성했으며 Piper 재생 명령이 정상 종료됐다. 사용자가 스피커 응답을 잘 들었다고 확인했다. 일회 시험이며 로봇 동시 부하·실사용 정확도 증거는 아니다.


## LangGraph 자동 분기 및 이미지 이해 (실험)

기존 `local`/`cloud` 실행은 그대로다. `auto`는 발화에서 시각·복잡도 단서를 먼저 찾고, 나머지는 로컬 모델에 `local`/`cloud`/`vision` 중 하나를 묻는다. 분류는 휴리스틱이며 정확도를 보장하지 않는다. 잘못된 분기는 `--route`로 직접 지정한다. 각 실행은 단발이며 대화 기록은 저장하지 않는다. 로봇 임무 전송·제어는 구현하지 않았다.

```bash
# 클라우드에 전송하지 않는 자동 분기
~/jetrover_ws/tools/voice/voice chat '안녕하세요' --backend auto
# 텍스트 클라우드 전송 허용 (발화 텍스트 전송 가능)
~/jetrover_ws/tools/voice/voice once --backend auto --allow-cloud --seconds 8
# 카메라 이미지를 클라우드로 보낼 때 두 옵션 모두 명시
~/jetrover_ws/tools/voice/voice once --backend auto --allow-cloud --allow-images --camera --seconds 8
# 이미지 파일과 경로를 직접 지정하는 시험
~/jetrover_ws/tools/voice/voice chat '사진에 무엇이 있나요?' --backend auto --route vision --allow-cloud --allow-images --image /path/to/image.jpg
```

카메라 경로는 별도로 실행 중인 ROS 2 Jazzy `/depth_cam/color/image_raw`를 최대 10초 기다려 한 프레임을 받아 임시 JPEG로 저장한 뒤 삭제한다. 카메라를 자동 실행하거나 로봇을 움직이지 않는다. JPEG/PNG 최대 4MB. 이미지 입력 시 발화 텍스트와 사진이 외부 API로 전송되므로 무료 한도와 제공자 정책을 확인한다.

`.env`에 기존 `VOICE_CLOUD_API_KEY`를 입력하면 텍스트와 VLM에 함께 사용한다. 별도 제공자를 쓰려면 `VOICE_VISION_BASE_URL`, `VOICE_VISION_API_KEY`, `VOICE_VISION_MODEL`을 설정한다(빈 값은 클라우드 URL/키를 사용). 기본 VLM은 Groq 문서상 이미지 입력을 지원하는 `qwen/qwen3.8-27b`; 실제 계정의 모델 접근과 무료 제공 여부는 별도 확인한다: https://console.groq.com/docs/vision . VLM 실패 시 사진 없이 추측하지 않고 실패를 알린다. 클라우드 처리 실패 시 조용히 다른 제공자에 전송하거나 자동 재시도하지 않는다.

검증: 자동 분기·전송 허용·오류·모의 VLM 요청 및 기존 회귀 테스트를 실행했다. 실제 클라우드 API/카메라 사진 전송과 음성 왕복, ROS 동시 부하·분류 정확도는 별도 실기 확인이 필요하다. VAD, 대화 기억, DOA, 로봇 동작 연결은 범위 밖이다.

Jetson 로컬 텍스트 실행에서 초기 분류기가 인사를 vision으로 잘못 분류했다. 흔한 인사를 규칙으로 우선 처리한 후 `안녕하세요`가 local로 분기하고 답변을 생성함을 확인했다. 다른 표현에 대한 정확도와 생성 답변 품질은 추가 평가가 필요하다.

2026-11-12 Groq 실제 연결: 계정 키로 텍스트 모델 응답(서울) 확인. 기존 VLM `qwen/qwen3.6-27b`는 이 계정에서 `model_not_found`(404)였고 모델 목록에 있는 `qwen/qwen3.8-27b`로 교체 후 합성 이미지의 빨간 도형을 올바르게 인식했다. 실제 카메라와 음성 왕복은 아직 미검증이다. 모델 가용성은 계정과 시점에 따라 달라질 수 있다.

## 상시 STT 서버 (whisper.cpp small + CUDA, 2026-11-22)

- 빌드: `~/.local/share/jetrover-voice/src/whisper.cpp`에서 `cmake -B build-cuda -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=87 -DCMAKE_BUILD_TYPE=Release && cmake --build build-cuda -j4 --target whisper-cli whisper-server`(CUDA 13.2, Orin Nano 약 50분). 기존 CPU 빌드 `build/`는 대체용으로 유지.
- 모델: `~/.local/share/jetrover-voice/models/ggml-small.bin`(huggingface `ggerganov/whisper.cpp`, SHA-256 `1be3a9b2063867b937e64e2ec7483364a79917e157fa98c5d94b5c1fffea987b`).
- 서비스: `tools/voice/systemd/jetrover-whisper.service`를 `~/.config/systemd/user/`에 복사 후 `systemctl --user enable --now jetrover-whisper`. `127.0.0.1:8178`만 연다. 메모리 RSS 약 1.2GB(GPU 모델 487MB 포함).
- 대시보드 음성(`tools/ops/backend/voice_routes.py`)은 서버를 먼저 쓰고, 연결이 안 되면 기존 CPU CLI(base)로 대체한다(`JETROVER_STT_URL`, 빈 값이면 서버 미사용).
- 측정(합성 10 + 실제 로봇 마이크 3문장): 힌트 없이 정확 일치 base(CPU) 4/13 → small(GPU) 6/13. 서버+명령 어휘 힌트 10/13. 1문장 전사 시간 CLI base 약 2.0초 → 서버 small 0.25~0.46초. 합성 음성(Piper KSS) 비중이 커서 실제 사람 발화 인식률로 보지 않는다. 자유 질문 단어("보정", "로봇팔")는 여전히 틀릴 수 있다.
