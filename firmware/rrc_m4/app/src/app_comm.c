/* 한글: 텔레메트리 팬아웃과 RRC 전송. RRC 모드: 호스트 UART(USART3 1Mbaud)가 RRC. MICROROS 모드: USART3은 micro-ROS, RRC는 USART1(115200)로 이동해 fallback/debug로 쓴다. 여러 태스크의 프레임이 섞이지 않도록 뮤텍스로 "프레임 단위 전체 또는 폐기"한다. */
/* Telemetry fan-out and the RRC transports. In COMM_MODE_RRC the RRC adapter owns the host UART
 * (USART3, 1 Mbaud, jetrover_base compatible). In COMM_MODE_MICROROS micro-ROS owns USART3 and the
 * RRC adapter moves to USART1 (115200, the ISP port) as Fallback/Debug. */
#include "app.h"
#include "drv_uart.h"
#include "FreeRTOS.h"
#include "semphr.h"
#include "task.h"

#if COMM_MODE == COMM_MODE_MICROROS
#include "comm_microros.h"
#endif

static StaticSemaphore_t g_tx_mtx_buf;
static SemaphoreHandle_t g_tx_mtx;

typedef struct {
    uart_port_id_t port;
} rrc_link_t;

/* All frames from all tasks go through here: whole frame or nothing, never interleaved. */
static void rrc_tx(void *ctx, const uint8_t *frame, size_t len)
{
    const rrc_link_t *l = ctx;
    StreamBufferHandle_t sb = drv_uart_tx_buffer(l->port);

    xSemaphoreTake(g_tx_mtx, portMAX_DELAY);
    if (xStreamBufferSpacesAvailable(sb) >= len) {
        drv_uart_write(l->port, frame, len);
    } else {
        (void)drv_uart_dropped; /* counted by drv_uart for partial writes; here the whole frame is dropped */
    }
    xSemaphoreGive(g_tx_mtx);
}

#if COMM_MODE == COMM_MODE_RRC
static rrc_link_t g_host_link = {UART_PORT_HOST};
#endif
#if COMM_MODE == COMM_MODE_MICROROS
static rrc_link_t g_aux_link = {UART_PORT_AUX};
#endif

void app_comm_init(void)
{
    g_tx_mtx = xSemaphoreCreateMutexStatic(&g_tx_mtx_buf);
#if COMM_MODE == COMM_MODE_RRC
    drv_uart_init(UART_PORT_HOST, 1000000);
    rrc_adapter_init(&g_app.rrc_host, &g_app.svc, rrc_tx, &g_host_link);
#else
    drv_uart_init(UART_PORT_HOST, 1000000); /* XRCE-DDS serial transport, see comm_microros.c */
    drv_uart_init(UART_PORT_AUX, 115200);
    rrc_adapter_init(&g_app.rrc_aux, &g_app.svc, rrc_tx, &g_aux_link);
#endif
}

#if COMM_MODE == COMM_MODE_RRC
#define RRC_PRIMARY (&g_app.rrc_host)
#else
#define RRC_PRIMARY (&g_app.rrc_aux)
#endif

void app_publish_imu(const float a[3], const float g[3])
{
    rrc_adapter_send_imu(RRC_PRIMARY, a, g);
#if COMM_MODE == COMM_MODE_MICROROS
    comm_microros_publish_imu(a, g);
#endif
}

void app_publish_battery(uint16_t mv)
{
    rrc_adapter_send_battery(RRC_PRIMARY, mv);
#if COMM_MODE == COMM_MODE_MICROROS
    comm_microros_publish_battery(mv);
#endif
}

void app_publish_key(uint8_t id, uint8_t ev)
{
    rrc_adapter_send_key(RRC_PRIMARY, id, ev);
}

void app_publish_gamepad(const gamepad_state_t *g)
{
    const rrc_gamepad_state_t r = {g->buttons, g->hat, g->lx, g->ly, g->rx, g->ry};
    rrc_adapter_send_gamepad(RRC_PRIMARY, &r);
}

void app_publish_sbus(const sbus_status_t *s)
{
    rrc_sbus_frame_t f;
    for (int i = 0; i < 16; i++) f.channels[i] = s->channels[i];
    f.ch17 = s->ch17;
    f.ch18 = s->ch18;
    f.signal_loss = s->signal_loss;
    f.fail_safe = s->fail_safe;
    rrc_adapter_send_sbus(RRC_PRIMARY, &f);
}

void app_publish_status(void)
{
    rrc_ext_status_t s = {0};
    const robot_ctrl_t *r = &g_app.robot;

    s.flags = (uint8_t)((r->estop ? RRC_STATUS_ESTOP : 0) | (r->moving ? RRC_STATUS_MOVING : 0) |
                        (r->low_battery ? RRC_STATUS_LOW_BATTERY : 0) | (r->enabled ? RRC_STATUS_MOTOR_ENABLED : 0));
    for (int i = 0; i < 4; i++) {
        s.motor_fault[i] = g_app.motors[i].fault;
        if (g_app.motors[i].fault) s.flags |= RRC_STATUS_MOTOR_FAULT;
    }
    s.stop_reason = r->stop_reason;
    s.imu_kind = g_app.imu_ok ? (uint8_t)g_app.imu.kind : 0;
    s.comm_mode = COMM_MODE;
    s.uptime_ms = app_now_ms();
    s.reset_cause = g_app.reset_cause;
    rrc_adapter_send_status(RRC_PRIMARY, &s);
#if COMM_MODE == COMM_MODE_MICROROS
    comm_microros_publish_status(&s);
#endif
}

void app_publish_wheel(void)
{
    rrc_ext_wheel_t w;
    for (int i = 0; i < 4; i++) {
        w.rps[i] = g_app.motors[i].rps;
        w.counter[i] = (int32_t)g_app.motors[i].counter;
    }
    rrc_adapter_send_wheel(RRC_PRIMARY, &w);
#if COMM_MODE == COMM_MODE_MICROROS
    comm_microros_publish_wheel(&w);
#endif
}

void app_publish_raw_hid(const uint8_t *report, size_t len)
{
    rrc_adapter_send_raw_hid(RRC_PRIMARY, report, len);
}

/* Feed bytes of the active RRC link (called by the comm RX task). */
void app_rrc_feed(const uint8_t *data, size_t len)
{
    rrc_adapter_feed(RRC_PRIMARY, data, len);
}

uart_port_id_t app_rrc_port(void)
{
#if COMM_MODE == COMM_MODE_RRC
    return UART_PORT_HOST;
#else
    return UART_PORT_AUX;
#endif
}
