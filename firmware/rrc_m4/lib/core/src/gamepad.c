/* 한글: 게임패드 리포트 파서 구현(레이아웃은 2026-10-10 실측). */
#include "core/gamepad.h"

/* MEASURED 2026-10-10 (raw HID capture while pressing every control in a known order, troubleshooting/039).
 * The 2.4 GHz receiver sends 11-byte reports starting with the report ID 0x07:
 *   [0]=0x07  [1]=LX [2]=LY [3]=RX [4]=RY (0..255, centre ~0x7f, up/left = 0)
 *   [5]=hat low nibble (0..7 clockwise from up, 0x0F released)
 *   [6] bit0 A, bit1 B, bit3 X, bit4 Y, bit6 L1, bit7 R1 (bit2/bit5 never seen)
 *   [7] bit0 L2, bit1 R2, bit2 SELECT, bit3 START, bit4 MODE, bit5 L3, bit6 R3
 *   [8]=R2 analog [9]=L2 analog [10]=0
 * raw_buttons = byte7 (bits 0..7) | byte6 << 8. Face buttons map to the vendor PS names the FUNC8 masks use:
 * A = CROSS, B = CIRCLE, X = SQUARE, Y = TRIANGLE.
 * 한글: 실측 레이아웃(맨 앞 리포트 ID 0x07 때문에 이전 추정보다 한 칸씩 밀려 있었다). */
const gamepad_layout_t GAMEPAD_LAYOUT_DEFAULT = {
    .min_len = 8,
    .lx = 1, .ly = 2, .rx = 3, .ry = 4,
    .hat_byte = 5, .hat_shift = 0,
    .btn_lo = 7, .btn_hi = 6,
    .btn_map = {
        GAMEPAD_MASK_L2, GAMEPAD_MASK_R2, GAMEPAD_MASK_SELECT, GAMEPAD_MASK_START,           /* byte7 bit 0..3 */
        GAMEPAD_MASK_MODE, GAMEPAD_MASK_L3, GAMEPAD_MASK_R3, 0,                              /* byte7 bit 4..7 */
        GAMEPAD_MASK_CROSS, GAMEPAD_MASK_CIRCLE, 0, GAMEPAD_MASK_SQUARE,                     /* byte6 bit 0..3 */
        GAMEPAD_MASK_TRIANGLE, 0, GAMEPAD_MASK_L1, GAMEPAD_MASK_R1,                          /* byte6 bit 4..7 */
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
