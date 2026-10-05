/* 한글: 증분형 PID 구현(헤더 설명 참고). */
#include "core/pid.h"

void rrc_pid_init(rrc_pid_t *pid, float kp, float ki, float kd)
{
    pid->set_point = 0.0f;
    pid->kp = kp;
    pid->ki = ki;
    pid->kd = kd;
    rrc_pid_reset(pid);
}

void rrc_pid_reset(rrc_pid_t *pid)
{
    pid->previous_0_err = 0.0f;
    pid->previous_1_err = 0.0f;
    pid->output = 0.0f;
}

void rrc_pid_update(rrc_pid_t *pid, float actual, float time_delta)
{
    const float err = pid->set_point - actual;
    const float integral = err * time_delta;
    const float derivative = (err - 2.0f * pid->previous_1_err + pid->previous_0_err) / time_delta;

    pid->output = (pid->kp * err) + (pid->ki * integral) + (pid->kd * derivative);
    pid->previous_1_err = pid->previous_0_err;
    pid->previous_0_err = err;
}
