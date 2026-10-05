/* 한글: SBUS 프레임 디코더: 25바이트, 16채널 11비트(원시 192~1792, 중앙 992). UART5 100000 baud 8E2(하드웨어 인버터). 채널은 FUNC9로 원시값 그대로 전달한다. */
/* SBUS frame decoder (RRC program analysis 3.13): 25 bytes, 0x0F header, 16 x 11-bit channels
 * (raw 192..1792, centre 992), flags (ch17/ch18/frame-lost/failsafe), 0x00 end byte.
 * UART5: 100000 baud, 8E2, hardware-inverted. Channels are forwarded raw in FUNC9. */
#ifndef CORE_SBUS_H
#define CORE_SBUS_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define SBUS_FRAME_LEN 25

typedef struct {
    int16_t channels[16];
    uint8_t ch17, ch18, signal_loss, fail_safe;
} sbus_status_t;

/* Returns 0 on a valid frame, -1 otherwise. */
int sbus_decode_frame(const uint8_t *frame25, sbus_status_t *out);

/* Resynchronising stream front-end: feed bytes, call when it returns 1. */
typedef struct {
    uint8_t buf[SBUS_FRAME_LEN];
    uint8_t len;
} sbus_stream_t;
void sbus_stream_init(sbus_stream_t *s);
int sbus_stream_feed(sbus_stream_t *s, uint8_t byte, sbus_status_t *out);

#ifdef __cplusplus
}
#endif
#endif
