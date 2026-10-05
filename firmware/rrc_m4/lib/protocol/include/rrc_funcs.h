// 한글: FUNC별 pack/unpack 헬퍼. 바이트 배치는 공식 PDF와 실기 캡처 기준이며 정수는 모두 리틀엔디안이다.
/* Per-FUNC pack/unpack helpers on top of rrc_protocol.h's generic frame codec.
 * Byte layouts are taken verbatim from firmware_source/"RRC Communication
 * Protocol with the Host Computer Analysis.pdf" (FUNC 1-9) plus the
 * empirically reverse-engineered FUNC 0 (battery, not in the vendor PDF) —
 * see firmware_source/BOARD_CONNECTORS.md for what's confirmed vs assumed.
 * All multi-byte integers are little-endian, matching the PDF's own examples.
 *
 * Bus servo (FUNC5) subcommands beyond move(0x01)/read-position(0x05) are
 * handled by lib/core bus_servo.c (bus_servo_plan_from_rrc / bus_servo_make_upload), whose layouts
 * come from the official docs repo (program analysis 3.14.2, 2026-10-05).
 *
 * PWM servo (FUNC4) deviation upload: the PDF text for "(2) PWM servo
 * deviation upload" shows subcommand byte 0x05, identical to the position
 * upload's subcommand -- almost certainly a copy/paste artifact in the PDF
 * (the read-deviation *request* uses 0x09; set-deviation request is 0x07, confirmed by the
 * official docs repo). The upload byte stays 0x05 as in the docs. rrc_unpack_pwm_servo_upload()
 * disambiguates by length (4 bytes = position, 3 bytes = deviation) and
 * ignores the subcommand byte's exact value for the deviation case. Verify
 * against a real capture before relying on this for calibration.
 */
#ifndef RRC_FUNCS_H
#define RRC_FUNCS_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ---- FUNC 0x00: battery/system (device -> host, encode only) ---- */
/* data_out must have room for 3 bytes. Returns data_len (3). */
// 한글: FUNC0 배터리(장치→호스트, 인코딩만).
size_t rrc_pack_battery_mv(uint16_t millivolts, uint8_t *data_out);

/* ---- FUNC 0x01: LED (host -> device, decode) ---- */
typedef struct {
    uint8_t led_id;
    uint16_t on_ms;
    uint16_t off_ms;
    uint16_t cycles;
} rrc_led_cmd_t;
// 한글: FUNC1 LED(호스트→장치, 디코드).
int rrc_unpack_led(const uint8_t *data, uint8_t len, rrc_led_cmd_t *out);

/* ---- FUNC 0x02: buzzer (host -> device, decode) ---- */
typedef struct {
    uint16_t freq_hz;
    uint16_t on_ms;
    uint16_t off_ms;
    uint16_t cycles;
} rrc_buzzer_cmd_t;
int rrc_unpack_buzzer(const uint8_t *data, uint8_t len, rrc_buzzer_cmd_t *out);

/* ---- FUNC 0x03: motor (host -> device, decode) ---- */
#define RRC_MOTOR_MAX_COUNT 8
typedef struct {
    uint8_t id;   /* 0-based wire id */
    float rps;
} rrc_motor_speed_t;
typedef struct {
    uint8_t subcommand; /* 0x01 = set speeds (the only one implemented) */
    uint8_t count;
    rrc_motor_speed_t speeds[RRC_MOTOR_MAX_COUNT];
} rrc_motor_cmd_t;
/* Returns 1 on success, 0 on malformed frame or count > RRC_MOTOR_MAX_COUNT. */
// 한글: FUNC3 모터 다중 설정(서브커맨드 0x01). 모터 ID는 0부터. 다른 서브커맨드는 rrc_unpack_motor_ex.
int rrc_unpack_motor(const uint8_t *data, uint8_t len, rrc_motor_cmd_t *out);

/* FUNC3 full subcommand set (PDF 3.14.2 / program analysis 3.14): 0x00 single, 0x01 multi,
 * 0x02 stop one, 0x03 stop by bit mask. Use rrc_unpack_motor_ex for any of them. */
typedef enum {
    RRC_MOTOR_SUB_SET_SINGLE = 0x00,
    RRC_MOTOR_SUB_SET_MULTI = 0x01,
    RRC_MOTOR_SUB_STOP_ONE = 0x02,
    RRC_MOTOR_SUB_STOP_MASK = 0x03,
} rrc_motor_sub_t;
typedef struct {
    uint8_t subcommand;
    uint8_t count;                                 /* valid for SET_SINGLE (1) / SET_MULTI */
    rrc_motor_speed_t speeds[RRC_MOTOR_MAX_COUNT];
    uint8_t stop_id;                               /* STOP_ONE */
    uint8_t stop_mask;                             /* STOP_MASK, bit i = motor id i */
} rrc_motor_cmd_ex_t;
int rrc_unpack_motor_ex(const uint8_t *data, uint8_t len, rrc_motor_cmd_ex_t *out);

/* ---- FUNC 0x04/0x05 subcommand bytes (Parameter 1 in the PDF) ---- */
#define RRC_SERVO_SUB_MOVE_MULTI 0x01
#define RRC_SERVO_SUB_MOVE_SINGLE 0x03 /* PWM servo only */
#define RRC_SERVO_SUB_READ_POSITION 0x05
#define RRC_SERVO_SUB_SET_DEVIATION 0x07 /* PWM servo only */
#define RRC_SERVO_SUB_READ_DEVIATION 0x09 /* PWM servo only */

/* ---- FUNC 0x04: PWM servo ---- */
#define RRC_PWM_SERVO_MAX_COUNT 8
typedef struct {
    uint8_t id;
    uint16_t pulse; /* [500, 2500] us <-> [0, 180] deg */
} rrc_pwm_servo_target_t;
typedef struct {
    uint16_t time_ms;
    uint8_t count;
    rrc_pwm_servo_target_t targets[RRC_PWM_SERVO_MAX_COUNT];
} rrc_pwm_servo_move_multi_t;
// 한글: FUNC4 PWM 서보: 펄스 500~2500us = 0~180도.
int rrc_unpack_pwm_servo_move_multi(const uint8_t *data, uint8_t len, rrc_pwm_servo_move_multi_t *out);

typedef struct {
    uint16_t time_ms;
    uint8_t id;
    uint16_t pulse;
} rrc_pwm_servo_move_single_t;
int rrc_unpack_pwm_servo_move_single(const uint8_t *data, uint8_t len, rrc_pwm_servo_move_single_t *out);

/* read position/deviation requests: data = [subcommand, servo_id] */
int rrc_unpack_pwm_servo_read_request(const uint8_t *data, uint8_t len, uint8_t *subcommand, uint8_t *servo_id);

/* set deviation: data = [0x07, servo_id, int8 deviation (-100..100)] */
int rrc_unpack_pwm_servo_set_deviation(const uint8_t *data, uint8_t len, uint8_t *servo_id, int8_t *deviation);

/* device -> host: position upload (len 4) or deviation upload (len 3) */
size_t rrc_pack_pwm_servo_position(uint8_t servo_id, uint16_t pulse, uint8_t *data_out);
size_t rrc_pack_pwm_servo_deviation(uint8_t servo_id, int8_t deviation, uint8_t *data_out);

/* ---- FUNC 0x05: bus servo (move + read-position only, see file header) ---- */
#define RRC_BUS_SERVO_MAX_COUNT 8
typedef struct {
    uint8_t id;
    uint16_t pulse; /* [0, 1000] <-> [0, 240] deg on the servos seen so far */
} rrc_bus_servo_target_t;
typedef struct {
    uint16_t time_ms;
    uint8_t count;
    rrc_bus_servo_target_t targets[RRC_BUS_SERVO_MAX_COUNT];
} rrc_bus_servo_move_t;
// 한글: FUNC5 버스 서보: 펄스 0~1000 = 0~240도.
int rrc_unpack_bus_servo_move(const uint8_t *data, uint8_t len, rrc_bus_servo_move_t *out);

/* read position request: data = [0x05, servo_id] */
int rrc_unpack_bus_servo_read_position(const uint8_t *data, uint8_t len, uint8_t *servo_id);

/* device -> host: position upload. success: 0 = ok, -1 = fail. */
size_t rrc_pack_bus_servo_position(uint8_t servo_id, int8_t success, int16_t pulse, uint8_t *data_out);

/* ---- FUNC 0x06: key/button (device -> host, encode) ---- */
typedef enum {
    RRC_BUTTON_PRESSED = 0x01,
    RRC_BUTTON_LONGPRESS = 0x02,
    RRC_BUTTON_CLICK = 0x20,
    RRC_BUTTON_DOUBLE_CLICK = 0x40,
} rrc_button_event_t;
// 한글: FUNC6 버튼 이벤트(장치→호스트).
size_t rrc_pack_key_event(uint8_t button_id, uint8_t event, uint8_t *data_out);

/* ---- FUNC 0x07: IMU (device -> host, encode) ---- */
typedef struct {
    float accel_g[3];    /* ax, ay, az in g, raw sensor axes (X=right, Y=back, Z=down) */
    float gyro_dps[3];   /* gx, gy, gz in deg/s, same raw axes */
} rrc_imu_sample_t;
/* data_out must have room for 24 bytes. */
// 한글: FUNC7 IMU(장치→호스트): 가속도 g, 자이로 deg/s, 센서 원시 축.
size_t rrc_pack_imu(const rrc_imu_sample_t *sample, uint8_t *data_out);

/* ---- FUNC 0x08: gamepad (device -> host, encode) ---- */
typedef struct {
    uint16_t buttons;
    uint8_t hat;
    int8_t lx, ly, rx, ry;
} rrc_gamepad_state_t;
// 한글: FUNC8 게임패드.
size_t rrc_pack_gamepad(const rrc_gamepad_state_t *state, uint8_t *data_out);

/* ---- FUNC 0x09: SBUS (device -> host, encode) ---- */
typedef struct {
    int16_t channels[16];
    uint8_t ch17;
    uint8_t ch18;
    uint8_t signal_loss;
    uint8_t fail_safe;
} rrc_sbus_frame_t;
/* data_out must have room for 36 bytes. */
// 한글: FUNC9 SBUS.
size_t rrc_pack_sbus(const rrc_sbus_frame_t *frame, uint8_t *data_out);

#ifdef __cplusplus
}
#endif

#endif /* RRC_FUNCS_H */
