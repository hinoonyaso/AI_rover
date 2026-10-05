/* 한글: SBUS 디코더 구현(0x0F 헤더, 끝 바이트 0x00 또는 0x?4). */
#include "core/sbus.h"

int sbus_decode_frame(const uint8_t *f, sbus_status_t *out)
{
    if (f[0] != 0x0F || !(f[24] == 0x00 || (f[24] & 0x0F) == 0x04)) {
        return -1;
    }
    out->channels[0] = (int16_t)(((f[1] | f[2] << 8)) & 0x07FF);
    out->channels[1] = (int16_t)(((f[2] >> 3 | f[3] << 5)) & 0x07FF);
    out->channels[2] = (int16_t)(((f[3] >> 6 | f[4] << 2 | f[5] << 10)) & 0x07FF);
    out->channels[3] = (int16_t)(((f[5] >> 1 | f[6] << 7)) & 0x07FF);
    out->channels[4] = (int16_t)(((f[6] >> 4 | f[7] << 4)) & 0x07FF);
    out->channels[5] = (int16_t)(((f[7] >> 7 | f[8] << 1 | f[9] << 9)) & 0x07FF);
    out->channels[6] = (int16_t)(((f[9] >> 2 | f[10] << 6)) & 0x07FF);
    out->channels[7] = (int16_t)(((f[10] >> 5 | f[11] << 3)) & 0x07FF);
    out->channels[8] = (int16_t)(((f[12] | f[13] << 8)) & 0x07FF);
    out->channels[9] = (int16_t)(((f[13] >> 3 | f[14] << 5)) & 0x07FF);
    out->channels[10] = (int16_t)(((f[14] >> 6 | f[15] << 2 | f[16] << 10)) & 0x07FF);
    out->channels[11] = (int16_t)(((f[16] >> 1 | f[17] << 7)) & 0x07FF);
    out->channels[12] = (int16_t)(((f[17] >> 4 | f[18] << 4)) & 0x07FF);
    out->channels[13] = (int16_t)(((f[18] >> 7 | f[19] << 1 | f[20] << 9)) & 0x07FF);
    out->channels[14] = (int16_t)(((f[20] >> 2 | f[21] << 6)) & 0x07FF);
    out->channels[15] = (int16_t)(((f[21] >> 5 | f[22] << 3)) & 0x07FF);
    out->ch17 = (f[23] & 0x01) ? 1 : 0;
    out->ch18 = (f[23] & 0x02) ? 1 : 0;
    out->signal_loss = (f[23] & 0x04) ? 1 : 0;
    out->fail_safe = (f[23] & 0x08) ? 1 : 0;
    return 0;
}

void sbus_stream_init(sbus_stream_t *s)
{
    s->len = 0;
}

/* 한글: 바이트 스트림에서 25바이트 프레임을 찾는다. 끝 바이트가 틀리면 payload 안의 다음 0x0F부터 다시 동기화한다. */
int sbus_stream_feed(sbus_stream_t *s, uint8_t byte, sbus_status_t *out)
{
    if (s->len == 0 && byte != 0x0F) {
        return 0;
    }
    s->buf[s->len++] = byte;
    if (s->len < SBUS_FRAME_LEN) {
        return 0;
    }
    s->len = 0;
    if (sbus_decode_frame(s->buf, out) == 0) {
        return 1;
    }
    /* Bad end byte: the 0x0F we locked on was probably payload. Rescan from the next 0x0F. */
    for (int i = 1; i < SBUS_FRAME_LEN; ++i) {
        if (s->buf[i] == 0x0F) {
            for (int j = i; j < SBUS_FRAME_LEN; ++j) {
                s->buf[s->len++] = s->buf[j];
            }
            break;
        }
    }
    return 0;
}
