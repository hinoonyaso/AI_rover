/* 한글: USB 게임패드 리포트→FUNC8. 이 수신기의 원시 HID 레이아웃은 문서가 없어서 기본 레이아웃은 "추정(미검증)"이며 테이블로 고칠 수 있다. */
/* USB gamepad (2.4 GHz PS2-style receiver on the USB HOST port) report -> FUNC8 state.
 * Vendor button masks are from the program analysis 3.12 (usbh_hid_gamepad.h). The raw HID
 * report layout of this receiver is NOT documented anywhere we have: the default layout below
 * is an assumption (UNVERIFIED) and the layout is table-driven so it can be corrected after
 * capturing a real report with the raw-report debug function (see app/usb_gamepad.c). */
#ifndef CORE_GAMEPAD_H
#define CORE_GAMEPAD_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define GAMEPAD_MASK_L2 0x0001u
#define GAMEPAD_MASK_R2 0x0002u
#define GAMEPAD_MASK_SELECT 0x0004u
#define GAMEPAD_MASK_START 0x0008u
#define GAMEPAD_MASK_L3 0x0020u
#define GAMEPAD_MASK_R3 0x0040u
#define GAMEPAD_MASK_CROSS 0x0100u
#define GAMEPAD_MASK_CIRCLE 0x0200u
#define GAMEPAD_MASK_L1 0x0400u
#define GAMEPAD_MASK_SQUARE 0x0800u
#define GAMEPAD_MASK_TRIANGLE 0x1000u
#define GAMEPAD_MASK_R1 0x8000u

typedef struct {
    uint16_t buttons;
    uint8_t hat; /* vendor encoding: bit3 = a direction is pressed, bits0..2 = direction index */
    int8_t lx, ly, rx, ry;
} gamepad_state_t;

typedef struct {
    uint8_t min_len;
    uint8_t lx, ly, rx, ry;  /* byte offsets of the 0..255 stick axes (128 = centre) */
    uint8_t hat_byte;        /* byte holding the HID hat nibble (0..7 = N..NW, 8/15 = released) */
    uint8_t hat_shift;
    uint8_t btn_lo, btn_hi;  /* byte offsets of the raw 16 button bits */
    uint16_t btn_map[16];    /* raw bit i -> GAMEPAD_MASK_* (0 = unused) */
} gamepad_layout_t;

extern const gamepad_layout_t GAMEPAD_LAYOUT_DEFAULT; /* assumption, see header comment */

/* Returns 0 on success, -1 if the report is too short. */
int gamepad_parse_report(const gamepad_layout_t *layout, const uint8_t *report, size_t len, gamepad_state_t *out);

#ifdef __cplusplus
}
#endif
#endif
