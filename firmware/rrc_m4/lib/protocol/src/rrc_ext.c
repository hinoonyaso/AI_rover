/* 한글: 확장 FUNC 팩/언팩 구현. */
#include "rrc_ext.h"

#include <string.h>

static void wr_u32(uint8_t *p, uint32_t v) {
    p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); p[2] = (uint8_t)(v >> 16); p[3] = (uint8_t)(v >> 24);
}
static uint16_t rd_u16(const uint8_t *p) { return (uint16_t)(p[0] | (p[1] << 8)); }
static float rd_f32(const uint8_t *p) {
    uint32_t b = (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
    float v;
    memcpy(&v, &b, sizeof(v));
    return v;
}
static void wr_f32(uint8_t *p, float v) {
    uint32_t b;
    memcpy(&b, &v, sizeof(b));
    wr_u32(p, b);
}

size_t rrc_ext_pack_status(const rrc_ext_status_t *s, uint8_t *d) {
    d[0] = s->flags;
    d[1] = s->stop_reason;
    d[2] = s->imu_kind;
    d[3] = s->comm_mode;
    for (int i = 0; i < 4; i++) d[4 + i] = s->motor_fault[i];
    wr_u32(&d[8], s->uptime_ms);
    wr_u32(&d[12], s->reset_cause);
    return RRC_EXT_STATUS_LEN;
}

size_t rrc_ext_pack_wheel(const rrc_ext_wheel_t *w, uint8_t *d) {
    for (int i = 0; i < 4; i++) {
        wr_f32(&d[i * 4], w->rps[i]);
    }
    for (int i = 0; i < 4; i++) {
        wr_u32(&d[16 + i * 4], (uint32_t)w->counter[i]);
    }
    return RRC_EXT_WHEEL_LEN;
}

int rrc_ext_unpack_diag(const uint8_t *d, uint8_t len, rrc_diag_cmd_t *out) {
    if (len < 1) return 0;
    memset(out, 0, sizeof(*out));
    out->subcommand = d[0];
    switch (d[0]) {
    case RRC_DIAG_CLEAR_ESTOP:
    case RRC_DIAG_ESTOP:
    case RRC_DIAG_REQUEST_STATUS:
        return len == 1;
    case RRC_DIAG_SET_TIMEOUT:
        if (len != 3) return 0;
        out->timeout_ms = rd_u16(&d[1]);
        return 1;
    case RRC_DIAG_SET_PID:
        if (len != 14) return 0;
        out->motor = d[1];
        out->kp = rd_f32(&d[2]);
        out->ki = rd_f32(&d[6]);
        out->kd = rd_f32(&d[10]);
        return 1;
    case RRC_DIAG_RAW_PWM:
        if (len != 4) return 0;
        out->motor = d[1];
        out->pulse = (int16_t)rd_u16(&d[2]);
        return 1;
    default:
        return 0;
    }
}

size_t rrc_ext_pack_raw_hid(const uint8_t *report, size_t len, uint8_t *d) {
    if (len > 32) len = 32;
    d[0] = (uint8_t)len;
    memcpy(&d[1], report, len);
    return 1 + len;
}
