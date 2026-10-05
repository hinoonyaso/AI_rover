/* 한글: 엔코더 모터 구현: 속도 필터 0.9/0.1, 데드존 ±250, 클램프 ±1000, runaway 래치(속도 명령이 큰데 PWM이 포화 근처에서 1초 넘게 속도가 안 따라오면 정지). */
#include "core/encoder_motor.h"
#include <math.h>

void enc_motor_init(enc_motor_t *m, int32_t ticks_per_circle, float rps_limit,
                    float kp, float ki, float kd, int32_t ticks_overflow, int8_t encoder_sign,
                    void (*set_pulse)(void *ctx, int pulse), void *ctx)
{
    m->counter = 0;
    m->overflow_num = 0;
    m->ticks_overflow = ticks_overflow;
    m->tps = 0.0f;
    m->rps = 0.0f;
    m->ticks_per_circle = ticks_per_circle;
    m->rps_limit = rps_limit;
    m->current_pulse = 0.0f;
    m->encoder_sign = encoder_sign < 0 ? -1 : 1;
    rrc_pid_init(&m->pid, kp, ki, kd);
    m->set_pulse = set_pulse;
    m->ctx = ctx;
    m->fault = ENC_MOTOR_FAULT_NONE;
    m->guard_count = 0;
}

int enc_motor_set_speed(enc_motor_t *m, float rps)
{
    if (m->fault == ENC_MOTOR_FAULT_RUNAWAY) {
        return -1;
    }
    /* 한글: NaN(잘못된 패킷)은 PID에 절대 들어가지 않게 0으로 바꾼다. */
    if (!(rps == rps)) { /* NaN from a bad packet must never reach the PID */
        rps = 0.0f;
    }
    if (rps > m->rps_limit) {
        rps = m->rps_limit;
    } else if (rps < -m->rps_limit) {
        rps = -m->rps_limit;
    }
    m->pid.set_point = rps;
    return 0;
}

void enc_motor_stop(enc_motor_t *m)
{
    m->pid.set_point = 0.0f;
    rrc_pid_reset(&m->pid);
    m->current_pulse = 0.0f;
    m->guard_count = 0;
    if (m->set_pulse) {
        m->set_pulse(m->ctx, 0);
    }
}

void enc_motor_clear_fault(enc_motor_t *m)
{
    m->fault = ENC_MOTOR_FAULT_NONE;
    m->guard_count = 0;
    enc_motor_stop(m);
}

void enc_motor_on_overflow(enc_motor_t *m, int counting_down)
{
    m->overflow_num += counting_down ? -1 : 1;
}

/* 한글: 엔코더 카운트로 속도(rps) 갱신. 전체 카운트 = 하드웨어 카운터 + 오버플로 횟수×60000, 부호는 모터별 encoder_sign으로 보정한다. */
void enc_motor_update(enc_motor_t *m, float period, int64_t hw_counter)
{
    int64_t total = hw_counter + m->overflow_num * (int64_t)m->ticks_overflow;
    total *= m->encoder_sign;
    const int64_t delta = total - m->counter;
    m->counter = total;
    m->tps = (float)delta / period * 0.9f + m->tps * 0.1f; /* vendor 0.9/0.1 low-pass */
    m->rps = m->tps / (float)m->ticks_per_circle;
}

/* 한글: PID 한 스텝: 드라이버 fault면 출력 0, 아니면 현재 PWM에 PID 출력을 더해 ±1000으로 클램프, ±250 데드존은 0으로 만든다. */
void enc_motor_control(enc_motor_t *m, float period, int driver_fault)
{
    float pulse = 0.0f;

    if (m->fault == ENC_MOTOR_FAULT_RUNAWAY) {
        m->current_pulse = 0.0f;
        m->set_pulse(m->ctx, 0);
        return;
    }
    if (driver_fault) {
        m->fault = ENC_MOTOR_FAULT_DRIVER; /* vendor behaviour: output forced to 0, PID frozen */
    } else {
        if (m->fault == ENC_MOTOR_FAULT_DRIVER) {
            m->fault = ENC_MOTOR_FAULT_NONE;
        }
        rrc_pid_update(&m->pid, m->rps, period);
        pulse = m->current_pulse + m->pid.output;
        if (pulse > ENC_MOTOR_PWM_LIMIT) {
            pulse = ENC_MOTOR_PWM_LIMIT;
        }
        if (pulse < -ENC_MOTOR_PWM_LIMIT) {
            pulse = -ENC_MOTOR_PWM_LIMIT;
        }
    }

    /* 한글: 폭주/막힘 감시. 속도 명령이 큰데 PWM이 포화 근처이고 실제 속도가 명령 방향으로 10%도 안 되는 상태가 100틱(1초) 이어지면 래치한다. */
    /* Runaway/stall guard. */
    if (fabsf(m->pid.set_point) >= ENC_MOTOR_GUARD_MIN_RPS && fabsf(pulse) >= ENC_MOTOR_GUARD_PULSE &&
        m->rps * m->pid.set_point < 0.1f * m->pid.set_point * m->pid.set_point) {
        if (++m->guard_count >= ENC_MOTOR_GUARD_TICKS) {
            m->fault = ENC_MOTOR_FAULT_RUNAWAY;
            m->current_pulse = 0.0f;
            m->set_pulse(m->ctx, 0);
            return;
        }
    } else {
        m->guard_count = 0;
    }

    const float out = (fabsf(pulse) < ENC_MOTOR_PWM_DEAD_ZONE) ? 0.0f : pulse;
    m->set_pulse(m->ctx, (int)out);
    m->current_pulse = pulse;
}
