#!/usr/bin/env bash
# 한글: ST-Link로 지금 STM32에 올라가 있는 플래시 전체(512 KB, STM32F407VET6)를 읽어 백업하고, 알려진 vendor 빌드와 비교한다.
#       읽기만 한다(쓰기/지우기 없음). 단, 읽는 동안 코어가 멈추거나 리셋될 수 있으므로 base_node를 끄고 모터 스위치 OFF.
# Read-only full-flash backup over SWD (st-flash), then compare with the known vendor build.
# Usage: swd_backup.sh [out_dir=~/firmware_source/swd_backup_<date>]
# Writes: flash_512k.bin, sha256, probe.txt, option_bytes.txt (if supported), compare.txt
set -euo pipefail
out=${1:-$HOME/firmware_source/swd_backup_$(date +%Y%m%d_%H%M%S)}
vendor=$HOME/jetrover_ws/firmware_source/decompile/RosRobotControllerM4.bin   # 2026-09-27 reflashed vendor app
pre=$HOME/firmware_source/RosRobotControllerM4_dumped_backup.bin              # UART dump before that reflash
for t in st-info st-flash; do command -v $t >/dev/null || { echo "$t missing: sudo apt install stlink-tools" >&2; exit 1; }; done
pgrep -x base_node >/dev/null && { echo "stop base_node first (tools/nav/stop_nav2.sh / Ctrl+C the launch)" >&2; exit 1; }
mkdir -p "$out"
st-info --probe | tee "$out/probe.txt"
grep -qi "flash: *524288\|flash: 512" "$out/probe.txt" || echo "WARN: flash size is not 512 KB -- check chip (expected STM32F407VET6)"
# RDP: level 0 (0xAA) expected -- the earlier UART bootloader dump worked / UART 덤프가 됐으니 RDP 0이 정상
st-flash --area=option read 2>&1 | tee "$out/option_bytes.txt" || echo "(option byte read not supported by this st-flash)"
st-flash read "$out/flash_512k.bin" 0x08000000 0x80000
(cd "$out" && sha256sum flash_512k.bin > sha256)
{
  echo "readout: $(cut -d' ' -f1 "$out/sha256")"
  n=$(stat -c %s "$vendor")
  if cmp -s -n "$n" "$out/flash_512k.bin" "$vendor"; then
    echo "first $n bytes == vendor build (decompile/RosRobotControllerM4.bin): YES"
  else
    echo "first $n bytes == vendor build: NO ($(cmp -n "$n" "$out/flash_512k.bin" "$vendor" | head -1))"
  fi
  rest=$(tail -c +"$((n + 1))" "$out/flash_512k.bin" | tr -d '\377' | wc -c)
  echo "non-0xFF bytes after the vendor image: $rest"
  cmp -s "$out/flash_512k.bin" "$pre" && echo "== pre-reflash UART dump: identical" \
    || echo "== pre-reflash UART dump: differs (expected, 2026-09-27 reflash)"
} | tee "$out/compare.txt"
echo "backup in $out -- copy it off the Jetson too (firmware_source is not in git)"
