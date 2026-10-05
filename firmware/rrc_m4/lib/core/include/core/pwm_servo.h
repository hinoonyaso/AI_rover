/* 한글: PWM 서보 위치 램프. 펄스 500~2500us=0~180도, 이동시간 20~30000ms, 오프셋 ±100us. 20ms마다 tick 호출. 벤더 코드가 상향 이동 시 overshoot 하는 부분은 선형 보간으로 고쳤다. */
/* PWM servo position ramp, vendor pwm_servo.c semantics (RRC program analysis 3.6/3.7):
 * pulse 500..2500 us <-> 0..180 deg, move time 20..30000 ms, offset -100..+100 us.
 * pwm_servo_tick() must be called every PWM_SERVO_TICK_MS (the vendor divides time by 20).
 * Deviation from the vendor code: it computes target + inc*remaining, which overshoots on upward
 * moves; this version interpolates linearly from the start value in both directions. */
#ifndef CORE_PWM_SERVO_H
#define CORE_PWM_SERVO_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define PWM_SERVO_TICK_MS 20
#define PWM_SERVO_MIN_US 500
#define PWM_SERVO_MAX_US 2500

typedef struct {
    int offset;
    int target_duty;
    int current_duty;
    int duty_raw;     /* pulse width to output: current_duty + offset */
    uint32_t duration;
    int start_duty;
    int total_ticks;
    int done_ticks;
    uint8_t is_running;
    uint8_t duty_changed;
} pwm_servo_t;

void pwm_servo_init(pwm_servo_t *s);
void pwm_servo_set_position(pwm_servo_t *s, uint32_t duty, uint32_t duration_ms);
void pwm_servo_set_offset(pwm_servo_t *s, int offset);
void pwm_servo_tick(pwm_servo_t *s);

#ifdef __cplusplus
}
#endif
#endif
