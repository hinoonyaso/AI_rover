/* 한글: ST7735S 드라이버(가로 모드, 오프셋 x=1,y=26). 한 줄(8픽셀 높이)씩 그려 RAM을 아낀다. */
#include "drv_lcd.h"

#include <string.h>

#include "FreeRTOS.h"
#include "board.h"
#include "lcd_font.h"
#include "task.h"

static SPI_HandleTypeDef hspi2;
static uint8_t g_ready;

#define X_OFFSET 1
#define Y_OFFSET 26

static inline void cs(int v) { HAL_GPIO_WritePin(LCD_CS_PORT, LCD_CS_PIN, v ? GPIO_PIN_SET : GPIO_PIN_RESET); }
static inline void dc(int v) { HAL_GPIO_WritePin(LCD_DC_PORT, LCD_DC_PIN, v ? GPIO_PIN_SET : GPIO_PIN_RESET); }

static void write_cmd(uint8_t c)
{
    dc(0);
    cs(0);
    HAL_SPI_Transmit(&hspi2, &c, 1, 10);
    cs(1);
}

static void write_data(const uint8_t *d, uint16_t n)
{
    dc(1);
    cs(0);
    HAL_SPI_Transmit(&hspi2, (uint8_t *)d, n, 50);
    cs(1);
}

static void cmd_args(uint8_t c, const uint8_t *a, uint8_t n)
{
    write_cmd(c);
    if (n) write_data(a, n);
}

static void delay(uint32_t ms) { vTaskDelay(pdMS_TO_TICKS(ms) ? pdMS_TO_TICKS(ms) : 1); }

static void set_window(uint16_t x0, uint16_t y0, uint16_t x1, uint16_t y1)
{
    const uint8_t xa[4] = {0, (uint8_t)(x0 + X_OFFSET), 0, (uint8_t)(x1 + X_OFFSET)};
    const uint8_t ya[4] = {0, (uint8_t)(y0 + Y_OFFSET), 0, (uint8_t)(y1 + Y_OFFSET)};
    cmd_args(0x2A, xa, 4);
    cmd_args(0x2B, ya, 4);
    write_cmd(0x2C);
}

int drv_lcd_init(void)
{
    GPIO_InitTypeDef g = {0};

    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_GPIOD_CLK_ENABLE();
    __HAL_RCC_SPI2_CLK_ENABLE();
    g.Mode = GPIO_MODE_AF_PP;
    g.Pull = GPIO_NOPULL;
    g.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    g.Alternate = GPIO_AF5_SPI2;
    g.Pin = GPIO_PIN_13; /* SCK */
    HAL_GPIO_Init(GPIOB, &g);
    g.Pin = GPIO_PIN_3; /* MOSI */
    HAL_GPIO_Init(GPIOC, &g);

    hspi2.Instance = SPI2;
    hspi2.Init.Mode = SPI_MODE_MASTER;
    hspi2.Init.Direction = SPI_DIRECTION_1LINE;
    hspi2.Init.DataSize = SPI_DATASIZE_8BIT;
    hspi2.Init.CLKPolarity = SPI_POLARITY_LOW;
    hspi2.Init.CLKPhase = SPI_PHASE_1EDGE;
    hspi2.Init.NSS = SPI_NSS_SOFT;
    hspi2.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_4; /* 10.5 MHz */
    hspi2.Init.FirstBit = SPI_FIRSTBIT_MSB;
    hspi2.Init.TIMode = SPI_TIMODE_DISABLE;
    hspi2.Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE;
    if (HAL_SPI_Init(&hspi2) != HAL_OK) {
        return -1;
    }

    HAL_GPIO_WritePin(LCD_RES_PORT, LCD_RES_PIN, GPIO_PIN_RESET);
    delay(20);
    HAL_GPIO_WritePin(LCD_RES_PORT, LCD_RES_PIN, GPIO_PIN_SET);
    delay(120);
    write_cmd(0x11); /* sleep out */
    delay(120);
    static const uint8_t frm[6] = {0x01, 0x2C, 0x2D, 0x01, 0x2C, 0x2D};
    cmd_args(0xB1, frm, 3);
    cmd_args(0xB2, frm, 3);
    cmd_args(0xB3, frm, 6);
    cmd_args(0xB4, (const uint8_t[]){0x07}, 1);
    cmd_args(0xC0, (const uint8_t[]){0xA2, 0x02, 0x84}, 3);
    cmd_args(0xC1, (const uint8_t[]){0xC5}, 1);
    cmd_args(0xC2, (const uint8_t[]){0x0A, 0x00}, 2);
    cmd_args(0xC3, (const uint8_t[]){0x8A, 0x2A}, 2);
    cmd_args(0xC4, (const uint8_t[]){0x8A, 0xEE}, 2);
    cmd_args(0xC5, (const uint8_t[]){0x0E}, 1);
    write_cmd(0x21); /* inversion on (IPS panel) */
    cmd_args(0x36, (const uint8_t[]){0xA8}, 1); /* landscape, BGR */
    cmd_args(0x3A, (const uint8_t[]){0x05}, 1); /* RGB565 */
    write_cmd(0x13);
    write_cmd(0x29); /* display on */
    g_ready = 1;
    drv_lcd_clear(LCD_BLACK);
    drv_lcd_backlight(1);
    return 0;
}

void drv_lcd_backlight(int on)
{
    HAL_GPIO_WritePin(LCD_BLK_PORT, LCD_BLK_PIN, on ? GPIO_PIN_SET : GPIO_PIN_RESET);
}

void drv_lcd_clear(uint16_t color)
{
    if (!g_ready) return;
    uint8_t line[160 * 2];
    for (int i = 0; i < 160; i++) {
        line[2 * i] = (uint8_t)(color >> 8);
        line[2 * i + 1] = (uint8_t)color;
    }
    set_window(0, 0, 159, 79);
    for (int y = 0; y < 80; y++) {
        write_data(line, sizeof(line));
    }
}

void drv_lcd_print(uint8_t row, const char *text, uint16_t fg, uint16_t bg)
{
    uint8_t buf[160 * 2 * 8]; /* 8 pixel rows of the text line */
    if (!g_ready || row >= LCD_ROWS) return;

    memset(buf, 0, sizeof(buf));
    for (int px = 0; px < 160; px++) {
        for (int py = 0; py < 8; py++) {
            buf[(py * 160 + px) * 2] = (uint8_t)(bg >> 8);
            buf[(py * 160 + px) * 2 + 1] = (uint8_t)bg;
        }
    }
    for (int col = 0; col < LCD_COLS && text[col]; col++) {
        int c = text[col];
        if (c >= 'a' && c <= 'z') c -= 32;
        if (c < 32 || c > 95) c = '?';
        const uint8_t *glyph = LCD_FONT5X7[c - 32];
        for (int gx = 0; gx < 5; gx++) {
            for (int gy = 0; gy < 7; gy++) {
                if ((glyph[gx] >> gy) & 1) {
                    const int idx = (gy * 160 + col * 6 + gx) * 2;
                    buf[idx] = (uint8_t)(fg >> 8);
                    buf[idx + 1] = (uint8_t)fg;
                }
            }
        }
    }
    set_window(0, (uint16_t)(row * 8), 159, (uint16_t)(row * 8 + 7));
    write_data(buf, sizeof(buf));
}
