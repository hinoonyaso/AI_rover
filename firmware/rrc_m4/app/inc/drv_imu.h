/* 한글: IMU 드라이버: 비트뱅잉 I2C(PB10 SCL/PB11 SDA) + 데이터 준비 EXTI(PB12). */
#ifndef DRV_IMU_H
#define DRV_IMU_H

#include "core/imu.h"
#include "FreeRTOS.h"
#include "semphr.h"

/* Initialises the bit-banged I2C bus + EXTI data-ready line and probes the sensor. */
int drv_imu_init(imu_t *imu);
/* Data-ready semaphore given from the EXTI15_10 ISR. */
SemaphoreHandle_t drv_imu_drdy(void);
/* Releases a stuck bus (9 SCL pulses + STOP). */
void drv_imu_bus_recover(void);
/* The bit-banged bus is shared with the SSD1306 OLED (0x3C). Call once before the tasks start:
 * prepares the open-drain GPIO and the bus mutex. 한글: OLED와 공유하는 버스 준비(뮤텍스 포함). */
void drv_i2c_shared_init(void);
/* One locked write transaction: START, addr+W, n bytes, STOP. Returns 0 on ACK. */
int drv_i2c_write_raw(uint8_t addr, const uint8_t *d, size_t n);

#endif
