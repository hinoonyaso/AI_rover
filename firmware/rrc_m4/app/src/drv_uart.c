/* 한글: DMA UART 구현. 수신은 원형 DMA + IDLE 인터럽트로 스트림 버퍼에 채우고, 송신은 스트림 버퍼에서 DMA로 내보낸다. HAL의 UART IRQ 핸들러를 우회하므로 송신 완료 시 gState를 직접 READY로 돌린다. */
#include "drv_uart.h"

#include <string.h>

#include "board.h"
#include "task.h"

#define RX_DMA_SIZE 512
#define RX_STREAM_MAX 2048
#define TX_STREAM_MAX 2048
#define TX_DMA_SIZE 256

typedef struct {
    USART_TypeDef *usart;
    UART_HandleTypeDef huart;
    DMA_HandleTypeDef hdma_rx, hdma_tx;
    uint8_t rx_dma[RX_DMA_SIZE];
    uint16_t rx_last;
    uint8_t tx_dma[TX_DMA_SIZE];
    volatile uint8_t tx_busy;
    StreamBufferHandle_t rx_stream, tx_stream;
    StaticStreamBuffer_t rx_sb, tx_sb;
    uint8_t rx_store[RX_STREAM_MAX + 1], tx_store[TX_STREAM_MAX + 1];
    volatile uint32_t dropped;
    TaskHandle_t tx_waiter;
} port_t;

static port_t g_port[UART_PORT_COUNT];

typedef struct {
    USART_TypeDef *usart;
    GPIO_TypeDef *tx_port, *rx_port;
    uint16_t tx_pin, rx_pin;
    uint32_t af;
    DMA_Stream_TypeDef *rx_stream, *tx_stream;
    uint32_t dma_channel;
    IRQn_Type usart_irq, rx_dma_irq, tx_dma_irq;
} port_cfg_t;

static const port_cfg_t CFG[UART_PORT_COUNT] = {
    /* host: USART3 PD8/PD9 AF7, DMA1 S1(RX) / S3(TX) ch4 */
    {USART3, GPIOD, GPIOD, GPIO_PIN_8, GPIO_PIN_9, GPIO_AF7_USART3, DMA1_Stream1, DMA1_Stream3, DMA_CHANNEL_4,
     USART3_IRQn, DMA1_Stream1_IRQn, DMA1_Stream3_IRQn},
    /* aux: USART1 PA9/PA10 AF7, DMA2 S2(RX) / S7(TX) ch4 */
    {USART1, GPIOA, GPIOA, GPIO_PIN_9, GPIO_PIN_10, GPIO_AF7_USART1, DMA2_Stream2, DMA2_Stream7, DMA_CHANNEL_4,
     USART1_IRQn, DMA2_Stream2_IRQn, DMA2_Stream7_IRQn},
    /* bluetooth: USART2 PD5/PD6 AF7, DMA1 S5(RX) / S6(TX) ch4 */
    {USART2, GPIOD, GPIOD, GPIO_PIN_5, GPIO_PIN_6, GPIO_AF7_USART2, DMA1_Stream5, DMA1_Stream6, DMA_CHANNEL_4,
     USART2_IRQn, DMA1_Stream5_IRQn, DMA1_Stream6_IRQn},
};

static void clk_enable(uart_port_id_t id)
{
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOD_CLK_ENABLE();
    __HAL_RCC_DMA1_CLK_ENABLE();
    __HAL_RCC_DMA2_CLK_ENABLE();
    if (id == UART_PORT_HOST) __HAL_RCC_USART3_CLK_ENABLE();
    if (id == UART_PORT_AUX) __HAL_RCC_USART1_CLK_ENABLE();
    if (id == UART_PORT_BT) __HAL_RCC_USART2_CLK_ENABLE();
}

void drv_uart_init(uart_port_id_t id, uint32_t baud)
{
    port_t *p = &g_port[id];
    const port_cfg_t *c = &CFG[id];
    GPIO_InitTypeDef g = {0};

    memset(p, 0, sizeof(*p));
    /* sizes per port (RAM is tight in the micro-ROS build): host full size, aux/bluetooth smaller */
    const size_t rxn = id == UART_PORT_HOST ? RX_STREAM_MAX : (id == UART_PORT_AUX ? 1024 : 128);
    const size_t txn = id == UART_PORT_HOST ? TX_STREAM_MAX : (id == UART_PORT_AUX ? 1024 : 128);
    p->rx_stream = xStreamBufferCreateStatic(rxn, 1, p->rx_store, &p->rx_sb);
    p->tx_stream = xStreamBufferCreateStatic(txn, 1, p->tx_store, &p->tx_sb);
    clk_enable(id);

    g.Pin = c->tx_pin;
    g.Mode = GPIO_MODE_AF_PP;
    g.Pull = GPIO_PULLUP;
    g.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    g.Alternate = c->af;
    HAL_GPIO_Init(c->tx_port, &g);
    g.Pin = c->rx_pin;
    HAL_GPIO_Init(c->rx_port, &g);

    p->usart = c->usart;
    p->huart.Instance = c->usart;
    p->huart.Init.BaudRate = baud;
    p->huart.Init.WordLength = UART_WORDLENGTH_8B;
    p->huart.Init.StopBits = UART_STOPBITS_1;
    p->huart.Init.Parity = UART_PARITY_NONE;
    p->huart.Init.Mode = UART_MODE_TX_RX;
    p->huart.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    p->huart.Init.OverSampling = UART_OVERSAMPLING_8; /* needed for 1 Mbaud at 42/84 MHz clocks accuracy */

    p->hdma_rx.Instance = c->rx_stream;
    p->hdma_rx.Init.Channel = c->dma_channel;
    p->hdma_rx.Init.Direction = DMA_PERIPH_TO_MEMORY;
    p->hdma_rx.Init.PeriphInc = DMA_PINC_DISABLE;
    p->hdma_rx.Init.MemInc = DMA_MINC_ENABLE;
    p->hdma_rx.Init.PeriphDataAlignment = DMA_PDATAALIGN_BYTE;
    p->hdma_rx.Init.MemDataAlignment = DMA_MDATAALIGN_BYTE;
    p->hdma_rx.Init.Mode = DMA_CIRCULAR;
    p->hdma_rx.Init.Priority = DMA_PRIORITY_HIGH;
    p->hdma_rx.Init.FIFOMode = DMA_FIFOMODE_DISABLE;
    HAL_DMA_Init(&p->hdma_rx);
    __HAL_LINKDMA(&p->huart, hdmarx, p->hdma_rx);

    p->hdma_tx = p->hdma_rx;
    p->hdma_tx.Instance = c->tx_stream;
    p->hdma_tx.Init.Direction = DMA_MEMORY_TO_PERIPH;
    p->hdma_tx.Init.Mode = DMA_NORMAL;
    p->hdma_tx.Init.Priority = DMA_PRIORITY_MEDIUM;
    HAL_DMA_Init(&p->hdma_tx);
    __HAL_LINKDMA(&p->huart, hdmatx, p->hdma_tx);

    HAL_UART_Init(&p->huart);

    HAL_NVIC_SetPriority(c->usart_irq, 5, 0);
    HAL_NVIC_SetPriority(c->rx_dma_irq, 5, 0);
    HAL_NVIC_SetPriority(c->tx_dma_irq, 5, 0);
    HAL_NVIC_EnableIRQ(c->usart_irq);
    HAL_NVIC_EnableIRQ(c->rx_dma_irq);
    HAL_NVIC_EnableIRQ(c->tx_dma_irq);

    /* circular DMA + IDLE interrupt: the handler drains whatever DMA has written so far */
    HAL_UART_Receive_DMA(&p->huart, p->rx_dma, RX_DMA_SIZE);
    __HAL_UART_ENABLE_IT(&p->huart, UART_IT_IDLE);
}

/* 한글: DMA가 지금까지 채운 만큼을 스트림 버퍼로 옮긴다(원형 버퍼 경계 처리 포함). */
static void rx_drain_isr(port_t *p, BaseType_t *woken)
{
    const uint16_t pos = (uint16_t)(RX_DMA_SIZE - __HAL_DMA_GET_COUNTER(&p->hdma_rx));
    uint16_t last = p->rx_last;

    if (pos == last) {
        return;
    }
    if (pos > last) {
        xStreamBufferSendFromISR(p->rx_stream, &p->rx_dma[last], pos - last, woken);
    } else {
        xStreamBufferSendFromISR(p->rx_stream, &p->rx_dma[last], RX_DMA_SIZE - last, woken);
        if (pos) {
            xStreamBufferSendFromISR(p->rx_stream, &p->rx_dma[0], pos, woken);
        }
    }
    p->rx_last = pos == RX_DMA_SIZE ? 0 : pos;
}

static void usart_irq(port_t *p)
{
    BaseType_t woken = pdFALSE;
    if (__HAL_UART_GET_FLAG(&p->huart, UART_FLAG_IDLE)) {
        __HAL_UART_CLEAR_IDLEFLAG(&p->huart);
        rx_drain_isr(p, &woken);
    }
    if (__HAL_UART_GET_FLAG(&p->huart, UART_FLAG_ORE) || __HAL_UART_GET_FLAG(&p->huart, UART_FLAG_FE) ||
        __HAL_UART_GET_FLAG(&p->huart, UART_FLAG_NE)) {
        __HAL_UART_CLEAR_OREFLAG(&p->huart);
        __HAL_UART_CLEAR_FEFLAG(&p->huart);
        __HAL_UART_CLEAR_NEFLAG(&p->huart);
    }
    if (__HAL_UART_GET_FLAG(&p->huart, UART_FLAG_TC) && __HAL_UART_GET_IT_SOURCE(&p->huart, UART_IT_TC)) {
        __HAL_UART_DISABLE_IT(&p->huart, UART_IT_TC);
        __HAL_UART_CLEAR_FLAG(&p->huart, UART_FLAG_TC);
        p->tx_busy = 0;
        p->huart.gState = HAL_UART_STATE_READY; /* HAL's own IRQ handler is bypassed */
        if (p->tx_waiter) {
            vTaskNotifyGiveFromISR(p->tx_waiter, &woken);
        }
    }
    portYIELD_FROM_ISR(woken);
}

/* DMA RX half/complete interrupts also drain (keeps latency bounded under a continuous stream). */
static void rx_dma_irq(port_t *p)
{
    BaseType_t woken = pdFALSE;
    if (__HAL_DMA_GET_FLAG(&p->hdma_rx, __HAL_DMA_GET_HT_FLAG_INDEX(&p->hdma_rx)) ||
        __HAL_DMA_GET_FLAG(&p->hdma_rx, __HAL_DMA_GET_TC_FLAG_INDEX(&p->hdma_rx))) {
        __HAL_DMA_CLEAR_FLAG(&p->hdma_rx, __HAL_DMA_GET_HT_FLAG_INDEX(&p->hdma_rx));
        __HAL_DMA_CLEAR_FLAG(&p->hdma_rx, __HAL_DMA_GET_TC_FLAG_INDEX(&p->hdma_rx));
        rx_drain_isr(p, &woken);
    }
    HAL_DMA_IRQHandler(&p->hdma_rx);
    portYIELD_FROM_ISR(woken);
}

static void tx_dma_irq(port_t *p)
{
    HAL_DMA_IRQHandler(&p->hdma_tx); /* its complete callback enables the UART TC interrupt */
}

size_t drv_uart_write(uart_port_id_t id, const uint8_t *data, size_t len)
{
    port_t *p = &g_port[id];
    const size_t n = xStreamBufferSend(p->tx_stream, data, len, 0);
    if (n < len) {
        p->dropped += (uint32_t)(len - n);
    }
    return n;
}

size_t drv_uart_read(uart_port_id_t id, uint8_t *buf, size_t max, TickType_t ticks)
{
    return xStreamBufferReceive(g_port[id].rx_stream, buf, max, ticks);
}

/* 한글: 송신 펌프: 스트림 버퍼에서 꺼내 DMA 전송, 완료를 알림으로 기다린다(50ms 제한으로 송신 태스크가 멈추지 않게). */
void drv_uart_tx_poll(uart_port_id_t id)
{
    port_t *p = &g_port[id];
    p->tx_waiter = xTaskGetCurrentTaskHandle();
    for (;;) {
        const size_t n = xStreamBufferReceive(p->tx_stream, p->tx_dma, TX_DMA_SIZE, portMAX_DELAY);
        if (n == 0) {
            continue;
        }
        p->tx_busy = 1;
        ulTaskNotifyTake(pdTRUE, 0); /* clear stale notifications */
        if (HAL_UART_Transmit_DMA(&p->huart, p->tx_dma, (uint16_t)n) != HAL_OK) {
            p->tx_busy = 0;
            p->dropped += (uint32_t)n;
            continue;
        }
        if (ulTaskNotifyTake(pdTRUE, pdMS_TO_TICKS(50)) == 0) { /* never wedge the TX task */
            HAL_UART_AbortTransmit(&p->huart);
            p->huart.gState = HAL_UART_STATE_READY;
            p->tx_busy = 0;
        }
    }
}

void drv_uart_send_blocking(uart_port_id_t id, const uint8_t *data, size_t len)
{
    HAL_UART_Transmit(&g_port[id].huart, (uint8_t *)data, (uint16_t)len, 50);
}

StreamBufferHandle_t drv_uart_tx_buffer(uart_port_id_t id) { return g_port[id].tx_stream; }
uint32_t drv_uart_dropped(uart_port_id_t id) { return g_port[id].dropped; }
void drv_uart_flush_rx(uart_port_id_t id) { xStreamBufferReset(g_port[id].rx_stream); }

/* ---- vectors ---- */
void USART3_IRQHandler(void) { usart_irq(&g_port[UART_PORT_HOST]); }
void DMA1_Stream1_IRQHandler(void) { rx_dma_irq(&g_port[UART_PORT_HOST]); }
void DMA1_Stream3_IRQHandler(void) { tx_dma_irq(&g_port[UART_PORT_HOST]); }
void USART1_IRQHandler(void) { usart_irq(&g_port[UART_PORT_AUX]); }
void DMA2_Stream2_IRQHandler(void) { rx_dma_irq(&g_port[UART_PORT_AUX]); }
void DMA2_Stream7_IRQHandler(void) { tx_dma_irq(&g_port[UART_PORT_AUX]); }
void USART2_IRQHandler(void) { usart_irq(&g_port[UART_PORT_BT]); }
void DMA1_Stream5_IRQHandler(void) { rx_dma_irq(&g_port[UART_PORT_BT]); }
void DMA1_Stream6_IRQHandler(void) { tx_dma_irq(&g_port[UART_PORT_BT]); }
