/* 한글: ST7735S 0.96인치 80x160 LCD(SPI2) 상태 화면 드라이버. 제어 핀 배정은 추정. */
#ifndef DRV_LCD_H
#define DRV_LCD_H

#include <stdint.h>

#define LCD_COLS 26 /* 160 px / 6 px per glyph */
#define LCD_ROWS 10 /* 80 px / 8 px per glyph */

/* ST7735S 0.96" 80x160 IPS on SPI2 (landscape). Returns 0 on success. Pins: PINMAP.md (control pins ASSUMED). */
int drv_lcd_init(void);
void drv_lcd_backlight(int on);
/* Draws one text line (padded with spaces to the full width). Colours are RGB565. */
void drv_lcd_print(uint8_t row, const char *text, uint16_t fg, uint16_t bg);
void drv_lcd_clear(uint16_t color);

#define LCD_BLACK 0x0000
#define LCD_WHITE 0xFFFF
#define LCD_RED 0xF800
#define LCD_GREEN 0x07E0
#define LCD_YELLOW 0xFFE0
#define LCD_CYAN 0x07FF

#endif
