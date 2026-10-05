/* 한글: 이 프로젝트 펌웨어에만 있는 확장 FUNC(0x20 상태, 0x21 엔코더 피드백, 0x22 진단 명령, 0x23 원시 HID). 호스트가 몰라도 무시되므로 켜 둬도 안전하다. */
/* Extension FUNCs that exist ONLY in this project's firmware (vendor firmware never sends or
 * accepts them). A host that does not know them ignores unknown FUNCs (jetrover_base counts
 * and drops them), so these are safe to leave enabled in RRC mode.
 *
 *   0x20 STATUS      device -> host, ~10 Hz
 *   0x21 WHEEL       device -> host, ~50 Hz  (encoder feedback the vendor firmware never exposed)
 *   0x22 DIAG_CMD    host -> device
 *   0x23 RAW_HID     device -> host, raw USB gamepad report (to correct the layout guess)
 */
#ifndef RRC_EXT_H
#define RRC_EXT_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define RRC_FUNC_EXT_STATUS 0x20
#define RRC_FUNC_EXT_WHEEL 0x21
#define RRC_FUNC_EXT_DIAG_CMD 0x22
#define RRC_FUNC_EXT_RAW_HID 0x23

/* STATUS flags */
#define RRC_STATUS_ESTOP 0x01
#define RRC_STATUS_MOVING 0x02
#define RRC_STATUS_LOW_BATTERY 0x04
#define RRC_STATUS_MOTOR_ENABLED 0x08
#define RRC_STATUS_MOTOR_FAULT 0x10   /* any wheel latched/driver fault */

typedef struct {
    uint8_t flags;
    uint8_t stop_reason;      /* robot_stop_reason_t */
    uint8_t imu_kind;         /* 0 none, 1 MPU6050, 2 QMI8658 */
    uint8_t comm_mode;        /* 0 RRC, 1 micro-ROS */
    uint8_t motor_fault[4];   /* enc_motor_fault_t per wheel */
    uint32_t uptime_ms;
    uint32_t reset_cause;     /* RCC_CSR flags captured at boot (0 if unknown) */
} rrc_ext_status_t;
#define RRC_EXT_STATUS_LEN 16
size_t rrc_ext_pack_status(const rrc_ext_status_t *s, uint8_t *data_out);

typedef struct {
    float rps[4];
    int32_t counter[4];
} rrc_ext_wheel_t;
#define RRC_EXT_WHEEL_LEN 32
size_t rrc_ext_pack_wheel(const rrc_ext_wheel_t *w, uint8_t *data_out);

/* DIAG_CMD subcommands */
typedef enum {
    RRC_DIAG_CLEAR_ESTOP = 0x01,   /* [] */
    RRC_DIAG_ESTOP = 0x02,         /* [] */
    RRC_DIAG_SET_TIMEOUT = 0x03,   /* [u16 ms] 0 disables */
    RRC_DIAG_SET_PID = 0x04,       /* [motor u8, kp f32, ki f32, kd f32]; motor 0xFF = all */
    RRC_DIAG_RAW_PWM = 0x05,       /* [motor u8, i16 pulse] open-loop, wheels lifted only, auto-expires */
    RRC_DIAG_REQUEST_STATUS = 0x06 /* [] */
} rrc_diag_sub_t;
typedef struct {
    uint8_t subcommand;
    uint16_t timeout_ms;
    uint8_t motor;
    float kp, ki, kd;
    int16_t pulse;
} rrc_diag_cmd_t;
/* Returns 1 if valid. */
int rrc_ext_unpack_diag(const uint8_t *data, uint8_t len, rrc_diag_cmd_t *out);

/* Raw HID: [len u8, report bytes...], truncated to 32 bytes. Returns data length. */
size_t rrc_ext_pack_raw_hid(const uint8_t *report, size_t len, uint8_t *data_out);

#ifdef __cplusplus
}
#endif
#endif
