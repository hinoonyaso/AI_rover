/* 한글: 모터 4개 드라이버: PWM(TIM1/9/10/11) + 엔코더(TIM2/3/4/5) + 10ms 제어 틱(TIM7). */
#ifndef DRV_MOTOR_H
#define DRV_MOTOR_H

#include <stdint.h>
#include "core/encoder_motor.h"
#include "FreeRTOS.h"
#include "task.h"

void drv_motor_init(enc_motor_t *motors[4]);
/* Starts the 10 ms TIM7 tick; `t` is notified from the ISR (ulTaskNotifyTake in the control task). */
void drv_motor_start_tick(TaskHandle_t t);
/* Signed pulse +-1000; positive = forward. Respects MOTOR_ENABLE. */
void drv_motor_set_pulse(uint8_t idx, int pulse);
int64_t drv_motor_read_counter(uint8_t idx);
int drv_motor_fault_active(void);
/* Register-only, safe from fault handlers. */
void drv_motor_all_off(void);

#endif
