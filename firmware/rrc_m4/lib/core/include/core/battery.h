/* 한글: 배터리 전압: ADC1의 Vrefint와 PB0 값으로 mV 계산(1210/adc0*adc1*11), 0.95/0.05 필터, 20V 초과/0/4095 거부. FUNC0에 실리는 값. */
/* Battery voltage from the ADC1 pair the vendor samples (RRC program analysis 3.4):
 *   adc[0] = internal Vrefint (nominally 1.21 V), adc[1] = PB0 divider tap,
 *   volt_mV = 1210 / adc[0] * adc[1] * 11  (12-bit, 1:11 divider), values 0 / 4095 rejected,
 * low-pass filtered (0.95/0.05, called every 50 ms). This is the value reported in FUNC0 (04 + u16 LE mV). */
#ifndef CORE_BATTERY_H
#define CORE_BATTERY_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    float filtered_mv;
    uint16_t millivolts;
    uint8_t valid;
} battery_t;

void battery_init(battery_t *b);
/* Returns 1 if the sample was accepted. */
int battery_update(battery_t *b, uint16_t adc_vrefint, uint16_t adc_pb0);

#ifdef __cplusplus
}
#endif
#endif
