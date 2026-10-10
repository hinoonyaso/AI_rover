#!/usr/bin/env bash
# 한글: ST-Link(SWD)로 STM32를 멈추지 않고(halt/reset 없음) 모터 PWM 비교 레지스터(CCR)와 엔코더 카운터(CNT)를 읽기만 한다.
#       032(정지 중 바퀴 울림) 확인용: 울리는 동안 CCR이 0이 아니고 CNT가 몇 틱 안에서 왔다 갔다 하면 = 속도 PID limit cycle 확정.
#       flash/쓰기 없음. 필요: sudo apt install openocd (setup/ENVIRONMENT_SETUP.md). ST-Link는 SWDIO/SWCLK/GND만 연결(3.3V 핀 연결 금지, 보드는 배터리 전원).
# Read-only SWD sampling of the motor PWM compare registers and encoder counters, target keeps running
# (IWDG ~20 ms would reset the board if we halted it). Addresses from firmware_source/PINMAP.md:
#   PWM  TIM1 CCR1..4 (M2 rev/fwd, M1 rev/fwd) 0x40010034..40, TIM9 CCR1/2 (M3) 0x40014034/38,
#        TIM10 CCR1 (M4 rev) 0x40014434, TIM11 CCR1 (M4 fwd) 0x40014834   (M2-M4 pairing = estimate)
#   ENC  CNT: M1 TIM5 0x40000C24, M2 TIM2 0x40000024, M3 TIM4 0x40000824, M4 TIM3 0x40000424
# Usage: swd_motor_probe.sh [samples=50] [interval_ms=100] > Log/swd_motor_probe_<date>.txt
set -euo pipefail
n=${1:-50}
dt=${2:-100}
command -v openocd >/dev/null || { echo "openocd not installed (sudo apt install openocd)" >&2; exit 1; }
openocd -f interface/${ADAPTER:-jlink}.cfg -c "transport select $([ "${ADAPTER:-jlink}" = stlink ] && echo hla_swd || echo swd)" -f target/stm32f4x.cfg \
  -c "reset_config none" -c "init" \
  -c "for {set i 0} {\$i < $n} {incr i} {
        echo \"--- sample \$i\"
        mdw 0x40010034 4
        mdw 0x40014034 2
        mdw 0x40014434 1
        mdw 0x40014834 1
        mdw 0x40000C24 1
        mdw 0x40000024 1
        mdw 0x40000824 1
        mdw 0x40000424 1
        sleep $dt
      }" \
  -c "shutdown" 2>&1
