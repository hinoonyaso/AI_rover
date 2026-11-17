#!/usr/bin/env bash
# Speak one text on the selected ALSA output with the project-local Piper environment.
# 한글: 프로젝트 전용 Piper 환경으로 지정된 ALSA 출력에 문장 하나를 재생한다.
set -euo pipefail
if [ "$#" -eq 0 ]; then
  printf '사용법: %s "재생할 문장"\n' "$0" >&2
  exit 2
fi
tts_root="${JETROVER_TTS_ROOT:-$HOME/.local/share/jetrover-tts}"
python="$tts_root/venv/bin/python"
model="$tts_root/voices/ko_KR-kss-medium.onnx"
device="${JETROVER_AUDIO_DEVICE:-plughw:CARD=Device,DEV=0}"
volume="${JETROVER_TTS_VOLUME:-0.2}"
if [ ! -x "$python" ] || [ ! -r "$model" ] || [ ! -r "$model.json" ]; then
  printf 'Piper 환경 또는 모델을 찾을 수 없습니다. tools/audio/README.md를 확인하세요.\n' >&2
  exit 1
fi
# Piper emits mono 22,050 Hz signed 16-bit PCM for this model; ALSA plug converts for the USB device.
# 한글: 이 모델의 PCM은 모노 22,050 Hz, 16비트이며 ALSA plug가 USB 형식으로 변환한다.
printf '%s\n' "$*" | env -u PYTHONPATH "$python" -m piper --model "$model" --volume "$volume" --output-raw \
  | aplay -q -D "$device" -t raw -f S16_LE -c 1 -r 22050
