#!/bin/sh
# Temporarily stream 8-channel PCM as hex; restore the vendor process on exit.
# 한글: 8채널 PCM을 일시적으로 16진수 전송하고 종료 시 기존 프로세스를 복구한다.
set -u
seconds="$1"
case "$seconds" in ''|*[!0-9]*) exit 1;; esac
[ "$seconds" -ge 1 ] && [ "$seconds" -le 60 ] || exit 1
watch_pid=$(ps | awk '$NF=="/data/build/watch" {print $1; exit}')
demo_pid=$(ps | awk '$NF=="./demo" {print $1; exit}')
[ -n "$watch_pid" ] && [ -n "$demo_pid" ] || exit 1
owner=$(sed -n 's/^owner_pid *: *//p' /proc/asound/card1/pcm0c/sub0/status)
[ "$owner" = "$demo_pid" ] || exit 1
backup="/data/build/demo.log.before-stream-$(date +%s)-$$"
[ ! -e "$backup" ] || exit 1
cp -p /data/build/demo.log "$backup" || exit 1
restore() {
 trap - EXIT HUP INT TERM
 if ! kill -0 "$demo_pid" 2>/dev/null; then
  cd /data/build || exit 1
  ./demo </dev/null >/dev/null 2>&1 &
  sleep 3
 fi
 kill -CONT "$watch_pid" 2>/dev/null || true
}
trap restore EXIT HUP INT TERM
kill -STOP "$watch_pid" || exit 1
kill -TERM "$demo_pid" || exit 1
n=0
while kill -0 "$demo_pid" 2>/dev/null && [ "$n" -lt 5 ]; do sleep 1; n=$((n+1)); done
kill -0 "$demo_pid" 2>/dev/null && exit 1
# Hex contains no terminal control characters; adb's PTY may alter binary PCM.
# 한글: ADB PTY의 바이너리 변형을 피하도록 제어 문자가 없는 16진수를 사용한다.
arecord -q -D hw:1,0 -t raw -f S16_LE -c 8 -r 16000 -d "$seconds" 2>/dev/null | hexdump -v -e '1/1 "%02x"'
