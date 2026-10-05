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

#endif
