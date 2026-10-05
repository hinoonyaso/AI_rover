/* 한글: 디바운스된 버튼 상태기계: PRESSED/LONGPRESS/CLICK/DOUBLE_CLICK(FUNC6) 이벤트를 만든다. 입력은 active-low(PE0/PE1). */
/* Debounced button FSM producing the FUNC6 events (pressed / long press / click / double click).
 * Reconstructed behaviour of the vendor button.c (state machine at FUN_0800bad8); timing
 * constants are the usual vendor values and are configurable. Active-low inputs (PE0/PE1). */
#ifndef CORE_BUTTON_H
#define CORE_BUTTON_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define BUTTON_EVENT_PRESSED 0x01
#define BUTTON_EVENT_LONGPRESS 0x02
#define BUTTON_EVENT_CLICK 0x20
#define BUTTON_EVENT_DOUBLE_CLICK 0x40

typedef struct {
    uint16_t debounce_ms;      /* default 20 */
    uint16_t long_press_ms;    /* default 1000 */
    uint16_t double_gap_ms;    /* default 300 */
    uint8_t raw_prev, stable, wait_second, long_sent;
    uint16_t raw_ms, held_ms, gap_ms;
} button_t;

void button_init(button_t *b);
/* pressed: 1 when the key is physically down. Returns a BUTTON_EVENT_* mask (0 if none);
 * several bits can be returned in the same call. */
uint8_t button_tick(button_t *b, uint8_t pressed, uint16_t dt_ms);

#ifdef __cplusplus
}
#endif
#endif
