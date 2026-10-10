/* 한글: 추상 I2C 위의 IMU 드라이버: MPU6050(보드 문서의 칩) + QMI8658 자동 판별. 출력은 FUNC7 보드 프레임(X=오른쪽,Y=뒤,Z=아래)의 g/deg/s. 칩→보드 축 변환은 추정(기본 항등), check_axes.py로 확인한다. */
/* IMU driver over an abstract I2C bus: MPU6050 (the chip the board documentation names) with
 * automatic detection of QMI8658 (the chip Hiwonder's newer sample code mentions), so one image
 * works on either board revision. Output is converted to g and deg/s in the *board* frame that
 * FUNC7 uses (X=right, Y=back, Z=down); the chip->board axis map is a build-time table
 * (UNVERIFIED default = identity, verify with tools/imu_calibration/check_axes.py). */
#ifndef CORE_IMU_H
#define CORE_IMU_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    /* Return 0 on success. */
    int (*write)(void *ctx, uint8_t addr7, uint8_t reg, const uint8_t *data, size_t len);
    int (*read)(void *ctx, uint8_t addr7, uint8_t reg, uint8_t *data, size_t len);
    void (*delay_ms)(uint32_t ms);
    void *ctx;
} i2c_bus_t;

typedef enum { IMU_NONE = 0, IMU_MPU6050 = 1, IMU_QMI8658 = 2 } imu_kind_t;

typedef struct {
    int8_t src[3]; /* board axis i takes chip axis src[i] (0..2) ... */
    int8_t sign[3]; /* ... multiplied by sign[i] (+1/-1) */
} imu_axis_map_t;

typedef struct {
    const i2c_bus_t *bus;
    imu_kind_t kind;
    uint8_t addr;
    float accel_lsb_per_g;
    float gyro_lsb_per_dps;
    imu_axis_map_t map;
    uint8_t whoami;
    uint8_t last_raw[14];  /* previous raw sample, for the frozen-sensor check */
    uint16_t same_count;   /* consecutive identical raw samples */
} imu_t;

/* A live sensor always has LSB noise. This many identical raw samples in a row (0.5 s at 50 Hz) means
 * the sensor stopped converting (2026-10-10: QMI8658 frozen after a cold power-on without soft reset)
 * -> imu_read() returns IMU_ERR_FROZEN until the data changes, so the caller re-initialises.
 * 한글: 원시 값이 25회 연속 똑같으면 센서 정지로 보고 오류를 돌려 재초기화하게 한다. */
#define IMU_FROZEN_SAMPLES 25
#define IMU_ERR_FROZEN (-2)

extern const imu_axis_map_t IMU_AXIS_MAP_IDENTITY;

/* Probes and configures the sensor (~111 Hz output data rate). Returns 0 on success. */
int imu_init(imu_t *imu, const i2c_bus_t *bus, const imu_axis_map_t *map);
/* Reads one sample; returns 0 on success, -1 on a bus error, IMU_ERR_FROZEN if the data stopped changing. */
int imu_read(imu_t *imu, float accel_g[3], float gyro_dps[3]);

#ifdef __cplusplus
}
#endif
#endif
