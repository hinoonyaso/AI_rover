/* RRC frame codec: AA 55 FUNC LEN DATA CRC8-MAXIM.
 * CRC covers FUNC+LEN+DATA only (not the AA 55 header).
 * Wire-compatible with jetrover_base (src/jetrover_base/src/rrc_protocol.cpp)
 * and with the vendor "RRC Communication Protocol with the Host Computer
 * Analysis.pdf" (firmware_source/). Freestanding: no libc allocation, no I/O.
 */
#ifndef RRC_PROTOCOL_H
#define RRC_PROTOCOL_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define RRC_HEADER_0 0xAAu
#define RRC_HEADER_1 0x55u
#define RRC_MAX_DATA_LEN 255
/* header(2) + func(1) + len(1) + data(<=255) + crc(1) */
#define RRC_MAX_FRAME_LEN (2 + 1 + 1 + RRC_MAX_DATA_LEN + 1)

typedef enum {
    RRC_FUNC_SYS = 0x00,        /* battery/system (undocumented by vendor, empirically reverse-engineered) */
    RRC_FUNC_LED = 0x01,
    RRC_FUNC_BUZZER = 0x02,
    RRC_FUNC_MOTOR = 0x03,
    RRC_FUNC_PWM_SERVO = 0x04,
    RRC_FUNC_BUS_SERVO = 0x05,
    RRC_FUNC_KEY = 0x06,
    RRC_FUNC_IMU = 0x07,
    RRC_FUNC_GAMEPAD = 0x08,
    RRC_FUNC_SBUS = 0x09,
} rrc_func_t;

uint8_t rrc_crc8_maxim(const uint8_t *data, size_t len);

/* Encode func+data into `out` (must be >= RRC_MAX_FRAME_LEN). Returns total
 * frame length, or 0 if data_len > RRC_MAX_DATA_LEN. */
size_t rrc_encode(uint8_t func, const uint8_t *data, size_t data_len, uint8_t *out);

/* Streaming parser: feed bytes one at a time (or via rrc_parser_feed_buf),
 * call rrc_parser_next to pop completed, CRC-valid frames. Resyncs on a
 * single leading 0xAA when a header/CRC mismatch is found (matches the host
 * parser's behavior in jetrover_base). */
typedef struct {
    uint8_t buf[RRC_MAX_FRAME_LEN * 2];
    size_t len;
} rrc_parser_t;

typedef struct {
    uint8_t func;
    uint8_t data[RRC_MAX_DATA_LEN];
    uint8_t data_len;
} rrc_frame_t;

void rrc_parser_init(rrc_parser_t *p);
/* Returns number of bytes actually consumed from `in` (may be less than
 * `in_len` if the internal buffer is full; caller should retry). */
size_t rrc_parser_feed(rrc_parser_t *p, const uint8_t *in, size_t in_len);
/* Pops one complete frame if available. Returns 1 if a frame was popped into
 * *out, 0 if none is available yet. */
int rrc_parser_next(rrc_parser_t *p, rrc_frame_t *out);

#ifdef __cplusplus
}
#endif

#endif /* RRC_PROTOCOL_H */
