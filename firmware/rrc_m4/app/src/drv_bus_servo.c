/* 한글: 버스 서보 반이중 링크. PE7/PE8 역할·극성은 추정이라, 첫 읽기 실패 시 4개 조합을 돌며 응답이 오는 조합을 기억한다. */
/* Half-duplex bus servo link on USART6 (115200). The two direction pins PE7/PE8 idle High (stock
 * firmware); their roles/polarity are ASSUMED, so on a failed read the driver cycles through the 4
 * combinations and keeps the first that gets an answer. */
#include "drv_bus_servo.h"

#include "FreeRTOS.h"
#include "board.h"
#include "semphr.h"

static UART_HandleTypeDef huart6;
static StaticSemaphore_t g_mtx_buf;
static SemaphoreHandle_t g_mtx;
static uint8_t g_combo; /* bit0: swap TX/RX pin roles, bit1: active-high instead of active-low */
static uint8_t g_combo_confirmed;

static void dir_set(int tx)
{
    GPIO_TypeDef *tx_port = (g_combo & 1) ? BUS_RX_EN_PORT : BUS_TX_EN_PORT;
    uint16_t tx_pin = (g_combo & 1) ? BUS_RX_EN_PIN : BUS_TX_EN_PIN;
    GPIO_TypeDef *rx_port = (g_combo & 1) ? BUS_TX_EN_PORT : BUS_RX_EN_PORT;
    uint16_t rx_pin = (g_combo & 1) ? BUS_TX_EN_PIN : BUS_RX_EN_PIN;
    const int active_low = !(g_combo & 2);
    const GPIO_PinState on = active_low ? GPIO_PIN_RESET : GPIO_PIN_SET;
    const GPIO_PinState off = active_low ? GPIO_PIN_SET : GPIO_PIN_RESET;

    HAL_GPIO_WritePin(tx_port, tx_pin, tx ? on : off);
    HAL_GPIO_WritePin(rx_port, rx_pin, tx ? off : on);
}

static void dir_idle(void)
{
    HAL_GPIO_WritePin(BUS_TX_EN_PORT, BUS_TX_EN_PIN, GPIO_PIN_SET); /* stock idle state */
    HAL_GPIO_WritePin(BUS_RX_EN_PORT, BUS_RX_EN_PIN, GPIO_PIN_SET);
}

void drv_bus_servo_init(void)
{
    GPIO_InitTypeDef g = {0};

    g_mtx = xSemaphoreCreateMutexStatic(&g_mtx_buf);
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_USART6_CLK_ENABLE();
    g.Pin = GPIO_PIN_6 | GPIO_PIN_7;
    g.Mode = GPIO_MODE_AF_PP;
    g.Pull = GPIO_PULLUP;
    g.Speed = GPIO_SPEED_FREQ_HIGH;
    g.Alternate = GPIO_AF8_USART6;
    HAL_GPIO_Init(GPIOC, &g);

    huart6.Instance = BUS_USART;
    huart6.Init.BaudRate = 115200;
    huart6.Init.WordLength = UART_WORDLENGTH_8B;
    huart6.Init.StopBits = UART_STOPBITS_1;
    huart6.Init.Parity = UART_PARITY_NONE;
    huart6.Init.Mode = UART_MODE_TX_RX;
    huart6.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart6.Init.OverSampling = UART_OVERSAMPLING_16;
    HAL_UART_Init(&huart6);
    dir_idle();
}

static void rx_flush(void)
{
    volatile uint32_t d;
    while (__HAL_UART_GET_FLAG(&huart6, UART_FLAG_RXNE)) {
        d = huart6.Instance->DR;
        (void)d;
    }
    __HAL_UART_CLEAR_OREFLAG(&huart6);
}

static void send_frame(const uint8_t *f, size_t n)
{
    rx_flush();
    dir_set(1);
    HAL_UART_Transmit(&huart6, (uint8_t *)f, (uint16_t)n, 20);
    while (!__HAL_UART_GET_FLAG(&huart6, UART_FLAG_TC)) {
    }
    dir_set(0);
}

static int wait_reply(uint8_t id, uint8_t cmd, bus_servo_reply_t *out, uint32_t timeout_ms)
{
    bus_servo_rx_t rx;
    uint8_t b;
    uint32_t start = HAL_GetTick();

    bus_servo_rx_init(&rx);
    while (HAL_GetTick() - start < timeout_ms) {
        if (HAL_UART_Receive(&huart6, &b, 1, 2) == HAL_OK) {
            if (bus_servo_rx_feed(&rx, b, out) && out->cmd == cmd &&
                (id == BUS_SERVO_ID_BROADCAST || out->id == id)) {
                return 0;
            }
        } else {
            __HAL_UART_CLEAR_OREFLAG(&huart6);
        }
    }
    return -1;
}

void drv_bus_servo_move(uint8_t id, uint16_t pulse, uint16_t time_ms)
{
    uint8_t f[BUS_SERVO_MAX_FRAME];
    const size_t n = bus_servo_build_move(id, pulse, time_ms, f);

    xSemaphoreTake(g_mtx, portMAX_DELAY);
    send_frame(f, n);
    dir_idle();
    xSemaphoreGive(g_mtx);
}

/* 한글: 블로킹 트랜잭션. 확인 전에는 최대 4개 방향핀 조합을 시도하고, 응답이 오면 그 조합을 확정한다. */
int drv_bus_servo_xfer(const bus_servo_plan_t *plan, uint8_t *reply, uint8_t *reply_len)
{
    uint8_t f[BUS_SERVO_MAX_FRAME];
    bus_servo_reply_t r;
    int rc = -1;
    const size_t n = bus_servo_build(plan->id, plan->cmd, plan->params, plan->nparams, f);

    xSemaphoreTake(g_mtx, portMAX_DELAY);
    const uint8_t first = g_combo;
    for (int attempt = 0; attempt < (g_combo_confirmed || !plan->expects_reply ? 1 : 4); attempt++) {
        send_frame(f, n);
        if (!plan->expects_reply) {
            rc = 0;
            break;
        }
        if (wait_reply(plan->id, plan->cmd, &r, 15) == 0) {
            for (uint8_t i = 0; i < r.nparams && i < plan->reply_len; i++) {
                reply[i] = r.params[i];
            }
            *reply_len = plan->reply_len;
            g_combo_confirmed = 1;
            rc = 0;
            break;
        }
        if (!g_combo_confirmed) {
            g_combo = (uint8_t)((g_combo + 1) & 3);
        }
    }
    if (rc != 0 && !g_combo_confirmed) {
        g_combo = first;
    }
    dir_idle();
    xSemaphoreGive(g_mtx);
    return rc;
}
