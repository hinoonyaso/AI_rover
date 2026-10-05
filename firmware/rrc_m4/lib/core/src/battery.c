/* 한글: 배터리 mV 변환/필터 구현. */
#include "core/battery.h"

void battery_init(battery_t *b)
{
    b->filtered_mv = 0.0f;
    b->millivolts = 0;
    b->valid = 0;
}

int battery_update(battery_t *b, uint16_t adc_vrefint, uint16_t adc_pb0)
{
    if (adc_vrefint == 0 || adc_vrefint == 4095 || adc_pb0 == 0 || adc_pb0 == 4095) {
        return 0;
    }
    const float mv = 1210.0f / (float)adc_vrefint * (float)adc_pb0 * 11.0f;
    if (mv > 20000.0f) { /* vendor: a car battery never exceeds 20 V, treat as a bad sample */
        return 0;
    }
    if (!b->valid) {
        b->filtered_mv = mv;
        b->valid = 1;
    } else {
        b->filtered_mv = b->filtered_mv * 0.95f + mv * 0.05f;
    }
    b->millivolts = (uint16_t)(b->filtered_mv + 0.5f);
    return 1;
}
