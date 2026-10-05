/* 한글: LED(FUNC1)/부저(FUNC2)용 on/off 패턴 생성기. repeat==0은 무한, off==0은 계속 켬, on==0은 끔/취소. */
/* On/off pattern generator for the LED (FUNC1) and buzzer (FUNC2).
 * Semantics follow the vendor led.c/buzzer.c: (on, off, repeat), repeat == 0 means forever,
 * off == 0 means solid on, on == 0 means off/cancel. A new pattern replaces the running one. */
#ifndef CORE_BLINK_H
#define CORE_BLINK_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint16_t on_ms, off_ms, repeat;
    uint16_t remaining;
    uint16_t elapsed_ms;
    uint8_t active;
    uint8_t level; /* 1 = output asserted */
} blink_t;

void blink_init(blink_t *b);
void blink_set(blink_t *b, uint16_t on_ms, uint16_t off_ms, uint16_t repeat);
/* Advance by dt_ms; returns the output level (1 = on). */
uint8_t blink_tick(blink_t *b, uint16_t dt_ms);

#ifdef __cplusplus
}
#endif
#endif
