#!/usr/bin/env bash
# 한글: soak_log.py(백그라운드)를 PID 파일로 멈춘다(flash 전에 J-Link를 비우려고). pkill -f는 자기 셸을 죽일 수 있어 쓰지 않는다.
# Stop the background soak logger by PID file (frees the J-Link before a flash).
pidfile=${1:-$HOME/jetrover_ws/Log/soak.pid}
pid=$(cat "$pidfile" 2>/dev/null) || { echo "no pid file $pidfile" >&2; exit 1; }
if ps -p "$pid" -o args= | grep -q "soak_log.py"; then kill -INT "$pid"; echo "stopped soak logger $pid"; else echo "pid $pid is not the soak logger (already stopped?)"; fi
