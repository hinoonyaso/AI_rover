/* 한글: Hiwonder LX 시리즈 버스 서보 프로토콜(55 55 ID LEN CMD 파라미터 체크섬)과 RRC FUNC5 요청→서보 트랜잭션 매핑. */
/* Hiwonder LX-series serial bus servo protocol (RRC program analysis 3.8.3):
 *   55 55 ID LEN CMD PARAMS... CHECKSUM, LEN = nparams + 3, CHECKSUM = ~(ID+LEN+CMD+PARAMS) & 0xFF
 * plus the mapping from RRC FUNC5 host requests to servo transactions. */
#ifndef CORE_BUS_SERVO_H
#define CORE_BUS_SERVO_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define BUS_SERVO_ID_BROADCAST 0xFE
#define BUS_SERVO_MAX_PARAMS 8
#define BUS_SERVO_MAX_FRAME (6 + BUS_SERVO_MAX_PARAMS)

enum {
    BUS_CMD_MOVE_TIME_WRITE = 1,
    BUS_CMD_ID_WRITE = 13,
    BUS_CMD_ID_READ = 14,
    BUS_CMD_ANGLE_OFFSET_ADJUST = 17,
    BUS_CMD_ANGLE_OFFSET_WRITE = 18,
    BUS_CMD_ANGLE_OFFSET_READ = 19,
    BUS_CMD_ANGLE_LIMIT_WRITE = 20,
    BUS_CMD_ANGLE_LIMIT_READ = 21,
    BUS_CMD_VIN_LIMIT_WRITE = 22,
    BUS_CMD_VIN_LIMIT_READ = 23,
    BUS_CMD_TEMP_MAX_LIMIT_WRITE = 24,
    BUS_CMD_TEMP_MAX_LIMIT_READ = 25,
    BUS_CMD_TEMP_READ = 26,
    BUS_CMD_VIN_READ = 27,
    BUS_CMD_POS_READ = 28,
    BUS_CMD_LOAD_OR_UNLOAD_WRITE = 31,
};

/* Returns the frame length written to out (>= BUS_SERVO_MAX_FRAME bytes), 0 on bad input. */
size_t bus_servo_build(uint8_t id, uint8_t cmd, const uint8_t *params, uint8_t nparams, uint8_t *out);
size_t bus_servo_build_move(uint8_t id, uint16_t position, uint16_t time_ms, uint8_t *out);

/* Streaming response parser. */
typedef struct {
    uint8_t buf[BUS_SERVO_MAX_FRAME + 2];
    uint8_t len;
} bus_servo_rx_t;
typedef struct {
    uint8_t id, cmd, nparams;
    uint8_t params[BUS_SERVO_MAX_PARAMS];
} bus_servo_reply_t;
void bus_servo_rx_init(bus_servo_rx_t *rx);
/* Feed one byte; returns 1 when a checksum-valid frame completed (copied to *out). */
int bus_servo_rx_feed(bus_servo_rx_t *rx, uint8_t byte, bus_servo_reply_t *out);

/* ---- RRC FUNC5 request -> servo transaction ---- */
typedef struct {
    uint8_t subcommand;   /* RRC subcommand (0x05, 0x07, ...) used to tag the upload */
    uint8_t id;           /* servo id to address (0xFE broadcast for ID read) */
    uint8_t cmd;          /* servo command */
    uint8_t params[BUS_SERVO_MAX_PARAMS];
    uint8_t nparams;
    uint8_t expects_reply;
    uint8_t reply_len;    /* expected reply parameter bytes */
} bus_servo_plan_t;
/* Single-servo requests (everything except subcommand 0x01 multi-move, which carries
 * several servos and is expanded by the caller). Returns 1 if recognised, else 0. */
int bus_servo_plan_from_rrc(const uint8_t *data, uint8_t len, bus_servo_plan_t *plan);
/* Build the FUNC5 upload data for a plan: [id, subcommand, success(0/-1), reply bytes...].
 * Returns data length. reply may be NULL when success != 0. */
size_t bus_servo_make_upload(const bus_servo_plan_t *plan, int success, const uint8_t *reply, uint8_t reply_len,
                             uint8_t *data_out);

#ifdef __cplusplus
}
#endif
#endif
