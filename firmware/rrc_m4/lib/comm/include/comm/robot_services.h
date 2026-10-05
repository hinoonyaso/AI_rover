/* 한글: 통신 계층이 하드웨어에 요청하는 서비스 표(LED/부저/서보/진단 등). 통신 계층은 주변장치를 직접 만지지 않고 이 표만 쓴다. 호스트 시험에서는 mock으로 대체한다. */
/* Hardware-facing services shared by every communication layer (RRC adapter, micro-ROS node).
 * The application fills this table with real drivers (target) or mocks (host tests); a comm layer
 * never talks to a peripheral directly. Callbacks may be NULL when a feature is not built in. */
#ifndef COMM_ROBOT_SERVICES_H
#define COMM_ROBOT_SERVICES_H

#include <stdint.h>
#include "core/bus_servo.h"
#include "core/robot_ctrl.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    robot_ctrl_t *robot;
    void *hw;

    uint32_t (*now_ms)(void *hw);
    void (*led_set)(void *hw, uint8_t id, uint16_t on_ms, uint16_t off_ms, uint16_t cycles);
    void (*buzzer_set)(void *hw, uint16_t freq_hz, uint16_t on_ms, uint16_t off_ms, uint16_t cycles);

    /* PWM servos: idx 0..3 (host ids are 1-based). */
    void (*pwm_servo_move)(void *hw, uint8_t idx, uint16_t pulse_us, uint16_t time_ms);
    int (*pwm_servo_get_pulse)(void *hw, uint8_t idx, uint16_t *pulse_us);
    void (*pwm_servo_set_offset)(void *hw, uint8_t idx, int8_t offset);
    int (*pwm_servo_get_offset)(void *hw, uint8_t idx, int8_t *offset);

    /* Bus servos (blocking half-duplex transaction, ~ms). Returns 0 on success. */
    void (*bus_servo_move)(void *hw, uint8_t id, uint16_t pulse, uint16_t time_ms);
    int (*bus_servo_xfer)(void *hw, const bus_servo_plan_t *plan, uint8_t *reply, uint8_t *reply_len);

    /* Diagnostics */
    void (*set_pid)(void *hw, uint8_t motor, float kp, float ki, float kd); /* motor 0xFF = all */
    void (*raw_pwm)(void *hw, uint8_t motor, int16_t pulse);
    void (*request_status)(void *hw);
} robot_services_t;

#ifdef __cplusplus
}
#endif
#endif
