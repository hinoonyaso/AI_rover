# 스피커 및 한국어 음성 출력 환경

2026-11-11 Jetson Orin Nano Ubuntu arm64 / ROS 2 Jazzy에서 준비한 개발용 환경. 로봇 제어와 별도이며 마이크 녹음이나 음성 명령 기능은 포함하지 않는다.

## 사용

```bash
tools/audio/speak.sh '안녕하세요. 스피커 출력 시험입니다.'
```

기본 출력은 USB `plughw:CARD=Device,DEV=0`, 기본 음량은 합성 오디오의 0.2배다. 현재 ALSA `Device`는 GeneralPlus USB Audio Device(`1b3f:2008`)이며 카드 번호 대신 이름을 쓴다. 이름은 동일 장치가 추가되면 바뀔 수 있으므로 연결 후 `aplay -l`, `aplay -L`, `ls -l /dev/snd/by-id`로 확인한다. mono→스테레오 형식 변환을 위해 `plughw`를 사용한다.

```bash
JETROVER_TTS_VOLUME=0.1 tools/audio/speak.sh '작은 음량 시험'
JETROVER_AUDIO_DEVICE='plughw:CARD=Device,DEV=0' tools/audio/speak.sh '출력 장치 시험'
JETROVER_AUDIO_DEVICE=null tools/audio/speak.sh '스피커를 사용하지 않는 합성 시험'
```

이 도구는 시스템 기본 오디오 출력이나 믹서 볼륨을 바꾸지 않는다. 스피커가 사용 중이면 ALSA 장치 열기가 실패할 수 있다. `aplay -l`에서 장치가 없으면 케이블·전원을 확인한다. 음량 확인은 `amixer -c Device sget Speaker`. 재생 명령 성공은 실제로 소리가 들렸다는 확인과 다르다.

## 사용자 환경 복구

시스템 패키지 설치 없이 Python 가상환경과 모델을 사용자 디렉터리에 둔다. 필요 패키지: Python 3.12의 `venv`/`pip`, `alsa-utils`의 `aplay`. 아래 명령은 모델 다운로드를 위해 네트워크가 필요하다. 현재 ROS 셸의 `PYTHONPATH`가 가상환경에 섞이지 않도록 Python 실행에서 제외한다.

```bash
mkdir -p "$HOME/.local/share/jetrover-tts/voices"
env -u PYTHONPATH python3 -m venv "$HOME/.local/share/jetrover-tts/venv"
env -u PYTHONPATH "$HOME/.local/share/jetrover-tts/venv/bin/python" -m pip install --only-binary=:all: -r tools/audio/requirements-jetson.txt
env -u PYTHONPATH "$HOME/.local/share/jetrover-tts/venv/bin/python" -m piper.download_voices --data-dir "$HOME/.local/share/jetrover-tts/voices" ko_KR-kss-medium
sha256sum "$HOME/.local/share/jetrover-tts/voices/ko_KR-kss-medium.onnx" "$HOME/.local/share/jetrover-tts/voices/ko_KR-kss-medium.onnx.json"
```

2026-11-11에 받은 모델 SHA-256: `624fd774e26895f24bebae1bd9a3379e3394baeade4b584924f83e414096e2c9`; 설정 JSON: `153b5619d0580f824a59108d83ca19434de410eb8e4fe80325b58684fdc8a1df`. 모델 또는 설정이 갱신되면 출처와 변경 내용을 확인하고 해시를 다시 기록한다.

[Piper](https://github.com/OHF-Voice/piper1-gpl)는 GPL-3.0이다. [KSS 모델 카드](https://huggingface.co/rhasspy/piper-voices/blob/main/ko/ko_KR/kss/medium/MODEL_CARD)는 학습 데이터 라이선스를 CC BY-NC-SA 4.0으로 기재하므로 상업적 사용 전 권리 조건을 확인해야 한다. 이 모델은 개발 시험용으로 설치했으며 배포하거나 저장소에 추가하지 않는다.

## 마이크 방향 진단

`python3 tools/audio/r818_doa.py --seconds 60`은 식별된 마이크 시리얼 포트의 깨우기 이벤트만 대기한다. 기기 각도가 실제로 전달되면 기기 기준 값만 출력한다. 현재 핸드셰이크만 확인됐으며 깨우기 이벤트·영점·회전 방향은 미검증이다. 모든 소리의 연속 DOA가 아니다. 상세 제약과 다음 확인은 `prd/audio-doa.md`.

## 실험용 다채널 DOA

`doa_core.py`는 동기화된 마이크별 PCM과 마이크 좌표를 입력받아 SRP-PHAT로 수평 방향을 추정한다. `doa_stream.py`는 16비트 다채널 WAV 또는 다채널 ALSA 입력을 0.25초 블록으로 읽고 JSONL을 출력한다. Python 3와 NumPy가 필요하다. 무음·방향이 모호한 블록은 `no_estimate`로 표시한다.

**현재 R818 내부 8채널을 Jetson으로 가져오는 실시간 경로 및 채널 배치는 미확인이다.** Jetson의 모노 `XFMDPV0018` USB 장치를 8채널로 지정하면 오류가 나며, 실제 DOA는 아직 동작하지 않는다. `example_doa_geometry.json`은 테스트용 가상 좌표·채널 순서이며 실제 기기 설정이 아니다. 실제 입력의 채널 순서·동기화 및 마이크 좌표, 로봇 정면/반시계 방향을 측정한 별도 JSON이 필요하다. `calibrated`는 사용자가 제공하는 표시일 뿐 프로그램이 보정을 검증하지 않는다.

```bash
# 실제 다채널 WAV와 검증한 geometry JSON이 준비된 경우
python3 tools/audio/doa_stream.py --wav /path/to/multichannel.wav --geometry /path/to/geometry.json

# 실제 다채널 ALSA 입력이 Jetson에 노출된 경우에만 사용
python3 tools/audio/doa_stream.py --device 'hw:CARD=YOUR_ARRAY,DEV=0' --channels 8 --geometry /path/to/geometry.json

python3 -m pytest -q tools/audio/test_doa_core.py tools/audio/test_doa_stream.py
python3 tools/audio/benchmark_doa_synthetic.py
```

JSON의 `channels`는 입력에서 사용할 마이크 6개의 0부터 시작하는 인덱스, `mic_xy_m`은 해당 순서의 평면 좌표(미터), `frame_id`는 좌표계, `calibrated`는 보정 여부다. `--rms-threshold`, `--min-contrast`, `--min-coherence`는 실측 조정 전의 임시 문턱값이다. `relative_contrast`와 `spatial_coherence`는 확률이나 정확도 보장이 아니다. 독립 잡음 200회는 방향이 없다고 판정했지만 상관 잡음·반향·실제 음성에 일반화된 결과가 아니다. 결과를 로봇 구동에 사용하지 않는다. 겹쳐 말하기, 반사·소음, 신호 지연·클리핑, 3차원 소리 위치에 대한 실기 성능은 검증되지 않았다.

### 모노 소음 억제 비교 시험

`python3 tools/audio/mic_denoise_check.py`는 16 kHz 모노를 20초 녹음한다. 처음 2초는 말하지 않고 주변의 지속적인 소음만 수집한 다음 발화한다. 원본과 소음 억제본을 같은 크기로 순서대로 재생하며 녹음은 메모리에서만 처리한다. 장치는 `--capture`, `--playback`, 길이는 `--seconds`로 변경할 수 있다. `python3 -m pytest -q tools/audio/test_denoise_mono.py`로 합성 신호 검증을 실행한다.

이 처리는 첫 2초의 소음 스펙트럼을 이용하는 오프라인 실험이며, 마이크 보드의 기존 처리 이후에 적용된다. 실시간 파이프라인이나 DOA 기능이 아니고, 갑작스러운 소리나 다른 사람의 목소리 제거를 보장하지 않는다. 배경 소음이 바뀌거나 초기 구간에 말소리가 섞이면 음질이 나빠질 수 있다.

### 실시간 모노 소음 억제 시험

```bash
python3 tools/audio/live_denoise.py --seconds 20
python3 -m pytest -q tools/audio/test_live_denoise.py tools/audio/test_denoise_mono.py
```

처음 2초 동안 말을 멈춰 주변 소음을 측정하고, 이어서 20초간 마이크를 처리해 낮은 음량(`--volume 0.1`)으로 스피커에 전달한다. 녹음은 저장하지 않는다. `--capture`, `--playback`, `--seconds`, `--volume`으로 장치와 시험 조건을 변경할 수 있으며 동시 모니터링 음량은 0~0.3으로 제한한다. 스피커를 마이크에서 떨어뜨리고 울림이 발생하면 Ctrl+C로 종료한다. 음향 에코 제거는 구현되지 않았다.

16 kHz 모노를 32 ms 창과 8 ms 간격으로 처리하며 초기 소음 프로필을 고정한다. 실제 환경이 바뀌거나 소음 측정 구간에 말하면 성능이 저하될 수 있다. 오프라인 알고리즘과 세부 처리가 달라 청취 품질도 따로 확인해야 한다. 음성 인식이나 ROS에 연결된 기능은 아니며, 내부 처리 지연 외 ALSA·장치 지연은 별도 측정하지 않았다.

스피커와 마이크 사이 울림을 피하면서 처리 결과를 확인하려면 `python3 tools/audio/live_denoise.py --seconds 15 --deferred`를 실행한다. 기본 재생 음량은 0.5이며 `--volume`으로 0~0.8 범위에서 조절할 수 있다. 입력을 실시간으로 처리해 메모리에 보관하고, 캡처를 종료한 다음에만 재생한다. 청취 지연이 있으므로 동시 모니터링이 아니다.

## 6채널 방향성 집음 실험

`beamform_wav.py`는 실제로 동기화된 6개 마이크 채널과 각 채널에 대응하는 검증된 좌표가 포함된 WAV에서 지정한 방향의 소리를 지연합 방식으로 집음한다. 다음은 예제이며 보정되지 않은 예제 좌표를 실제 기기에 사용하면 안 된다.

```bash
python3 tools/audio/beamform_wav.py --wav six-channel.wav --geometry measured-geometry.json --angle 0 --output beamformed.wav
python3 -m pytest -q tools/audio/test_beamform_array.py
```

출력 파일은 새 파일이어야 한다. 현재 합성 음원에서만 검증했고, 실제 입력 경로와 채널 배치가 확인되지 않아 실기 적용은 미완료다. 전체 WAV를 메모리에서 처리하므로 실시간 집음 기능이 아니다. 저주파·반사음·인접 음원 분리는 제한적이다.

## R818 8채널 스트리밍 진단 (실험용)

`r818_stream_probe.py`는 별도 8채널 인터페이스가 없는 현재 보드에서 실행 중인 `demo`를 잠시 중단하고 16진수로 ADB를 통해 8채널을 가져온다. 1~60초로 제한하고 음성은 저장하지 않는다. 종료 후 보드의 기존 음성 프로그램을 재시작한다. 보드의 음성 기능과 동시 동작하지 않으며 재시작 시 로그가 초기화되어 사전 로그를 보드 `/data/build/demo.log.before-stream-*`에 백업한다. 강제 종료나 연결 장애 시 복구를 반드시 확인해야 한다.

```bash
LD_LIBRARY_PATH=/tmp/jetrover-adb-root/usr/lib/aarch64-linux-gnu/android \
  python3 tools/audio/r818_stream_probe.py \
  --adb /tmp/jetrover-adb-root/usr/lib/android-sdk/platform-tools/adb \
  --geometry tools/audio/experimental_geometry_20261111.json --seconds 10
```

ADB 경로는 현재 시스템의 임시 설치 경로이므로 재부팅 후 달라질 수 있다. 첫 2초는 시작 과도응답 때문에 억제한다. `unverified_candidate`는 RMS 100과 공간 일치도 0.35를 넘은 실험 후보일 뿐 신뢰할 수 있는 방향이나 발화 감지가 아니다. 실기에서 조용한 구간의 후보 및 방향 오차가 발생했다. 특히 모터 제어에 사용하지 않는다. `--min-rms`와 `--min-coherence`는 실험용이며 환경 전용 조정값이다.

`r818_experiment/`에는 보드가 원래 캡처를 독점한 상태에서 데이터그램으로 PCM을 복사하는 실험 소스가 있다. 임시 런타임 주입과 프로그램 재시작이 필요하고, 기존 음성 음질·장시간 부하·경쟁 상태·종단간 지연은 아직 검증되지 않았다. 수신기 이탈 후 기존 프로그램 생존 및 재접속을 짧게 시험했지만 상시 서비스나 로봇 구동에 사용하지 않는다. 상세 측정은 `prd/audio-doa.md`.

## R818 깨우기 이벤트 수신 기록

`python3 tools/audio/r818_wake_probe.py --seconds 90`은 마이크 제어 시리얼의 모든 프레임을 기록한다(기본 수신 전용, `--ack`는 핸드셰이크 확인 응답 전송). 음성을 저장하지 않고 로봇을 움직이지 않는다. 2026-11-22 두 모드 모두 "Hello Hiwonder"에 이벤트가 없었다(`troubleshooting/063`).
