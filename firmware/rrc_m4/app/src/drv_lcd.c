/* 한글: 보드 상태 화면 = SSD1306 128x32 흑백 OLED, I2C 주소 0x3C, IMU와 같은 소프트웨어 I2C 버스(PB10/PB11)를 뮤텍스로 공유.
 *       2026-10-10 vendor 바이너리 분석으로 확인(u8g2 ssd1306_128x32_univision 초기화, oled_mutex) — 이전의 "ST7735 SPI2 LCD"는 추정이 틀렸다.
 *       한 줄 = 한 페이지(8픽셀)씩 보내고 버스를 놓아 IMU가 오래 기다리지 않게 한다. */
/* Status display: SSD1306 128x32 monochrome OLED at I2C 0x3C on the bit-banged IMU bus (PB10/PB11),
 * shared through the bus mutex in drv_imu.c. Identified 2026-10-10 from the vendor binary (u8g2
 * ssd1306_128x32_univision init sequence, "oled_mutex"); the earlier ST7735/SPI2 assumption was wrong
 * (troubleshooting/035). Each text row is one 8-pixel page sent in its own transaction, so the IMU
 * waits at most one page (~5 ms at ~250 kHz). Only the lcd task calls this driver. */
#include "drv_lcd.h"

#include <string.h>

#include "drv_imu.h"
#include "lcd_font.h"

#define OLED_ADDR 0x3C
#define OLED_W 128

static uint8_t g_ready;
static uint8_t g_page[1 + OLED_W]; /* control byte 0x40 + one 128-column page */

/* Vendor init sequence (u8x8 ssd1306_128x32_univision): display off, clock, mux 32, offset 0,
 * start line 0, charge pump on, horizontal addressing, segment/COM remap, COM pins 0x02,
 * contrast 0x8F, precharge, VCOMH, scroll off, resume RAM, normal (not inverted), display on. */
static const uint8_t INIT_CMDS[] = {
    0x00, /* control byte: command stream */
    0xAE, 0xD5, 0x80, 0xA8, 0x1F, 0xD3, 0x00, 0x40, 0x8D, 0x14, 0x20, 0x00, 0xA1, 0xC8,
    0xDA, 0x02, 0x81, 0x8F, 0xD9, 0xF1, 0xDB, 0x40, 0x2E, 0xA4, 0xA6, 0xAF,
};

static int send_cmds(const uint8_t *c, size_t n) { return drv_i2c_write_raw(OLED_ADDR, c, n); }

/* 한글: 페이지(행) 하나를 열 0~127에 쓴다. */
static int flush_page(uint8_t row)
{
    const uint8_t win[] = {0x00, 0x21, 0x00, OLED_W - 1, 0x22, row, row}; /* column / page range */
    if (send_cmds(win, sizeof(win))) return -1;
    g_page[0] = 0x40; /* control byte: data stream */
    return drv_i2c_write_raw(OLED_ADDR, g_page, sizeof(g_page));
}

int drv_lcd_init(void)
{
    drv_i2c_shared_init();
    if (send_cmds(INIT_CMDS, sizeof(INIT_CMDS))) {
        return -1; /* no ACK at 0x3C: no display */
    }
    g_ready = 1;
    drv_lcd_clear(LCD_BLACK);
    return 0;
}

void drv_lcd_backlight(int on)
{
    if (!g_ready) return;
    const uint8_t c[] = {0x00, (uint8_t)(on ? 0xAF : 0xAE)}; /* OLED: display on/off */
    send_cmds(c, sizeof(c));
}

void drv_lcd_clear(uint16_t color)
{
    if (!g_ready) return;
    memset(&g_page[1], color != LCD_BLACK ? 0xFF : 0x00, OLED_W);
    for (uint8_t row = 0; row < LCD_ROWS; row++) {
        flush_page(row);
    }
}

/* Monochrome: pixels are lit where fg != black; bg != black draws inverted text. */
void drv_lcd_print(uint8_t row, const char *text, uint16_t fg, uint16_t bg)
{
    if (!g_ready || row >= LCD_ROWS) return;
    const uint8_t invert = (bg != LCD_BLACK) || (fg == LCD_BLACK);
    memset(&g_page[1], 0, OLED_W);
    for (int col = 0; col < LCD_COLS && text[col]; col++) {
        int c = text[col];
        if (c >= 'a' && c <= 'z') c -= 32;
        if (c < 32 || c > 95) c = '?';
        memcpy(&g_page[1 + col * 6], LCD_FONT5X7[c - 32], 5); /* column bytes, LSB = top row */
    }
    if (invert) {
        for (int i = 1; i <= OLED_W; i++) g_page[i] = (uint8_t)~g_page[i];
    }
    flush_page(row);
}
