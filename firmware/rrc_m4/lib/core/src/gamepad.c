/* 한글: 게임패드 리포트 파서 구현(기본 레이아웃은 미검증 추정). */
#include "core/gamepad.h"

/* UNVERIFIED default: typical 8-byte PS2-clone HID report
 *   [0]=lx [1]=ly [2]=rx [3]=ry [4]=hat(low nibble)+face buttons [5]=shoulder/start bits ... */
const gamepad_layout_t GAMEPAD_LAYOUT_DEFAULT = {
    .min_len = 6,
    .lx = 0, .ly = 1, .rx = 2, .ry = 3,
    .hat_byte = 4, .hat_shift = 0,
    .btn_lo = 4, .btn_hi = 5,
    .btn_map = {
        0, 0, 0, 0,                                                   /* bits 0..3: hat nibble */
        GAMEPAD_MASK_SQUARE, GAMEPAD_MASK_CROSS, GAMEPAD_MASK_CIRCLE, GAMEPAD_MASK_TRIANGLE, /* 4..7 */
        GAMEPAD_MASK_L1, GAMEPAD_MASK_R1, GAMEPAD_MASK_L2, GAMEPAD_MASK_R2,                  /* 8..11 */
        GAMEPAD_MASK_SELECT, GAMEPAD_MASK_START, GAMEPAD_MASK_L3, GAMEPAD_MASK_R3,           /* 12..15 */
    },
};

static int8_t axis(uint8_t raw)
{
    return (int8_t)((int)raw - 128);
}

int gamepad_parse_report(const gamepad_layout_t *l, const uint8_t *r, size_t len, gamepad_state_t *out)
{
    if (len < l->min_len) {
        return -1;
    }
    out->lx = axis(r[l->lx]);
    out->ly = axis(r[l->ly]);
    out->rx = axis(r[l->rx]);
    out->ry = axis(r[l->ry]);

    const uint8_t raw_hat = (uint8_t)((r[l->hat_byte] >> l->hat_shift) & 0x0F);
    out->hat = (raw_hat < 8) ? (uint8_t)(0x08 | raw_hat) : 0x00; /* released -> 0 */

    const uint16_t raw_buttons = (uint16_t)(r[l->btn_lo] | (r[l->btn_hi] << 8));
    uint16_t mapped = 0;
    for (int i = 0; i < 16; ++i) {
        if ((raw_buttons >> i) & 1u) {
            mapped |= l->btn_map[i];
        }
    }
    out->buttons = mapped;
    return 0;
}
