/* 한글: 애플리케이션 싱글톤과 태스크 간 연결. 드라이버는 drv_*.c, 이식 가능한 로직은 lib/core. */
/* Application singletons and the cross-task glue. Hardware drivers are in drv_*.c; portable logic in lib/core. */
#ifndef APP_H
#define APP_H

#include <stdint.h>

#include "app_config.h"
#include "comm/rrc_adapter.h"
#include "comm/robot_services.h"
#include "core/battery.h"
#include "core/blink.h"
#include "core/button.h"
#include "core/encoder_motor.h"
#include "core/gamepad.h"
#include "core/imu.h"
#include "core/local_drive.h"
#include "core/pwm_servo.h"
#include "core/robot_ctrl.h"
#include "core/sbus.h"

typedef enum {
    HB_CONTROL = 0,
    HB_IMU,
    HB_COMM_RX,
    HB_COMM_TX,
    HB_UI,
    HB_COUNT
} hb_id_t;

typedef struct {
    enc_motor_t motors[4];
    robot_ctrl_t robot;
    imu_t imu;
    uint8_t imu_ok;
    battery_t battery;
    blink_t led, buzzer;
    button_t button[2];
    pwm_servo_t servo[PWM_SERVO_COUNT];
    local_drive_t local;
    robot_services_t svc;
    rrc_adapter_t rrc_host; /* RRC mode: on the host UART. MICROROS mode: not used */
    rrc_adapter_t rrc_aux;  /* MICROROS mode: fallback/debug RRC on USART1 */
    volatile uint32_t hb[HB_COUNT];
    volatile int16_t raw_pwm[4];
    volatile uint32_t raw_pwm_until_ms[4];
    uint32_t reset_cause;
    uint32_t boot_ms;
    volatile uint32_t imu_samples;
    volatile uint32_t imu_errors;
} app_t;

extern app_t g_app;

static inline void hb_beat(hb_id_t id) { g_app.hb[id]++; }
uint32_t app_now_ms(void);

/* ---- telemetry fan-out (RRC and/or micro-ROS), implemented in app_comm.c ---- */
void app_publish_imu(const float accel_g[3], const float gyro_dps[3]);
void app_publish_battery(uint16_t mv);
void app_publish_key(uint8_t id, uint8_t ev);
void app_publish_gamepad(const gamepad_state_t *g);
void app_publish_sbus(const sbus_status_t *s);
void app_publish_status(void);
void app_publish_wheel(void);
void app_publish_raw_hid(const uint8_t *report, size_t len);

/* ---- init / tasks ---- */
void app_init(void);               /* builds singletons + services, no RTOS objects started */
void app_create_tasks(void);
void app_safe_state(void);         /* register-only: motors off */

/* implemented in tasks.c */
void app_services_init(void);

#endif

void app_comm_init(void);
void app_rrc_feed(const uint8_t *data, size_t len);
#include "drv_uart.h"
uart_port_id_t app_rrc_port(void);
