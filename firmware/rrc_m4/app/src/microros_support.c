/* 한글: micro-ROS용 FreeRTOS 연결부: 할당자(realloc이 없는 heap_4를 위해 크기 헤더 사용), clock_gettime, 호스트 UART 위 커스텀 시리얼 전송. */
/* micro-ROS platform glue for FreeRTOS: allocators on the FreeRTOS heap, clock_gettime, and the
 * custom serial transport on the host UART (USART3, 1 Mbaud, DMA/IDLE stream buffers). */
#include <rmw_microros/rmw_microros.h>
#include <rcutils/allocator.h>
#include <time.h>
#include <string.h>

#include "FreeRTOS.h"
#include "drv_uart.h"
#include "task.h"

/* ---------- allocators (heap_4 has no realloc: keep the size in a header) ---------- */
typedef struct {
    size_t size;
    size_t pad; /* keeps user data 8-byte aligned */
} alloc_hdr_t;

static void *uros_allocate(size_t size, void *state)
{
    (void)state;
    alloc_hdr_t *h = pvPortMalloc(size + sizeof(alloc_hdr_t));
    if (!h) {
        return NULL;
    }
    h->size = size;
    return h + 1;
}

static void uros_deallocate(void *p, void *state)
{
    (void)state;
    if (p) {
        vPortFree((alloc_hdr_t *)p - 1);
    }
}

static void *uros_reallocate(void *p, size_t size, void *state)
{
    if (!p) {
        return uros_allocate(size, state);
    }
    alloc_hdr_t *old = (alloc_hdr_t *)p - 1;
    if (size <= old->size) {
        return p;
    }
    void *n = uros_allocate(size, state);
    if (n) {
        memcpy(n, p, old->size);
        uros_deallocate(p, state);
    }
    return n;
}

static void *uros_zero_allocate(size_t n, size_t size, void *state)
{
    void *p = uros_allocate(n * size, state);
    if (p) {
        memset(p, 0, n * size);
    }
    return p;
}

void microros_set_allocators(void)
{
    rcutils_allocator_t a = rcutils_get_zero_initialized_allocator();
    a.allocate = uros_allocate;
    a.deallocate = uros_deallocate;
    a.reallocate = uros_reallocate;
    a.zero_allocate = uros_zero_allocate;
    a.state = NULL;
    if (rcutils_set_default_allocator(&a) != true) { for (;;) { } }
}

/* ---------- time: the XRCE client needs a monotonic clock ---------- */
int clock_gettime(clockid_t clk_id, struct timespec *tp)
{
    (void)clk_id;
    const TickType_t ticks = xTaskGetTickCount();
    const uint64_t ms = (uint64_t)ticks * portTICK_PERIOD_MS;
    tp->tv_sec = (time_t)(ms / 1000U);
    tp->tv_nsec = (long)((ms % 1000U) * 1000000UL);
    return 0;
}

/* ---------- custom serial transport (HDLC framing is done by the XRCE client) ---------- */
static bool transport_open(struct uxrCustomTransport *t)
{
    (void)t;
    drv_uart_flush_rx(UART_PORT_HOST);
    return true;
}

static bool transport_close(struct uxrCustomTransport *t)
{
    (void)t;
    return true;
}

static size_t transport_write(struct uxrCustomTransport *t, const uint8_t *buf, size_t len, uint8_t *err)
{
    (void)t;
    size_t sent = 0;
    TickType_t waited = 0;
    while (sent < len) {
        const size_t n = drv_uart_write(UART_PORT_HOST, buf + sent, len - sent);
        sent += n;
        if (n == 0) { /* TX buffer full: let the TX task drain (bounded wait) */
            vTaskDelay(1);
            if (++waited > pdMS_TO_TICKS(50)) {
                *err = 1;
                break;
            }
        }
    }
    return sent;
}

static size_t transport_read(struct uxrCustomTransport *t, uint8_t *buf, size_t len, int timeout, uint8_t *err)
{
    (void)t;
    (void)err;
    return drv_uart_read(UART_PORT_HOST, buf, len, timeout <= 0 ? 0 : pdMS_TO_TICKS((uint32_t)timeout));
}

void microros_transport_init(void)
{
    rmw_uros_set_custom_transport(true /* framing */, NULL, transport_open, transport_close, transport_write,
                                  transport_read);
}
