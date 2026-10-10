/* 한글: 보드 상태 화면 드라이버 — SSD1306 128x32 흑백 OLED(I2C 0x3C, IMU 버스 공유). 2026-10-10 vendor 바이너리로 확인(이전 ST7735 SPI 가정은 틀림). */
#ifndef DRV_LCD_H
#define DRV_LCD_H

#include <stdint.h>

#define LCD_COLS 21 /* 128 px / 6 px per glyph */
#define LCD_ROWS 4  /* 32 px / 8 px per page */

/* SSD1306 128x32 OLED on the shared bit-banged I2C bus (0x3C). Returns 0 on success (display ACKs). */
int drv_lcd_init(void);
/* OLED has no backlight: display on/off. */
void drv_lcd_backlight(int on);
/* Draws one text line (padded to the full width). Colours keep the RGB565 names for the API:
 * monochrome, fg != black is lit; bg != black inverts the line. */
void drv_lcd_print(uint8_t row, const char *text, uint16_t fg, uint16_t bg);
void drv_lcd_clear(uint16_t color);

#define LCD_BLACK 0x0000
#define LCD_WHITE 0xFFFF
#define LCD_RED 0xF800
#define LCD_GREEN 0x07E0
#define LCD_YELLOW 0xFFE0
#define LCD_CYAN 0x07FF

#endif
