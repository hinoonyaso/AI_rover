/* 한글: 깜빡임 패턴 구현. */
#include "core/blink.h"

void blink_init(blink_t *b)
{
    b->on_ms = b->off_ms = b->repeat = 0;
    b->remaining = 0;
    b->elapsed_ms = 0;
    b->active = 0;
    b->level = 0;
}

void blink_set(blink_t *b, uint16_t on_ms, uint16_t off_ms, uint16_t repeat)
{
    b->on_ms = on_ms;
    b->off_ms = off_ms;
    b->repeat = repeat;
    b->remaining = repeat;
    b->elapsed_ms = 0;
    b->active = (on_ms != 0);
    b->level = (on_ms != 0);
}

uint8_t blink_tick(blink_t *b, uint16_t dt_ms)
{
    if (!b->active || b->off_ms == 0) { /* off, or solid on */
        return b->level;
    }
    b->elapsed_ms = (uint16_t)(b->elapsed_ms + dt_ms);
    if (b->level && b->elapsed_ms >= b->on_ms) {
        b->level = 0;
        b->elapsed_ms = 0;
        if (b->repeat != 0 && --b->remaining == 0) {
            b->active = 0; /* finished the last cycle's on phase; stay off */
        }
    } else if (!b->level && b->elapsed_ms >= b->off_ms) {
        b->level = 1;
        b->elapsed_ms = 0;
    }
    return b->level;
}
