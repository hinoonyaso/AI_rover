/* 한글: 배터리 ADC, LED/부저/버튼, 부팅 시 안전 GPIO, PWM 서보(TIM13 소프트웨어 PWM) 드라이버. */
#ifndef DRV_MISC_H
#define DRV_MISC_H

#include <stdint.h>

/* ---- battery ADC (ADC1 IN8 = PB0, IN17 = Vrefint, DMA2 stream 0) ---- */
void drv_battery_init(void);
/* Starts a conversion pair; results valid ~100 us later. */
void drv_battery_trigger(void);
void drv_battery_get(uint16_t *vrefint_counts, uint16_t *pb0_counts);

/* ---- LED / buzzer / buttons ---- */
void drv_ui_gpio_init(void);
void drv_led_write(int on);
void drv_buzzer_write(int on);
int drv_key_pressed(uint8_t key_index); /* 0 = PE0, 1 = PE1 */

/* ---- boot-time GPIO states copied from the stock firmware (PINMAP.md) ---- */
void drv_gpio_safe_init(void);

/* ---- PWM servos (TIM13 software PWM, lazy start) ---- */
void drv_pwm_servo_init(void);
void drv_pwm_servo_set_pulse(uint8_t idx, uint16_t pulse_us);
void drv_pwm_servo_enable(void); /* idempotent: first call starts TIM13 */

#endif
