#!/usr/bin/env bash
# 한글: SWD 디버거(J-Link 호환/ST-Link, openocd)로 지금 STM32에 올라가 있는 플래시 전체(512 KB, STM32F407VET6)를 읽어 백업하고,
#       알려진 vendor 빌드와 비교한다. 읽기만 한다(쓰기/지우기 없음). 두 번 읽어 해시가 같아야 성공(클론 디버거 대비).
#       읽는 동안 코어가 멈추면 IWDG로 리셋될 수 있으므로 base_node를 끄고 모터 스위치 OFF.
# Read-only full-flash backup over SWD with openocd, read twice and compared (clone probes can be flaky),
# then compared with the known vendor build.
# Usage: swd_backup.sh [out_dir=~/firmware_source/swd_backup_<date>]
#   ADAPTER=jlink (default, the J-Link OB clone we have) | stlink     SPEED=1000 (kHz; try 400 if it fails)
# Writes: flash_512k.bin, flash_512k_2.bin, sha256, probe.txt, compare.txt
# 2026-10-10: the probe on hand enumerates as SEGGER J-Link PLUS (1366:0101) but reports
# "J-Link ARM-OB STM32" firmware -> a clone. Use openocd; never let SEGGER tools update its firmware.
set -euo pipefail
out=${1:-$HOME/firmware_source/swd_backup_$(date +%Y%m%d_%H%M%S)}
adapter=${ADAPTER:-jlink}
speed=${SPEED:-1000}
vendor=$HOME/jetrover_ws/firmware_source/decompile/RosRobotControllerM4.bin   # 2026-09-27 reflashed vendor app
pre=$HOME/firmware_source/RosRobotControllerM4_dumped_backup.bin              # UART dump before that reflash
command -v openocd >/dev/null || { echo "openocd missing: sudo apt install openocd" >&2; exit 1; }
pgrep -x base_node >/dev/null && { echo "stop base_node first (Ctrl+C the launch)" >&2; exit 1; }
case "$adapter" in
  jlink) iface=(-f interface/jlink.cfg -c "transport select swd") ;;
  stlink) iface=(-f interface/stlink.cfg -c "transport select hla_swd") ;;
  *) echo "ADAPTER must be jlink or stlink" >&2; exit 1 ;;
esac
ocd() { timeout -s KILL 180 openocd "${iface[@]}" -c "adapter speed $speed" -f target/stm32f4x.cfg \
          -c "reset_config none" -c "init" "$@" -c "shutdown" 2>&1; }
mkdir -p "$out"
ocd -c "dap info" -c "flash probe 0" | tee "$out/probe.txt"
grep -q "VTarget = 3\.[0-9]* V" "$out/probe.txt" || { echo "target voltage not ~3.3 V -- check VTref/GND" >&2; exit 1; }
grep -qi "flash size = 512 *KiB\|flash size = 512k" "$out/probe.txt" \
  || echo "WARN: flash size is not reported as 512 KiB -- check probe.txt (expected STM32F407VET6)"
# dump_image may halt the core briefly; reading the flash does not change it / 읽기는 플래시를 바꾸지 않음
ocd -c "dump_image $out/flash_512k.bin 0x08000000 0x80000" | tail -3
ocd -c "dump_image $out/flash_512k_2.bin 0x08000000 0x80000" | tail -3
(cd "$out" && sha256sum flash_512k.bin flash_512k_2.bin > sha256)
if ! cmp -s "$out/flash_512k.bin" "$out/flash_512k_2.bin"; then
  echo "FAIL: the two reads differ -- retry with SPEED=400; do NOT flash anything" >&2; exit 1
fi
[ "$(stat -c %s "$out/flash_512k.bin")" = 524288 ] || { echo "FAIL: dump is not 512 KiB" >&2; exit 1; }
{
  echo "readout (2 reads identical): $(cut -d' ' -f1 "$out/sha256" | head -1)"
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
