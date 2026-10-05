/* 한글: 버튼 상태기계 구현(디바운스 20ms, 길게 1000ms, 더블클릭 간격 300ms 기본값). */
#include "core/button.h"

void button_init(button_t *b)
{
    b->debounce_ms = 20;
    b->long_press_ms = 1000;
    b->double_gap_ms = 300;
    b->raw_prev = b->stable = b->wait_second = b->long_sent = 0;
    b->raw_ms = b->held_ms = b->gap_ms = 0;
}

/* 한글: 10ms 호출 기준 상태기계. 한 번에 여러 이벤트 비트가 나올 수 있다. */
uint8_t button_tick(button_t *b, uint8_t pressed, uint16_t dt_ms)
{
    uint8_t ev = 0;

    pressed = pressed ? 1 : 0;
    if (pressed != b->raw_prev) {
        b->raw_prev = pressed;
        b->raw_ms = 0;
    } else if (b->raw_ms < 0xFFFF - dt_ms) {
        b->raw_ms = (uint16_t)(b->raw_ms + dt_ms);
    }

    if (pressed != b->stable && b->raw_ms >= b->debounce_ms) {
        b->stable = pressed;
        if (pressed) {
            ev |= BUTTON_EVENT_PRESSED;
            b->held_ms = 0;
            b->long_sent = 0;
        } else if (!b->long_sent) {
            if (b->wait_second) {
                b->wait_second = 0;
                ev |= BUTTON_EVENT_DOUBLE_CLICK;
            } else {
                b->wait_second = 1;
                b->gap_ms = 0;
            }
        }
    }

    if (b->stable) {
        if (b->held_ms < 0xFFFF - dt_ms) {
            b->held_ms = (uint16_t)(b->held_ms + dt_ms);
        }
        if (!b->long_sent && b->held_ms >= b->long_press_ms) {
            b->long_sent = 1;
            b->wait_second = 0;
            ev |= BUTTON_EVENT_LONGPRESS;
        }
    } else if (b->wait_second) {
        b->gap_ms = (uint16_t)(b->gap_ms + dt_ms);
        if (b->gap_ms >= b->double_gap_ms) {
            b->wait_second = 0;
            ev |= BUTTON_EVENT_CLICK;
        }
    }
    return ev;
}
