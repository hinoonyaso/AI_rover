/* 한글: 소프트웨어 I2C(약 250kHz) + EXTI. 벤더 이미지도 I2C 주변장치 없이 비트뱅잉한다. 클럭 스트레칭 대기는 시간 제한이 있고 실패하면 버스 복구(SCL 9펄스+STOP). */
/* IMU on a bit-banged I2C bus (PB10 SCL / PB11 SDA, open drain) with EXTI on PB12.
 * The vendor firmware also bit-bangs this bus (no I2C peripheral is initialised in the image). */
#include "drv_imu.h"

#include "app_config.h"
#include "board.h"

static StaticSemaphore_t g_drdy_buf;
static SemaphoreHandle_t g_drdy;

#define HALF_PERIOD_CYCLES (SystemCoreClock / 250000U / 2U) /* ~250 kHz */

static void dwt_init(void)
{
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT = 0;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
}

static inline void delay_cycles(uint32_t c)
{
    const uint32_t start = DWT->CYCCNT;
    while ((DWT->CYCCNT - start) < c) {
    }
}

static inline void scl(int v) { HAL_GPIO_WritePin(IMU_SCL_PORT, IMU_SCL_PIN, v ? GPIO_PIN_SET : GPIO_PIN_RESET); }
static inline void sda(int v) { HAL_GPIO_WritePin(IMU_SDA_PORT, IMU_SDA_PIN, v ? GPIO_PIN_SET : GPIO_PIN_RESET); }
static inline int sda_read(void) { return HAL_GPIO_ReadPin(IMU_SDA_PORT, IMU_SDA_PIN) == GPIO_PIN_SET; }
static inline int scl_read(void) { return HAL_GPIO_ReadPin(IMU_SCL_PORT, IMU_SCL_PIN) == GPIO_PIN_SET; }
static inline void dly(void) { delay_cycles(HALF_PERIOD_CYCLES); }

/* Releases SCL and waits for the slave to stop stretching (bounded). */
/* 한글: SCL을 놓고 슬레이브의 클럭 스트레칭이 끝날 때까지 기다린다(최대 약 2ms). */
static int scl_high(void)
{
    scl(1);
    for (int i = 0; i < 2000; i++) {
        if (scl_read()) {
            return 0;
        }
        delay_cycles(SystemCoreClock / 1000000U);
    }
    return -1;
}

static int start_cond(void)
{
    sda(1);
    if (scl_high()) return -1;
    dly();
    sda(0);
    dly();
    scl(0);
    return 0;
}

static void stop_cond(void)
{
    sda(0);
    dly();
    scl_high();
    dly();
    sda(1);
    dly();
}

static int write_byte(uint8_t b)
{
    for (int i = 7; i >= 0; i--) {
        sda((b >> i) & 1);
        dly();
        if (scl_high()) return -1;
        dly();
        scl(0);
    }
    sda(1);
    dly();
    if (scl_high()) return -1;
    dly();
    const int nack = sda_read();
    scl(0);
    return nack ? -1 : 0;
}

static uint8_t read_byte(int ack)
{
    uint8_t b = 0;
    sda(1);
    for (int i = 0; i < 8; i++) {
        dly();
        scl_high();
        dly();
        b = (uint8_t)((b << 1) | (sda_read() ? 1 : 0));
        scl(0);
    }
    sda(ack ? 0 : 1);
    dly();
    scl_high();
    dly();
    scl(0);
    sda(1);
    return b;
}

void drv_imu_bus_recover(void)
{
    sda(1);
    for (int i = 0; i < 9; i++) {
        scl(0);
        dly();
        scl(1);
        dly();
    }
    stop_cond();
}

static int i2c_write(void *ctx, uint8_t addr, uint8_t reg, const uint8_t *d, size_t n)
{
    (void)ctx;
    int rc = start_cond();
    if (!rc) rc = write_byte((uint8_t)(addr << 1));
    if (!rc) rc = write_byte(reg);
    for (size_t i = 0; !rc && i < n; i++) rc = write_byte(d[i]);
    stop_cond();
    if (rc) drv_imu_bus_recover();
    return rc;
}

static int i2c_read(void *ctx, uint8_t addr, uint8_t reg, uint8_t *d, size_t n)
{
    (void)ctx;
    int rc = start_cond();
    if (!rc) rc = write_byte((uint8_t)(addr << 1));
    if (!rc) rc = write_byte(reg);
    if (!rc) rc = start_cond(); /* repeated start */
    if (!rc) rc = write_byte((uint8_t)((addr << 1) | 1));
    for (size_t i = 0; !rc && i < n; i++) d[i] = read_byte(i + 1 < n);
    stop_cond();
    if (rc) drv_imu_bus_recover();
    return rc;
}

static void delay_ms(uint32_t ms) { vTaskDelay(pdMS_TO_TICKS(ms) ? pdMS_TO_TICKS(ms) : 1); }

static const i2c_bus_t g_bus = {i2c_write, i2c_read, delay_ms, NULL};

int drv_imu_init(imu_t *imu)
{
    GPIO_InitTypeDef g = {0};
    static const imu_axis_map_t map = {IMU_MAP_SRC, IMU_MAP_SIGN};

    __HAL_RCC_GPIOB_CLK_ENABLE();
    g_drdy = xSemaphoreCreateBinaryStatic(&g_drdy_buf);
    dwt_init();

    g.Pin = IMU_SCL_PIN | IMU_SDA_PIN;
    g.Mode = GPIO_MODE_OUTPUT_OD;
    g.Pull = GPIO_NOPULL; /* external 10k pull-ups on the board */
    g.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOB, &g);
    scl(1);
    sda(1);
    drv_imu_bus_recover();

    g.Pin = IMU_INT_PIN;
    g.Mode = GPIO_MODE_IT_RISING; /* MPU6050 INT is configured active-high push-pull in imu.c */
    g.Pull = GPIO_PULLDOWN;
    HAL_GPIO_Init(IMU_INT_PORT, &g);
    HAL_NVIC_SetPriority(EXTI15_10_IRQn, 5, 0);
    HAL_NVIC_EnableIRQ(EXTI15_10_IRQn);

    return imu_init(imu, &g_bus, &map);
}

SemaphoreHandle_t drv_imu_drdy(void) { return g_drdy; }

/* 한글: IMU 데이터 준비 인터럽트: 세마포어를 줘서 imu_task를 깨운다. */
void EXTI15_10_IRQHandler(void)
{
    if (__HAL_GPIO_EXTI_GET_IT(IMU_INT_PIN)) {
        __HAL_GPIO_EXTI_CLEAR_IT(IMU_INT_PIN);
        BaseType_t woken = pdFALSE;
        if (g_drdy) {
            xSemaphoreGiveFromISR(g_drdy, &woken);
        }
        portYIELD_FROM_ISR(woken);
    }
}
