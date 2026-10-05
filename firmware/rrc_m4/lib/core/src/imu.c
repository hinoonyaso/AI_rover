/* 한글: IMU 구현: MPU6050 설정(SMPLRT_DIV=8 → 약 111Hz, ±500dps, ±2g), QMI8658 설정(±512dps, ±4g, 125Hz). */
#include "core/imu.h"

#define MPU_ADDR_LO 0x68
#define MPU_ADDR_HI 0x69
#define MPU_REG_SMPLRT_DIV 0x19
#define MPU_REG_CONFIG 0x1A
#define MPU_REG_GYRO_CONFIG 0x1B
#define MPU_REG_ACCEL_CONFIG 0x1C
#define MPU_REG_INT_PIN_CFG 0x37
#define MPU_REG_INT_ENABLE 0x38
#define MPU_REG_ACCEL_XOUT_H 0x3B
#define MPU_REG_PWR_MGMT_1 0x6B
#define MPU_REG_WHO_AM_I 0x75

#define QMI_ADDR_HI 0x6B
#define QMI_ADDR_LO 0x6A
#define QMI_REG_WHO_AM_I 0x00
#define QMI_WHO_AM_I_VALUE 0x05
#define QMI_REG_CTRL1 0x02
#define QMI_REG_CTRL2 0x03
#define QMI_REG_CTRL3 0x04
#define QMI_REG_CTRL7 0x08
#define QMI_REG_AX_L 0x35

const imu_axis_map_t IMU_AXIS_MAP_IDENTITY = {{0, 1, 2}, {1, 1, 1}};

static int wr1(const i2c_bus_t *b, uint8_t addr, uint8_t reg, uint8_t v)
{
    return b->write(b->ctx, addr, reg, &v, 1);
}

/* 한글: MPU6050 탐색/설정. WHO_AM_I가 0x68(또는 호환 칩 값)이면 사용. 게이트 DLPF on일 때 자이로 출력률 1kHz이므로 SMPLRT_DIV=8 → 약 111Hz(기존 펌웨어와 동일). */
static int try_mpu(imu_t *imu, uint8_t addr)
{
    uint8_t id = 0;
    const i2c_bus_t *b = imu->bus;

    if (b->read(b->ctx, addr, MPU_REG_WHO_AM_I, &id, 1) != 0) {
        return -1;
    }
    /* 0x68 MPU6050; 0x70/0x71/0x72/0x73/0x98 are common compatible/clone ids */
    if (!(id == 0x68 || id == 0x69 || (id >= 0x70 && id <= 0x73) || id == 0x98)) {
        return -1;
    }
    imu->whoami = id;
    imu->kind = IMU_MPU6050;
    imu->addr = addr;
    imu->accel_lsb_per_g = 16384.0f;   /* +-2 g */
    imu->gyro_lsb_per_dps = 65.5f;     /* +-500 dps */

    if (wr1(b, addr, MPU_REG_PWR_MGMT_1, 0x80) != 0) { /* device reset */
        return -1;
    }
    b->delay_ms(100);
    if (wr1(b, addr, MPU_REG_PWR_MGMT_1, 0x01) != 0) { /* wake, PLL with X gyro */
        return -1;
    }
    b->delay_ms(10);
    /* Gyro output rate is 1 kHz when the DLPF is on, so div 8 -> 111 Hz, matching the stock firmware. */
    int rc = wr1(b, addr, MPU_REG_SMPLRT_DIV, 8);
    rc |= wr1(b, addr, MPU_REG_CONFIG, 0x03);        /* DLPF ~44 Hz */
    rc |= wr1(b, addr, MPU_REG_GYRO_CONFIG, 0x08);   /* +-500 dps */
    rc |= wr1(b, addr, MPU_REG_ACCEL_CONFIG, 0x00);  /* +-2 g */
    rc |= wr1(b, addr, MPU_REG_INT_PIN_CFG, 0x10);   /* INT push-pull, active high, cleared on any read */
    rc |= wr1(b, addr, MPU_REG_INT_ENABLE, 0x01);    /* data ready */
    return rc ? -1 : 0;
}

/* 한글: QMI8658 탐색/설정(WHO_AM_I=0x05). 하드웨어 미확인, 보드 개정에 따라 있을 수 있어 자동 판별만 해 둔다. */
static int try_qmi(imu_t *imu, uint8_t addr)
{
    uint8_t id = 0;
    const i2c_bus_t *b = imu->bus;

    if (b->read(b->ctx, addr, QMI_REG_WHO_AM_I, &id, 1) != 0 || id != QMI_WHO_AM_I_VALUE) {
        return -1;
    }
    imu->whoami = id;
    imu->kind = IMU_QMI8658;
    imu->addr = addr;
    imu->accel_lsb_per_g = 8192.0f;  /* +-4 g */
    imu->gyro_lsb_per_dps = 64.0f;   /* +-512 dps */

    int rc = wr1(b, addr, QMI_REG_CTRL1, 0x40);  /* address auto-increment */
    rc |= wr1(b, addr, QMI_REG_CTRL2, 0x16);     /* accel +-4 g, 125 Hz */
    rc |= wr1(b, addr, QMI_REG_CTRL3, 0x56);     /* gyro +-512 dps, 125 Hz */
    rc |= wr1(b, addr, QMI_REG_CTRL7, 0x03);     /* enable accel + gyro */
    return rc ? -1 : 0;
}

int imu_init(imu_t *imu, const i2c_bus_t *bus, const imu_axis_map_t *map)
{
    imu->bus = bus;
    imu->kind = IMU_NONE;
    imu->map = map ? *map : IMU_AXIS_MAP_IDENTITY;

    if (try_mpu(imu, MPU_ADDR_LO) == 0 || try_mpu(imu, MPU_ADDR_HI) == 0 ||
        try_qmi(imu, QMI_ADDR_HI) == 0 || try_qmi(imu, QMI_ADDR_LO) == 0) {
        return 0;
    }
    imu->kind = IMU_NONE;
    return -1;
}

static int16_t be16(const uint8_t *p)
{
    return (int16_t)((p[0] << 8) | p[1]);
}

static int16_t le16(const uint8_t *p)
{
    return (int16_t)((p[1] << 8) | p[0]);
}

/* 한글: 한 샘플 읽기 후 축 변환 맵 적용(board axis i = chip axis src[i] × sign[i]). */
int imu_read(imu_t *imu, float accel_g[3], float gyro_dps[3])
{
    uint8_t raw[14];
    int16_t a[3], g[3];
    const i2c_bus_t *b = imu->bus;

    if (imu->kind == IMU_MPU6050) {
        if (b->read(b->ctx, imu->addr, MPU_REG_ACCEL_XOUT_H, raw, 14) != 0) {
            return -1;
        }
        for (int i = 0; i < 3; ++i) {
            a[i] = be16(&raw[2 * i]);
            g[i] = be16(&raw[8 + 2 * i]); /* raw[6..7] is temperature */
        }
    } else if (imu->kind == IMU_QMI8658) {
        if (b->read(b->ctx, imu->addr, QMI_REG_AX_L, raw, 12) != 0) {
            return -1;
        }
        for (int i = 0; i < 3; ++i) {
            a[i] = le16(&raw[2 * i]);
            g[i] = le16(&raw[6 + 2 * i]);
        }
    } else {
        return -1;
    }
    for (int i = 0; i < 3; ++i) {
        const int s = imu->map.src[i];
        accel_g[i] = (float)a[s] / imu->accel_lsb_per_g * (float)imu->map.sign[i];
        gyro_dps[i] = (float)g[s] / imu->gyro_lsb_per_dps * (float)imu->map.sign[i];
    }
    return 0;
}
