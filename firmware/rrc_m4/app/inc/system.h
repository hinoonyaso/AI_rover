/* 한글: 클럭, 리셋 원인, 치명적 오류 처리(안전 상태 훅 → 모터 출력 0 → IWDG 리셋 대기). */
#ifndef SYSTEM_H
#define SYSTEM_H

#include <stdint.h>

void system_clock_config(void);
void system_capture_reset_cause(void);
uint32_t system_reset_cause(void);
/* Called on fatal errors with interrupts disabled: must only touch registers (no RTOS calls). */
void system_set_safe_state_hook(void (*hook)(void));
__attribute__((noreturn)) void system_fatal(const char *why);

#endif
