/* 한글: STM32F407VET6 RRC 보드 핀 테이블. 각 핀의 출처/신뢰도는 firmware_source/PINMAP.md. CONFIRMED=확정, ASSUMED=추정. */
/* STM32F407VET6 RRC board pin table. Source and confidence for every line: firmware_source/PINMAP.md. */
#ifndef BOARD_H
#define BOARD_H

#include "stm32f4xx_hal.h"

/* ---- host / aux / bluetooth / sbus / bus-servo UARTs ---- */
#define HOST_USART USART3 /* PD8 TX, PD9 RX, AF7, 1 Mbaud  -- CONFIRMED */
#define AUX_USART USART1  /* PA9 TX, PA10 RX, AF7 (ISP port) -- CONFIRMED */
#define BT_USART USART2   /* PD5 TX, PD6 RX, AF7, 9600     -- CONFIRMED */
#define SBUS_UART UART5   /* PD2 RX, AF8, 100000 8E2       -- CONFIRMED */
#define BUS_USART USART6  /* PC6 TX, PC7 RX, AF8, 115200 half duplex -- port CONFIRMED */

/* Bus servo direction control, idle = both High (vendor MX_GPIO_Init). ASSUMED: PE7 = TX buffer
 * /OE, PE8 = RX buffer /OE, active Low. drv_bus_servo.c re-tries the other 3 combinations. */
#define BUS_TX_EN_PORT GPIOE
#define BUS_TX_EN_PIN GPIO_PIN_7
#define BUS_RX_EN_PORT GPIOE
#define BUS_RX_EN_PIN GPIO_PIN_8

/* ---- user LED (PE10, active Low) and buzzer (PA8, active High) -- CONFIRMED ---- */
#define LED_PORT GPIOE
#define LED_PIN GPIO_PIN_10
#define BUZZER_PORT GPIOA
#define BUZZER_PIN GPIO_PIN_8

/* ---- buttons PE0 / PE1, active Low -- pins CONFIRMED, id mapping ASSUMED ---- */
#define KEY1_PORT GPIOE
#define KEY1_PIN GPIO_PIN_0
#define KEY2_PORT GPIOE
#define KEY2_PIN GPIO_PIN_1

/* ---- IMU: soft I2C PB10 SCL / PB11 SDA, INT on PB12 -- CONFIRMED ---- */
#define IMU_SCL_PORT GPIOB
#define IMU_SCL_PIN GPIO_PIN_10
#define IMU_SDA_PORT GPIOB
#define IMU_SDA_PIN GPIO_PIN_11
#define IMU_INT_PORT GPIOB
#define IMU_INT_PIN GPIO_PIN_12

/* ---- motor driver fault input PD3 (High = fault) -- ASSUMED polarity ---- */
#define MOTOR_FAULT_PORT GPIOD
#define MOTOR_FAULT_PIN GPIO_PIN_3

/* ---- PWM servos: GPIO soft PWM on TIM13 -- pins ASSUMED ---- */
#define PWM_SERVO_PINS_INIT { \
    {GPIOC, GPIO_PIN_8}, {GPIOC, GPIO_PIN_9}, {GPIOA, GPIO_PIN_11}, {GPIOA, GPIO_PIN_12} }

/* ---- status display: SSD1306 128x32 OLED at I2C 0x3C on the IMU bus (PB10/PB11) -- CONFIRMED
 * 2026-10-10 from the vendor binary. The SPI2 "LCD" (PB13/PC3, PD11..14) did not react when probed:
 * those pins are left in their vendor reset levels by drv_gpio_safe_init and otherwise unused. ---- */

/* ---- battery ADC1: PB0 (IN8) + Vrefint (IN17), DMA2 stream 0 channel 0 -- CONFIRMED ---- */

/* ---- motor PWM: TIM1 CH1..4 (PE9, PE11, PE13, PE14 AF1), TIM9 CH1/2 (PE5, PE6 AF3),
 *      TIM10 CH1 (PB8 AF3), TIM11 CH1 (PB9 AF3). PSC 839, ARR 999 (200 Hz, +-1000 = 0..100 %) ---- */
#define MOTOR_PWM_PSC 839
#define MOTOR_PWM_ARR 999

#endif
