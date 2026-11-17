#!/bin/sh
# Recreate the user-local CPU voice environment without changing system packages.
# 한글: 시스템 패키지를 바꾸지 않고 사용자 전용 CPU 음성 환경을 복구한다.
set -eu
voice_root="$HOME/.local/share/jetrover-voice"
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
mkdir -p "$voice_root/src" "$voice_root/models"
checkout() {
    component="$1"; repository="$2"; revision="$3"
    target="$voice_root/src/$component"
    if [ ! -d "$target/.git" ]; then
        git init "$target"
        git -C "$target" remote add origin "$repository"
        git -C "$target" fetch --depth 1 origin "$revision"
        git -C "$target" checkout --detach FETCH_HEAD
    fi
    current=$(git -C "$target" rev-parse HEAD)
    if [ "$current" != "$revision" ]; then
        printf '%s\n' "다른 버전이 이미 있습니다: $target" >&2
        exit 1
    fi
}
checkout whisper.cpp https://github.com/ggml-org/whisper.cpp.git d2c6f05a46dacf663e357bcf0ed40f542a72825d
checkout llama.cpp https://github.com/ggml-org/llama.cpp.git 956591f4570aa6636895d90439892fef7c075b17
cmake -S "$voice_root/src/whisper.cpp" -B "$voice_root/src/whisper.cpp/build" -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=OFF -DWHISPER_BUILD_TESTS=OFF -DWHISPER_BUILD_EXAMPLES=ON
cmake --build "$voice_root/src/whisper.cpp/build" --target whisper-cli -j 1
cmake -S "$voice_root/src/llama.cpp" -B "$voice_root/src/llama.cpp/build" -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_CURL=OFF
cmake --build "$voice_root/src/llama.cpp/build" --target llama-completion -j 2
if [ ! -f "$voice_root/models/ggml-base.bin" ]; then
    curl -fL --retry 2 'https://huggingface.co/ggerganov/whisper.cpp/resolve/5359861c739e955e79d9a303bcbc70fb988958b1/ggml-base.bin' -o "$voice_root/models/ggml-base.bin.part"
    mv "$voice_root/models/ggml-base.bin.part" "$voice_root/models/ggml-base.bin"
fi
if [ ! -f "$voice_root/models/Qwen3-1.7B-Q4_K_M.gguf" ]; then
    curl -fL --retry 2 'https://huggingface.co/second-state/Qwen3-1.7B-GGUF/resolve/9bcdc2d703843e5e820383fe115eb0f7ad586643/Qwen3-1.7B-Q4_K_M.gguf' -o "$voice_root/models/Qwen3-1.7B-Q4_K_M.gguf.part"
    mv "$voice_root/models/Qwen3-1.7B-Q4_K_M.gguf.part" "$voice_root/models/Qwen3-1.7B-Q4_K_M.gguf"
fi
printf '%s  %s\n' '60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe' "$voice_root/models/ggml-base.bin" | sha256sum -c -
printf '%s  %s\n' 'a7f6720f68f4a4567ebf7e3257041dd0b72077b518efe56890aec3516b59b9de' "$voice_root/models/Qwen3-1.7B-Q4_K_M.gguf" | sha256sum -c -
if [ ! -x "$voice_root/venv/bin/python" ]; then env -u PYTHONPATH python3 -m venv "$voice_root/venv"; fi
env -u PYTHONPATH "$voice_root/venv/bin/pip" install -r "$repo_root/tools/voice/requirements.txt"
if [ ! -e "$repo_root/tools/voice/.env" ]; then
    umask 077
    cp "$repo_root/tools/voice/.env.example" "$repo_root/tools/voice/.env"
fi
printf '%s\n' '기존 Piper 환경은 tools/audio/README.md를 참고하세요.'
