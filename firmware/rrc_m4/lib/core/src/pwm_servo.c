/* 한글: PWM 서보 램프 구현. */
#include "core/pwm_servo.h"

void pwm_servo_init(pwm_servo_t *s)
{
    s->offset = 0;
    s->target_duty = 1500;
    s->current_duty = 1500;
    s->duty_raw = 1500;
    s->duration = 0;
    s->start_duty = 1500;
    s->total_ticks = 0;
    s->done_ticks = 0;
    s->is_running = 0;
    s->duty_changed = 0;
}

void pwm_servo_set_position(pwm_servo_t *s, uint32_t duty, uint32_t duration_ms)
{
    duration_ms = duration_ms < 20 ? 20 : (duration_ms > 30000 ? 30000 : duration_ms);
    duty = duty > PWM_SERVO_MAX_US ? PWM_SERVO_MAX_US : (duty < PWM_SERVO_MIN_US ? PWM_SERVO_MIN_US : duty);
    s->target_duty = (int)duty;
    s->duration = duration_ms;
    s->duty_changed = 1;
}

void pwm_servo_set_offset(pwm_servo_t *s, int offset)
{
    s->offset = offset < -100 ? -100 : (offset > 100 ? 100 : offset);
}

/* 한글: 20ms마다 호출: 시작값에서 목표값까지 선형 보간(상향/하향 모두 단조). */
void pwm_servo_tick(pwm_servo_t *s)
{
    if (s->duty_changed) {
        s->duty_changed = 0;
        s->start_duty = s->current_duty;
        s->total_ticks = (int)(s->duration / PWM_SERVO_TICK_MS); /* >= 1 because duration >= 20 */
        s->done_ticks = 0;
        s->is_running = 1;
    }
    if (s->is_running) {
        if (++s->done_ticks >= s->total_ticks) {
            s->current_duty = s->target_duty;
            s->is_running = 0;
        } else {
            s->current_duty = s->start_duty + (int)((float)(s->target_duty - s->start_duty) *
                                                    (float)s->done_ticks / (float)s->total_ticks);
        }
    }
    s->duty_raw = s->current_duty + s->offset;
}
