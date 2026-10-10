/* 한글: 로봇 제어 API 구현: 명령 수락 조건(enabled, estop 아님, 저전압 아님), 명령 timeout, 바퀴 fault 시 전체 정지. */
#include "core/robot_ctrl.h"

#include <math.h>

void robot_init(robot_ctrl_t *rc, enc_motor_t *motors[ROBOT_NUM_MOTORS], const mecanum_cfg_t *mecanum,
                uint8_t enabled)
{
    for (int i = 0; i < ROBOT_NUM_MOTORS; ++i) {
        rc->motors[i] = motors[i];
    }
    rc->mecanum = *mecanum;
    rc->cmd_timeout_ms = ROBOT_DEFAULT_CMD_TIMEOUT_MS;
    rc->low_battery_mv = 9500;
    rc->low_battery_clear_mv = 10000;
    rc->enabled = enabled;
    rc->last_cmd_ms = 0;
    rc->moving = 0;
    rc->estop = 0;
    rc->low_battery = 0;
    rc->last_source = ROBOT_SRC_NONE;
    rc->stop_reason = ROBOT_STOP_NONE;
    rc->owner = ROBOT_SRC_NONE;
    rc->rejected_cmds = 0;
}

/* 한글: 명령을 받아도 되는 상태인가: 모터 활성 + e-stop 아님 + 저전압 아님. */
static int accepting(const robot_ctrl_t *rc)
{
    return rc->enabled && !rc->estop && !rc->low_battery;
}

static void note_command(robot_ctrl_t *rc, uint32_t now_ms, robot_cmd_source_t src)
{
    rc->last_cmd_ms = now_ms;
    rc->last_source = (uint8_t)src;
    rc->owner = (uint8_t)src;
    rc->moving = 1;
    rc->stop_reason = ROBOT_STOP_NONE;
}

/* 한글: 다른 출처가 바퀴를 쥐고 있고(이동 중) 그 명령이 아직 timeout 전이면 거부. */
static int owned_by_other(const robot_ctrl_t *rc, uint32_t now_ms, robot_cmd_source_t src)
{
    if (rc->owner == ROBOT_SRC_NONE || rc->owner == (uint8_t)src || !rc->moving) {
        return 0;
    }
    if (rc->cmd_timeout_ms != 0 && (uint32_t)(now_ms - rc->last_cmd_ms) > rc->cmd_timeout_ms) {
        return 0; /* the owner went silent; robot_tick stops it on the next tick anyway */
    }
    return 1;
}

int robot_set_velocity(robot_ctrl_t *rc, float vx, float vy, float wz, uint32_t now_ms, robot_cmd_source_t src)
{
    float rps[ROBOT_NUM_MOTORS];

    if (!accepting(rc)) {
        return -1;
    }
    if (!isfinite(vx) || !isfinite(vy) || !isfinite(wz) || owned_by_other(rc, now_ms, src)) {
        rc->rejected_cmds++;
        return -1; /* not a command: the timeout keeps running / 명령으로 치지 않음 */
    }
    mecanum_inverse(&rc->mecanum, vx, vy, wz, rps);
    for (int i = 0; i < ROBOT_NUM_MOTORS; ++i) {
        (void)enc_motor_set_speed(rc->motors[i], rps[i]);
    }
    note_command(rc, now_ms, src);
    return 0;
}

int robot_set_wheel_rps(robot_ctrl_t *rc, uint8_t id, float rps, uint32_t now_ms, robot_cmd_source_t src)
{
    if (id >= ROBOT_NUM_MOTORS || !accepting(rc)) {
        return -1;
    }
    if (!isfinite(rps) || owned_by_other(rc, now_ms, src)) {
        rc->rejected_cmds++;
        return -1;
    }
    (void)enc_motor_set_speed(rc->motors[id], rps);
    note_command(rc, now_ms, src);
    return 0;
}

void robot_stop(robot_ctrl_t *rc, robot_stop_reason_t reason)
{
    for (int i = 0; i < ROBOT_NUM_MOTORS; ++i) {
        enc_motor_stop(rc->motors[i]);
    }
    rc->moving = 0;
    rc->owner = ROBOT_SRC_NONE; /* any stop releases the wheels / 정지하면 제어권 해제 */
    rc->stop_reason = (uint8_t)reason;
}

void robot_stop_mask(robot_ctrl_t *rc, uint8_t mask)
{
    if ((mask & 0x0F) == 0x0F) { /* every wheel: a complete stop, so release the wheels too (2026-10-10 review) */
        robot_stop(rc, ROBOT_STOP_COMMAND);
        return;
    }
    for (int i = 0; i < ROBOT_NUM_MOTORS; ++i) {
        if (mask & (1u << i)) {
            enc_motor_stop(rc->motors[i]);
        }
    }
}

void robot_estop(robot_ctrl_t *rc)
{
    rc->estop = 1;
    robot_stop(rc, ROBOT_STOP_ESTOP);
}

void robot_clear_estop(robot_ctrl_t *rc)
{
    rc->estop = 0;
    for (int i = 0; i < ROBOT_NUM_MOTORS; ++i) {
        enc_motor_clear_fault(rc->motors[i]);
    }
    rc->stop_reason = ROBOT_STOP_NONE;
}

/* 한글: 저전압 차단(히스테리시스: 9.5V 미만 차단, 10.0V 이상에서 해제). */
void robot_update_battery(robot_ctrl_t *rc, uint16_t millivolts)
{
    if (rc->low_battery_mv == 0 || millivolts == 0) {
        return;
    }
    if (!rc->low_battery && millivolts < rc->low_battery_mv) {
        rc->low_battery = 1;
        robot_stop(rc, ROBOT_STOP_LOW_BATTERY);
    } else if (rc->low_battery && millivolts >= rc->low_battery_clear_mv) {
        rc->low_battery = 0;
    }
}

/* 한글: 10ms 주기 호출: 바퀴 하나라도 runaway면 전체 정지, 명령이 timeout보다 오래 끊기면 정지. */
void robot_tick(robot_ctrl_t *rc, uint32_t now_ms)
{
    for (int i = 0; i < ROBOT_NUM_MOTORS; ++i) {
        if (rc->motors[i]->fault == ENC_MOTOR_FAULT_RUNAWAY) {
            robot_stop(rc, ROBOT_STOP_MOTOR_FAULT); /* never keep driving the other wheels */
            return;
        }
    }
    if (rc->moving && rc->cmd_timeout_ms != 0 && (uint32_t)(now_ms - rc->last_cmd_ms) > rc->cmd_timeout_ms) {
        robot_stop(rc, ROBOT_STOP_TIMEOUT);
    }
}
