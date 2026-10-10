/* 한글: 싱글톤 생성과 robot_services_t 연결(통신 계층이 하드웨어에 요청할 수 있는 것들의 구현). */
/* Singleton construction and the robot_services_t table (what the comm layers may ask the hardware). */
#include "app.h"

#include "FreeRTOS.h"
#include "drv_bus_servo.h"
#include "drv_misc.h"
#include "drv_motor.h"
#include "system.h"
#include "task.h"

app_t g_app;

uint32_t app_now_ms(void) { return (uint32_t)(xTaskGetTickCount() * portTICK_PERIOD_MS); }

void app_safe_state(void) { drv_motor_all_off(); }

/* ---- services ---- */
static uint32_t svc_now(void *hw) { (void)hw; return app_now_ms(); }

static void svc_led(void *hw, uint8_t id, uint16_t on, uint16_t off, uint16_t cycles)
{
    (void)hw;
    (void)id; /* the board has a single user LED */
    blink_set(&g_app.led, on, off, cycles);
}

static void svc_buzzer(void *hw, uint16_t freq, uint16_t on, uint16_t off, uint16_t cycles)
{
    (void)hw;
    (void)freq; /* active buzzer assumed: frequency has no effect (PINMAP.md) */
    blink_set(&g_app.buzzer, on, off, cycles);
}

static void svc_servo_move(void *hw, uint8_t idx, uint16_t pulse, uint16_t time_ms)
{
    (void)hw;
    pwm_servo_set_position(&g_app.servo[idx], pulse, time_ms);
    drv_pwm_servo_enable();
}

static int svc_servo_get(void *hw, uint8_t idx, uint16_t *pulse)
{
    (void)hw;
    *pulse = (uint16_t)g_app.servo[idx].current_duty;
    return 0;
}

static void svc_servo_set_off(void *hw, uint8_t idx, int8_t off)
{
    (void)hw;
    pwm_servo_set_offset(&g_app.servo[idx], off);
}

static int svc_servo_get_off(void *hw, uint8_t idx, int8_t *off)
{
    (void)hw;
    *off = (int8_t)g_app.servo[idx].offset;
    return 0;
}

static void svc_bus_move(void *hw, uint8_t id, uint16_t pulse, uint16_t ms)
{
    (void)hw;
    drv_bus_servo_move(id, pulse, ms);
}

static int svc_bus_xfer(void *hw, const bus_servo_plan_t *plan, uint8_t *reply, uint8_t *rl)
{
    (void)hw;
    return drv_bus_servo_xfer(plan, reply, rl);
}

static void svc_set_pid(void *hw, uint8_t motor, float kp, float ki, float kd)
{
    (void)hw;
    for (uint8_t i = 0; i < 4; i++) {
        if (motor == 0xFF || motor == i) {
            g_app.motors[i].pid.kp = kp;
            g_app.motors[i].pid.ki = ki;
            g_app.motors[i].pid.kd = kd;
        }
    }
}

/* 한글: 진단용 개루프 PWM(바퀴를 띄운 시험 전용). 500ms 안에 갱신이 없으면 자동 해제된다. */
static void svc_raw_pwm(void *hw, uint8_t motor, int16_t pulse)
{
    (void)hw;
#if MOTOR_ENABLE
    if (motor < 4 && !g_app.robot.estop) {
        g_app.raw_pwm[motor] = pulse;
        g_app.raw_pwm_until_ms[motor] = app_now_ms() + 500; /* auto-expires: needs a stream of commands */
    }
#else
    (void)motor;
    (void)pulse;
#endif
}

static void svc_request_status(void *hw)
{
    (void)hw;
    app_publish_status();
    app_publish_diag(); /* task stacks + counters (0x24) / 스택 여유와 카운터 */
}

static void motor_pulse(void *ctx, int pulse) { drv_motor_set_pulse((uint8_t)(uintptr_t)ctx, pulse); }

void app_init(void)
{
    static const int8_t sign[4] = MOTOR_ENCODER_SIGN;
    static const mecanum_cfg_t mecanum = {ROBOT_WHEELBASE_M, ROBOT_TRACK_WIDTH_M, ROBOT_WHEEL_DIAMETER_M};
    enc_motor_t *mp[4];

    for (int i = 0; i < 4; i++) {
        enc_motor_init(&g_app.motors[i], MOTOR_TICKS_PER_CIRCLE, MOTOR_RPS_LIMIT, MOTOR_PID_KP, MOTOR_PID_KI,
                       MOTOR_PID_KD, MOTOR_ENCODER_TIM_OVERFLOW, sign[i], motor_pulse,
                       (void *)(uintptr_t)i);
        mp[i] = &g_app.motors[i];
    }
    robot_init(&g_app.robot, mp, &mecanum, MOTOR_ENABLE);
    g_app.robot.cmd_timeout_ms = CMD_TIMEOUT_MS;
    g_app.robot.low_battery_mv = LOW_BATTERY_CUTOFF_MV;
    g_app.robot.low_battery_clear_mv = LOW_BATTERY_CLEAR_MV;

    battery_init(&g_app.battery);
    blink_init(&g_app.led);
    blink_init(&g_app.buzzer);
    button_init(&g_app.button[0]);
    button_init(&g_app.button[1]);
    for (int i = 0; i < PWM_SERVO_COUNT; i++) {
        pwm_servo_init(&g_app.servo[i]);
    }
    local_drive_init(&g_app.local, &g_app.robot);

    g_app.svc = (robot_services_t){
        .robot = &g_app.robot,
        .hw = NULL,
        .now_ms = svc_now,
        .led_set = svc_led,
        .buzzer_set = svc_buzzer,
        .pwm_servo_move = svc_servo_move,
        .pwm_servo_get_pulse = svc_servo_get,
        .pwm_servo_set_offset = svc_servo_set_off,
        .pwm_servo_get_offset = svc_servo_get_off,
        .bus_servo_move = svc_bus_move,
        .bus_servo_xfer = svc_bus_xfer,
        .set_pid = svc_set_pid,
        .raw_pwm = svc_raw_pwm,
        .request_status = svc_request_status,
    };
    g_app.reset_cause = system_reset_cause();
}
