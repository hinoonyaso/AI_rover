/* 한글: 모든 통신 계층(micro-ROS, RRC, 게임패드, SBUS)이 공유하는 로봇 제어 API. 통신 코드는 모터를 직접 만지지 않고 이 함수들만 호출한다. 명령 timeout, e-stop 래치, 저전압 차단, 바퀴 runaway 시 전체 정지를 여기서 처리한다. */
/* Robot control API shared by every communication layer (micro-ROS, RRC, gamepad, SBUS).
 * Communication code must only call these functions; it never touches motors directly.
 * This module knows nothing about any wire protocol (architecture rule from the PRD).
 *
 * Safety handled here, independent of the host:
 *  - command timeout: wheels stop if no motion command arrives within timeout_ms
 *  - emergency stop latch (until robot_clear_estop)
 *  - low-battery cutoff with hysteresis
 *  - latched encoder runaway on any wheel stops all wheels
 *  - non-finite (NaN/Inf) motion commands are dropped (2026-10-10)
 *  - one command source at a time: the source that started moving owns the wheels until it stops or its
 *    commands time out; motion commands from any other source are rejected meanwhile. Stop and e-stop are
 *    always accepted from anyone (2026-10-10, micro-ROS + RRC fallback must never fight over the wheels).
 * 한글: NaN/Inf 명령 폐기, 한 번에 한 출처만 제어(정지·e-stop은 누구든 가능).
 */
#ifndef CORE_ROBOT_CTRL_H
#define CORE_ROBOT_CTRL_H

#include <stdint.h>
#include "core/encoder_motor.h"
#include "core/mecanum.h"

#ifdef __cplusplus
extern "C" {
#endif

#define ROBOT_NUM_MOTORS 4
#define ROBOT_DEFAULT_CMD_TIMEOUT_MS 1000u

typedef enum {
    ROBOT_SRC_NONE = 0,
    ROBOT_SRC_MICROROS,
    ROBOT_SRC_RRC,
    ROBOT_SRC_GAMEPAD,
    ROBOT_SRC_SBUS,
    ROBOT_SRC_BLUETOOTH,
    ROBOT_SRC_INTERNAL,
} robot_cmd_source_t;

typedef enum {
    ROBOT_STOP_NONE = 0,
    ROBOT_STOP_TIMEOUT,
    ROBOT_STOP_ESTOP,
    ROBOT_STOP_LOW_BATTERY,
    ROBOT_STOP_MOTOR_FAULT,
    ROBOT_STOP_COMMAND,
} robot_stop_reason_t;

typedef struct {
    enc_motor_t *motors[ROBOT_NUM_MOTORS];
    mecanum_cfg_t mecanum;
    uint32_t cmd_timeout_ms;      /* 0 disables the timeout (not recommended) */
    uint16_t low_battery_mv;      /* cutoff, 0 disables */
    uint16_t low_battery_clear_mv;/* hysteresis release level */
    uint8_t enabled;              /* 0: every command is ignored (MOTOR_ENABLE build flag off) */

    uint32_t last_cmd_ms;
    uint8_t moving;
    uint8_t estop;
    uint8_t low_battery;
    uint8_t last_source;
    uint8_t stop_reason;
    uint8_t owner;                /* robot_cmd_source_t holding the wheels, NONE when stopped */
    uint32_t rejected_cmds;       /* motion commands refused (other source / non-finite) */
} robot_ctrl_t;

void robot_init(robot_ctrl_t *rc, enc_motor_t *motors[ROBOT_NUM_MOTORS], const mecanum_cfg_t *mecanum,
                uint8_t enabled);

/* Body velocity (m/s, m/s, rad/s) -> wheel targets via mecanum_inverse.
 * Returns 0 if applied, -1 if refused (not accepting, non-finite input, or another source owns the wheels). */
int robot_set_velocity(robot_ctrl_t *rc, float vx, float vy, float wz, uint32_t now_ms, robot_cmd_source_t src);
/* Direct per-wheel target in rev/s (RRC FUNC3 path). id is 0-based. Same return as robot_set_velocity. */
int robot_set_wheel_rps(robot_ctrl_t *rc, uint8_t id, float rps, uint32_t now_ms, robot_cmd_source_t src);
void robot_stop(robot_ctrl_t *rc, robot_stop_reason_t reason);
/* RRC FUNC3 subcommands 0x02 (single) / 0x03 (bit mask). */
void robot_stop_mask(robot_ctrl_t *rc, uint8_t mask);
void robot_estop(robot_ctrl_t *rc);
void robot_clear_estop(robot_ctrl_t *rc);
void robot_update_battery(robot_ctrl_t *rc, uint16_t millivolts);
/* Call every ~10 ms from the control task (not from an interrupt). */
void robot_tick(robot_ctrl_t *rc, uint32_t now_ms);

#ifdef __cplusplus
}
#endif
#endif
