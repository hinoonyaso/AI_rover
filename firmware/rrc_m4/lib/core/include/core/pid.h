/* 한글: 증분형 속도 PID(Hiwonder pid.c와 동일 수식). 출력은 "현재 PWM에 더할 변화량"이다. */
/* Incremental speed PID exactly as in Hiwonder's pid.c (RRC program analysis 3.11):
 * output is a *delta* that encoder_motor adds to the current pulse every period. */
#ifndef CORE_PID_H
#define CORE_PID_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    float set_point;
    float kp, ki, kd;
    float previous_0_err;
    float previous_1_err;
    float output;
} rrc_pid_t;

void rrc_pid_init(rrc_pid_t *pid, float kp, float ki, float kd);
void rrc_pid_reset(rrc_pid_t *pid);
void rrc_pid_update(rrc_pid_t *pid, float actual, float time_delta);

#ifdef __cplusplus
}
#endif
#endif
