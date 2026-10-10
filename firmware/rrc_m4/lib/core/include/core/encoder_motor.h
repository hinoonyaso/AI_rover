/* 한글: 엔코더 모터: 속도 측정 + 증분 PID + PWM 클램프/데드존. 벤더에 없던 드라이버 fault 입력과 runaway(엔코더 부호 오류/막힘) 래치를 추가했다. */
/* Encoder motor object: speed measurement + incremental PID + PWM clamp/dead zone,
 * reconstructed from Hiwonder's encoder_motor.c (RRC program analysis 3.10/3.11) and
 * cross-checked against the decompiled FUN_0800befc (control) / FUN_0800bfe0 (update).
 * Unlike the vendor code this adds guards the vendor lacks: a motor-driver fault input,
 * and a runaway/stall latch (wrong encoder polarity would otherwise be positive feedback).
 */
#ifndef CORE_ENCODER_MOTOR_H
#define CORE_ENCODER_MOTOR_H

#include <stdint.h>
#include "core/pid.h"

#ifdef __cplusplus
extern "C" {
#endif

#define ENC_MOTOR_PWM_LIMIT 1000.0f
#define ENC_MOTOR_PWM_DEAD_ZONE 250.0f

/* Runaway/stall guard: set point is demanding (>= GUARD_MIN_RPS) while the PWM has been
 * pinned near the limit and the measured speed is not following for this many periods. */
#define ENC_MOTOR_GUARD_MIN_RPS 0.3f
#define ENC_MOTOR_GUARD_PULSE 900.0f
#define ENC_MOTOR_GUARD_TICKS 100 /* 1 s at the 10 ms control period */
/* Encoder-sign guard (2026-10-10 bring-up: a wrong ENCODER_SIGN made the PID accelerate a coasting
 * wheel to full PWM at set point 0, which the stall guard above never sees). A driven wheel must turn
 * the way it is pushed: |pulse| >= 600 while the measured speed is >= 1 rps the OTHER way and not
 * slowing down for 200 ms -> latch RUNAWAY. Normal reversals decelerate, so they do not count.
 * 한글: 큰 PWM과 반대 방향으로 1 rps 넘게 돌면서 감속하지 않는 상태가 200 ms면 래치(엔코더 부호 오류). */
#define ENC_MOTOR_SIGN_GUARD_PULSE 600.0f
#define ENC_MOTOR_SIGN_GUARD_RPS 1.0f
#define ENC_MOTOR_SIGN_GUARD_TICKS 20

typedef enum {
    ENC_MOTOR_FAULT_NONE = 0,
    ENC_MOTOR_FAULT_DRIVER = 1,   /* driver fault pin asserted (not latched, follows the pin) */
    ENC_MOTOR_FAULT_RUNAWAY = 2,  /* latched: speed not following command (polarity/stall) */
} enc_motor_fault_t;

typedef struct enc_motor enc_motor_t;
struct enc_motor {
    int64_t counter;        /* total count including overflows */
    int64_t overflow_num;   /* timer wrap count (+1 up, -1 down) */
    int32_t ticks_overflow; /* timer auto-reload used as the wrap value (60000 on this board) */
    float tps;              /* ticks per second (low-pass filtered) */
    float rps;              /* output shaft revolutions per second */
    int32_t ticks_per_circle;
    float rps_limit;
    float current_pulse;
    int8_t encoder_sign;    /* +1 / -1, set per motor in the board config */
    rrc_pid_t pid;
    void (*set_pulse)(void *ctx, int pulse); /* signed, +-ENC_MOTOR_PWM_LIMIT */
    void *ctx;
    uint8_t fault;          /* enc_motor_fault_t */
    uint16_t guard_count;
    uint16_t sign_guard_count;
    float sign_guard_last_rps; /* |rps| at the previous tick, to tell braking from runaway */
};

void enc_motor_init(enc_motor_t *m, int32_t ticks_per_circle, float rps_limit,
                    float kp, float ki, float kd, int32_t ticks_overflow, int8_t encoder_sign,
                    void (*set_pulse)(void *ctx, int pulse), void *ctx);
/* Returns 0 on success, -1 if a latched fault refuses the command. Clamped to +-rps_limit. */
int enc_motor_set_speed(enc_motor_t *m, float rps);
void enc_motor_stop(enc_motor_t *m);
void enc_motor_clear_fault(enc_motor_t *m);
/* hw_counter: raw timer count (0..ticks_overflow). Call every `period` seconds. */
void enc_motor_update(enc_motor_t *m, float period, int64_t hw_counter);
/* Timer overflow/underflow interrupt. */
void enc_motor_on_overflow(enc_motor_t *m, int counting_down);
/* driver_fault: nonzero when the motor driver reports a fault. Call every `period` seconds. */
void enc_motor_control(enc_motor_t *m, float period, int driver_fault);

#ifdef __cplusplus
}
#endif
#endif
