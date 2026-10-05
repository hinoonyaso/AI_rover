/* 한글: 버스 서보(USART6 반이중) 드라이버. 방향 제어 핀 역할이 추정이라 실패 시 4가지 조합을 자동 탐색한다. */
#ifndef DRV_BUS_SERVO_H
#define DRV_BUS_SERVO_H

#include <stdint.h>
#include "core/bus_servo.h"

void drv_bus_servo_init(void);
void drv_bus_servo_move(uint8_t id, uint16_t pulse, uint16_t time_ms);
/* Blocking transaction. Returns 0 on success (reply filled when the plan expects one). */
int drv_bus_servo_xfer(const bus_servo_plan_t *plan, uint8_t *reply, uint8_t *reply_len);

#endif
