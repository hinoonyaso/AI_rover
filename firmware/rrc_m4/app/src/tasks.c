/* 한글: FreeRTOS 태스크들(정적 할당, 스택은 CCM). supervisor가 control/imu/comm_rx/ui heartbeat를 모두 확인할 때만 IWDG를 먹인다 — 벤더 펌웨어의 "app_task만 20ms 워치독을 먹이는" 약점(troubleshooting/001) 대응. */
/* FreeRTOS tasks. Every task is statically allocated (stacks in CCM). A supervisor task feeds the IWDG
 * only while all critical tasks keep making progress - this is the fix for the stock firmware's
 * "app_task alone feeds a 20 ms watchdog" weakness (troubleshooting/001). */
#include <stdio.h>
#include <string.h>

#include "FreeRTOS.h"
#include "app.h"
#include "board.h"
#include "drv_bus_servo.h"
#include "drv_imu.h"
#include "drv_lcd.h"
#include "drv_misc.h"
#include "drv_motor.h"
#include "drv_uart.h"
#include "semphr.h"
#include "system.h"
#include "usb_gamepad.h"
#include "task.h"

#if COMM_MODE == COMM_MODE_MICROROS
#include "comm_microros.h"
#endif

#define CCM __attribute__((section(".ccmbss")))

typedef struct {
    StaticTask_t tcb;
    StackType_t *stack;
    TaskHandle_t handle;
} task_slot_t;

#define DECLARE_TASK(name, words) \
    static StackType_t name##_stack[words] CCM; \
    static task_slot_t name##_slot = {.stack = name##_stack}

#define START_TASK(fn, name, words, prio, slot) \
    do { (slot).handle = xTaskCreateStatic(fn, name, words, NULL, prio, (slot).stack, &(slot).tcb); \
         configASSERT((slot).handle); } while (0)

DECLARE_TASK(control, 512);
DECLARE_TASK(imu, 512);
DECLARE_TASK(rx, 768);
DECLARE_TASK(tx, 384);
DECLARE_TASK(ui, 768);
DECLARE_TASK(lcd, 640);
DECLARE_TASK(sbus, 384);
DECLARE_TASK(bt, 384);
DECLARE_TASK(sup, 384);
DECLARE_TASK(usb, 640);
#if COMM_MODE == COMM_MODE_MICROROS
DECLARE_TASK(uros, 3072); /* 12 KB: micro-ROS recommends >= 10 KB */
DECLARE_TASK(hosttx, 384);
#endif

static IWDG_HandleTypeDef g_iwdg;

/* ===================================================================== */
/* control: 10 ms, woken by TIM7                                          */
/* ===================================================================== */
/* 한글: 제어 태스크(10ms, TIM7 알림으로 깨어남): 엔코더 읽기→robot_tick→모터별 PID. 틱이 50ms 넘게 없으면 heartbeat를 올리지 않아 supervisor가 알아챈다. */
static void control_task(void *arg)
{
    (void)arg;
    drv_motor_start_tick(control_slot.handle);
    for (;;) {
        if (ulTaskNotifyTake(pdTRUE, pdMS_TO_TICKS(50)) == 0) {
            continue; /* no tick: do not beat, the supervisor will notice */
        }
        const uint32_t now = app_now_ms();
        const int fault = drv_motor_fault_active();

        taskENTER_CRITICAL();
        for (uint8_t i = 0; i < 4; i++) {
            enc_motor_update(&g_app.motors[i], 0.01f, drv_motor_read_counter(i));
        }
        taskEXIT_CRITICAL();

        robot_tick(&g_app.robot, now);
        for (uint8_t i = 0; i < 4; i++) {
            if (g_app.raw_pwm[i] != 0) {
                if ((int32_t)(now - g_app.raw_pwm_until_ms[i]) > 0 || g_app.robot.estop) {
                    g_app.raw_pwm[i] = 0;
                    drv_motor_set_pulse(i, 0);
                } else {
                    drv_motor_set_pulse(i, g_app.raw_pwm[i]); /* open loop, diagnostics only */
                }
                continue;
            }
            enc_motor_control(&g_app.motors[i], 0.01f, fault);
        }
        hb_beat(HB_CONTROL);
    }
}

/* ===================================================================== */
/* IMU                                                                    */
/* ===================================================================== */
/* 한글: IMU 태스크: 데이터 준비 인터럽트(없으면 20ms 폴링)로 읽어 텔레메트리로 보낸다. 센서가 없으면 2초마다 재탐색하며 heartbeat는 계속 올린다. */
static void imu_task(void *arg)
{
    (void)arg;
    float a[3], g[3];
    int fails = 0;

    g_app.imu_ok = (drv_imu_init(&g_app.imu) == 0);
    for (;;) {
        if (!g_app.imu_ok) { /* keep beating; retry the probe every 2 s so a late/replugged sensor is found */
            vTaskDelay(pdMS_TO_TICKS(2000));
            g_app.imu_ok = (drv_imu_init(&g_app.imu) == 0);
            hb_beat(HB_IMU);
            continue;
        }
        /* data-ready interrupt, or poll at ~100 Hz if the INT line is not wired/available */
        xSemaphoreTake(drv_imu_drdy(), pdMS_TO_TICKS(20));
        if (imu_read(&g_app.imu, a, g) == 0) {
            fails = 0;
            g_app.imu_samples++;
            app_publish_imu(a, g);
        } else {
            g_app.imu_errors++;
            if (++fails >= 10) {
                drv_imu_bus_recover();
                g_app.imu_ok = (drv_imu_init(&g_app.imu) == 0);
                fails = 0;
            }
            vTaskDelay(pdMS_TO_TICKS(5));
        }
        hb_beat(HB_IMU);
    }
}

/* ===================================================================== */
/* communication                                                          */
/* ===================================================================== */
static void rx_task(void *arg)
{
    (void)arg;
    uint8_t buf[128];
    for (;;) {
        const size_t n = drv_uart_read(app_rrc_port(), buf, sizeof(buf), pdMS_TO_TICKS(20));
        if (n) {
            app_rrc_feed(buf, n);
        }
        hb_beat(HB_COMM_RX);
    }
}

#if COMM_MODE == COMM_MODE_MICROROS
static void host_tx_task(void *arg)
{
    (void)arg;
    drv_uart_tx_poll(UART_PORT_HOST); /* drains the XRCE transport's TX stream buffer */
}
#endif

static void tx_task(void *arg)
{
    (void)arg;
    /* drv_uart_tx_poll blocks forever; heartbeat comes from the UI task for TX health */
    drv_uart_tx_poll(app_rrc_port());
}

/* ===================================================================== */
/* UI / periodic services: buttons, LED, buzzer, servos, battery, status   */
/* ===================================================================== */
/* 한글: UI/주기 서비스(10ms): LED·부저 패턴, 버튼 이벤트, 서보 램프(20ms), 배터리 변환(50ms), 엔코더/상태/배터리 텔레메트리. */
static void ui_task(void *arg)
{
    (void)arg;
    TickType_t last = xTaskGetTickCount();
    uint32_t n = 0;
    uint16_t vref = 0, pb0 = 0;

    drv_battery_trigger();
    for (;;) {
        vTaskDelayUntil(&last, pdMS_TO_TICKS(10));
        n++;

        drv_led_write(blink_tick(&g_app.led, 10));
        drv_buzzer_write(blink_tick(&g_app.buzzer, 10));

        for (uint8_t k = 0; k < 2; k++) {
            const uint8_t ev = button_tick(&g_app.button[k], (uint8_t)drv_key_pressed(k), 10);
            for (uint8_t bit = 0x01; bit; bit = (uint8_t)(bit << 1)) {
                if (ev & bit) {
                    app_publish_key((uint8_t)(k + 1), bit);
                    if (bit == BUTTON_EVENT_CLICK) {
                        blink_set(&g_app.buzzer, 50, 50, 1); /* vendor beeps on click */
                    }
                }
            }
        }

        if (n % 2 == 0) { /* 20 ms */
            for (int i = 0; i < PWM_SERVO_COUNT; i++) {
                pwm_servo_tick(&g_app.servo[i]);
                drv_pwm_servo_set_pulse((uint8_t)i, (uint16_t)g_app.servo[i].duty_raw);
            }
        }
        if (n % 5 == 0) { /* 50 ms */
            drv_battery_get(&vref, &pb0);
            if (battery_update(&g_app.battery, vref, pb0)) {
                robot_update_battery(&g_app.robot, g_app.battery.millivolts);
            }
            drv_battery_trigger();
        }
        if (n % (WHEEL_PERIOD_MS / 10) == 0) {
            app_publish_wheel();
        }
        if (n % (STATUS_PERIOD_MS / 10) == 0) {
            app_publish_status();
        }
        if (n % 50 == 0 && g_app.battery.valid) { /* 2 Hz */
            app_publish_battery(g_app.battery.millivolts);
        }
        hb_beat(HB_UI);
    }
}

/* ===================================================================== */
/* LCD status page (low priority, never touches control state)             */
/* ===================================================================== */
static void lcd_task(void *arg)
{
    (void)arg;
    char line[48]; /* longer than a display row: drv_lcd_print stops at LCD_COLS / 한 줄보다 길게, 출력 때 잘림 */

    if (drv_lcd_init() != 0) {
        vTaskDelete(NULL);
    }
    for (;;) {
        /* 128x32 OLED: 4 lines x 21 chars (2026-10-10, was 7 lines for the assumed 80x160 LCD).
         * 한글: 128x32 OLED라 4줄 x 21자로 줄임. */
        const robot_ctrl_t *r = &g_app.robot;
        snprintf(line, sizeof(line), "RRC-M4 %s %lus R%02lX", COMM_MODE == COMM_MODE_MICROROS ? "UROS" : "RRC",
                 (unsigned long)(app_now_ms() / 1000), (unsigned long)g_app.reset_cause);
        drv_lcd_print(0, line, LCD_WHITE, LCD_BLACK);
        snprintf(line, sizeof(line), "BAT %u.%03uV%s", g_app.battery.millivolts / 1000, g_app.battery.millivolts % 1000,
                 g_app.robot.low_battery ? " LOW" : "");
        drv_lcd_print(1, line, LCD_WHITE, g_app.robot.low_battery ? LCD_WHITE : LCD_BLACK);
        snprintf(line, sizeof(line), "IMU %s", g_app.imu_ok ? (g_app.imu.kind == IMU_MPU6050 ? "MPU6050" : "QMI8658") : "NONE");
        drv_lcd_print(2, line, LCD_WHITE, g_app.imu_ok ? LCD_BLACK : LCD_WHITE);
        snprintf(line, sizeof(line), "MOT %s %s F%d%d%d%d", r->enabled ? "EN" : "OFF", r->estop ? "ESTOP" : (r->moving ? "RUN" : "IDLE"),
                 g_app.motors[0].fault, g_app.motors[1].fault, g_app.motors[2].fault, g_app.motors[3].fault);
        drv_lcd_print(3, line, LCD_WHITE, r->estop ? LCD_WHITE : LCD_BLACK);
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}

/* ===================================================================== */
/* SBUS (UART5, 100000 baud 8E2 -> 9 bit word with parity in HAL)          */
/* ===================================================================== */
static UART_HandleTypeDef g_huart5;
static DMA_HandleTypeDef g_hdma_uart5;
static uint8_t g_sbus_dma[128];

static void sbus_hw_init(void)
{
    GPIO_InitTypeDef g = {0};
    __HAL_RCC_GPIOD_CLK_ENABLE();
    __HAL_RCC_UART5_CLK_ENABLE();
    __HAL_RCC_DMA1_CLK_ENABLE();
    g.Pin = GPIO_PIN_2;
    g.Mode = GPIO_MODE_AF_PP;
    g.Pull = GPIO_PULLUP;
    g.Speed = GPIO_SPEED_FREQ_HIGH;
    g.Alternate = GPIO_AF8_UART5;
    HAL_GPIO_Init(GPIOD, &g);

    g_hdma_uart5.Instance = DMA1_Stream0;
    g_hdma_uart5.Init.Channel = DMA_CHANNEL_4;
    g_hdma_uart5.Init.Direction = DMA_PERIPH_TO_MEMORY;
    g_hdma_uart5.Init.PeriphInc = DMA_PINC_DISABLE;
    g_hdma_uart5.Init.MemInc = DMA_MINC_ENABLE;
    g_hdma_uart5.Init.PeriphDataAlignment = DMA_PDATAALIGN_BYTE;
    g_hdma_uart5.Init.MemDataAlignment = DMA_MDATAALIGN_BYTE;
    g_hdma_uart5.Init.Mode = DMA_CIRCULAR;
    g_hdma_uart5.Init.Priority = DMA_PRIORITY_LOW;
    g_hdma_uart5.Init.FIFOMode = DMA_FIFOMODE_DISABLE;
    HAL_DMA_Init(&g_hdma_uart5);
    __HAL_LINKDMA(&g_huart5, hdmarx, g_hdma_uart5);

    g_huart5.Instance = SBUS_UART;
    g_huart5.Init.BaudRate = 100000;
    g_huart5.Init.WordLength = UART_WORDLENGTH_9B; /* 8 data + even parity */
    g_huart5.Init.StopBits = UART_STOPBITS_2;
    g_huart5.Init.Parity = UART_PARITY_EVEN;
    g_huart5.Init.Mode = UART_MODE_RX;
    g_huart5.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    g_huart5.Init.OverSampling = UART_OVERSAMPLING_16;
    HAL_UART_Init(&g_huart5);
    HAL_UART_Receive_DMA(&g_huart5, g_sbus_dma, sizeof(g_sbus_dma));
}

/* 한글: SBUS 태스크: 원형 DMA 버퍼를 5ms마다 폴링해 파싱(ISR 불필요). 호스트로는 최대 50Hz. */
static void sbus_task(void *arg)
{
    (void)arg;
    sbus_stream_t st;
    sbus_status_t s;
    uint16_t last = 0;
    uint32_t last_pub = 0;

    sbus_hw_init();
    sbus_stream_init(&st);
    for (;;) {
        vTaskDelay(pdMS_TO_TICKS(5)); /* polls the circular DMA buffer: no ISR needed */
        const uint16_t pos = (uint16_t)(sizeof(g_sbus_dma) - __HAL_DMA_GET_COUNTER(&g_hdma_uart5));
        while (last != pos) {
            if (sbus_stream_feed(&st, g_sbus_dma[last], &s)) {
                const uint32_t now = app_now_ms();
                if (now - last_pub >= 20) { /* <= 50 Hz to the host */
                    last_pub = now;
                    app_publish_sbus(&s);
                }
#if LOCAL_DRIVE_ENABLE
                if (!s.signal_loss && !s.fail_safe) { /* vendor mapping: left stick = channels 3 (x) / 2 (y), centre 992 */
                    const char c = local_drive_atc(s.channels[3] - 992, s.channels[2] - 992, 400);
                    local_drive_char(&g_app.local, c, now, ROBOT_SRC_SBUS);
                }
#endif
            }
            last = (uint16_t)((last + 1) % sizeof(g_sbus_dma));
        }
    }
}

/* ===================================================================== */
/* Bluetooth app (USART2, 9600): character protocol + battery report       */
/* ===================================================================== */
/* 한글: 블루투스 태스크: 한 글자 명령 수신, 배터리 "VxxxxV" 문자열을 1초마다 송신. */
static void bt_task(void *arg)
{
    (void)arg;
    uint8_t b[16];
    uint32_t last_report = 0;

    drv_uart_init(UART_PORT_BT, 9600);
    for (;;) {
        const size_t n = drv_uart_read(UART_PORT_BT, b, sizeof(b), pdMS_TO_TICKS(100));
        const uint32_t now = app_now_ms();
#if LOCAL_DRIVE_ENABLE
        for (size_t i = 0; i < n; i++) {
            local_drive_char(&g_app.local, (char)b[i], now, ROBOT_SRC_BLUETOOTH);
        }
#else
        (void)n;
#endif
        if (now - last_report >= 1000 && g_app.battery.valid) { /* app expects "VxxxxV" once a second */
            char msg[12];
            const int len = snprintf(msg, sizeof(msg), "V%uV", g_app.battery.millivolts);
            drv_uart_write(UART_PORT_BT, (const uint8_t *)msg, (size_t)len);
            last_report = now;
        }
        {
            uint8_t out[32];
            const size_t m = xStreamBufferReceive(drv_uart_tx_buffer(UART_PORT_BT), out, sizeof(out), 0);
            if (m) {
                drv_uart_send_blocking(UART_PORT_BT, out, m); /* a few bytes per second: no DMA task needed */
            }
        }
    }
}

/* ===================================================================== */
/* USB gamepad report -> FUNC8 (+ raw FUNC 0x23, rate limited, to confirm the layout)  */
/* ===================================================================== */
/* 한글: 게임패드 리포트 콜백: 원시 리포트(FUNC 0x23, 100ms 제한)와 해석 결과(FUNC8, 50Hz 제한)를 올린다. */
static void gamepad_report(const uint8_t *report, size_t len)
{
    static uint8_t last_report[32];
    static uint32_t last_raw_ms, last_pub_ms;
    static gamepad_state_t last;
    gamepad_state_t g;
    const uint32_t now = app_now_ms();

    if (now - last_raw_ms >= 100 && (len != sizeof(last_report) || memcmp(report, last_report, len < 32 ? len : 32) != 0)) {
        last_raw_ms = now;
        memcpy(last_report, report, len < sizeof(last_report) ? len : sizeof(last_report));
        app_publish_raw_hid(report, len);
    }
    if (gamepad_parse_report(&GAMEPAD_LAYOUT_DEFAULT, report, len, &g) != 0) {
        return;
    }
    if (now - last_pub_ms >= 20) { /* <= 50 Hz */
        last_pub_ms = now;
        app_publish_gamepad(&g);
    }
#if LOCAL_DRIVE_ENABLE
    {
        char c = local_drive_hat_char(g.hat);
        if (c == 'I') c = local_drive_atc(g.lx, g.ly, 60);
        local_drive_char(&g_app.local, c, now, ROBOT_SRC_GAMEPAD);
        if ((g.buttons & GAMEPAD_MASK_START) && !(last.buttons & GAMEPAD_MASK_START)) local_drive_char(&g_app.local, 'S', now, ROBOT_SRC_GAMEPAD);
        if ((g.buttons & GAMEPAD_MASK_SELECT) && !(last.buttons & GAMEPAD_MASK_SELECT)) local_drive_char(&g_app.local, 'j', now, ROBOT_SRC_GAMEPAD);
    }
#endif
    (void)last;
#if LOCAL_DRIVE_ENABLE
    last = g;
#endif
}

/* ===================================================================== */
/* supervisor + watchdog                                                   */
/* ===================================================================== */
typedef struct {
    hb_id_t id;
    uint32_t deadline_ms;
    uint32_t last_value, last_change_ms;
} hb_watch_t;

static hb_watch_t g_watch[] = {
    {HB_CONTROL, 100, 0, 0},
    {HB_IMU, 3000, 0, 0},   /* tolerant: sensor-less boards keep beating at 0.5 Hz */
    {HB_COMM_RX, 200, 0, 0},
    {HB_UI, 200, 0, 0},
};

/* 한글: 감독 태스크(최고 우선순위): 모든 heartbeat가 마감 내에 갱신될 때만 IWDG를 먹인다. 하나라도 멈추면 모터 PWM을 즉시 0으로 하고 리셋을 기다린다. */
static void sup_task(void *arg)
{
    (void)arg;
    TickType_t last = xTaskGetTickCount();

    for (;;) {
        vTaskDelayUntil(&last, pdMS_TO_TICKS(25));
        const uint32_t now = app_now_ms();
        int healthy = 1;
        for (size_t i = 0; i < sizeof(g_watch) / sizeof(g_watch[0]); i++) {
            hb_watch_t *w = &g_watch[i];
            const uint32_t v = g_app.hb[w->id];
            if (v != w->last_value) {
                w->last_value = v;
                w->last_change_ms = now;
            } else if (now - w->last_change_ms > w->deadline_ms) {
                healthy = 0;
            }
        }
        if (healthy) {
            HAL_IWDG_Refresh(&g_iwdg);
        } else {
            drv_motor_all_off(); /* wheels stop immediately; no refresh -> IWDG resets the MCU */
        }
    }
}

static void iwdg_start(void)
{
    g_iwdg.Instance = IWDG;
    g_iwdg.Init.Prescaler = IWDG_PRESCALER_32; /* 32 kHz LSI / 32 = 1 kHz */
    g_iwdg.Init.Reload = IWDG_TIMEOUT_MS - 1;
    HAL_IWDG_Init(&g_iwdg);
}

/* ===================================================================== */
void vApplicationIdleHook(void) {}

void app_create_tasks(void)
{
    app_comm_init();
    drv_gpio_safe_init();
    drv_i2c_shared_init(); /* IMU + OLED bus and its mutex, before any task touches it */
    drv_motor_init((enc_motor_t *[]){&g_app.motors[0], &g_app.motors[1], &g_app.motors[2], &g_app.motors[3]});
    drv_battery_init();
    drv_pwm_servo_init();
    drv_bus_servo_init();

    START_TASK(control_task, "control", 512, 6, control_slot);
    START_TASK(imu_task, "imu", 512, 5, imu_slot);
    START_TASK(rx_task, "comm_rx", 768, 4, rx_slot);
    START_TASK(tx_task, "comm_tx", 384, 3, tx_slot);
    START_TASK(ui_task, "ui", 768, 3, ui_slot);
    START_TASK(lcd_task, "lcd", 640, 1, lcd_slot);
    START_TASK(sbus_task, "sbus", 384, 2, sbus_slot);
    usb_gamepad_set_cb(gamepad_report);
    START_TASK(usb_gamepad_task, "usb", 640, 2, usb_slot);
    START_TASK(bt_task, "bt", 384, 2, bt_slot);
#if COMM_MODE == COMM_MODE_MICROROS
    START_TASK(comm_microros_task, "uros", 3072, 4, uros_slot);
    START_TASK(host_tx_task, "host_tx", 384, 3, hosttx_slot);
#endif
    START_TASK(sup_task, "supervisor", 384, 7, sup_slot);
    iwdg_start();
}
