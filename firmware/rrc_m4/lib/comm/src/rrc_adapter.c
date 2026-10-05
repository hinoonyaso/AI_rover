/* 한글: RRC 어댑터 구현. 수신 프레임을 FUNC별로 분기해 robot_services를 호출하고, 응답/텔레메트리는 tx 콜백으로 내보낸다. */
#include "comm/rrc_adapter.h"

#include <string.h>

void rrc_adapter_init(rrc_adapter_t *a, const robot_services_t *svc,
                      void (*tx)(void *, const uint8_t *, size_t), void *tx_ctx)
{
    memset(a, 0, sizeof(*a));
    a->svc = svc;
    a->tx = tx;
    a->tx_ctx = tx_ctx;
    rrc_parser_init(&a->parser);
}

static void send_frame(rrc_adapter_t *a, uint8_t func, const uint8_t *data, size_t len)
{
    uint8_t frame[RRC_MAX_FRAME_LEN];
    const size_t n = rrc_encode(func, data, len, frame);
    if (n && a->tx) {
        a->tx(a->tx_ctx, frame, n);
    }
}

static uint32_t now(const robot_services_t *s)
{
    return s->now_ms ? s->now_ms(s->hw) : 0;
}

/* ---- incoming ---- */

/* 한글: FUNC3: 단일/다중 속도 설정, 한 개/마스크 정지. 모터 ID는 0부터(펌웨어 확정 사실). 범위 밖 ID는 robot_ctrl이 무시한다. */
static void on_motor(rrc_adapter_t *a, const rrc_frame_t *f)
{
    rrc_motor_cmd_ex_t m;
    const robot_services_t *s = a->svc;

    if (!rrc_unpack_motor_ex(f->data, f->data_len, &m)) {
        return;
    }
    switch (m.subcommand) {
    case RRC_MOTOR_SUB_SET_SINGLE:
    case RRC_MOTOR_SUB_SET_MULTI:
        for (uint8_t i = 0; i < m.count; i++) {
            robot_set_wheel_rps(s->robot, m.speeds[i].id, m.speeds[i].rps, now(s), ROBOT_SRC_RRC);
        }
        break;
    case RRC_MOTOR_SUB_STOP_ONE:
        if (m.stop_id < ROBOT_NUM_MOTORS) {
            robot_stop_mask(s->robot, (uint8_t)(1u << m.stop_id));
        }
        break;
    case RRC_MOTOR_SUB_STOP_MASK:
        robot_stop_mask(s->robot, m.stop_mask);
        break;
    default:
        break;
    }
}

/* 한글: FUNC4: 서보 ID는 호스트 기준 1~4 → 내부 0~3으로 변환. */
static void on_pwm_servo(rrc_adapter_t *a, const rrc_frame_t *f)
{
    const robot_services_t *s = a->svc;
    uint8_t sub, id;
    int8_t dev;
    rrc_pwm_servo_move_multi_t mm;
    rrc_pwm_servo_move_single_t ms;
    uint8_t out[4];

    if (rrc_unpack_pwm_servo_move_multi(f->data, f->data_len, &mm)) {
        for (uint8_t i = 0; i < mm.count; i++) {
            if (s->pwm_servo_move && mm.targets[i].id >= 1 && mm.targets[i].id <= 4) {
                s->pwm_servo_move(s->hw, (uint8_t)(mm.targets[i].id - 1), mm.targets[i].pulse, mm.time_ms);
            }
        }
    } else if (rrc_unpack_pwm_servo_move_single(f->data, f->data_len, &ms)) {
        if (s->pwm_servo_move && ms.id >= 1 && ms.id <= 4) {
            s->pwm_servo_move(s->hw, (uint8_t)(ms.id - 1), ms.pulse, ms.time_ms);
        }
    } else if (rrc_unpack_pwm_servo_set_deviation(f->data, f->data_len, &id, &dev)) {
        if (s->pwm_servo_set_offset && id >= 1 && id <= 4) {
            s->pwm_servo_set_offset(s->hw, (uint8_t)(id - 1), dev);
        }
    } else if (rrc_unpack_pwm_servo_read_request(f->data, f->data_len, &sub, &id)) {
        if (id < 1 || id > 4) {
            return;
        }
        if (sub == RRC_SERVO_SUB_READ_POSITION && s->pwm_servo_get_pulse) {
            uint16_t pulse;
            if (s->pwm_servo_get_pulse(s->hw, (uint8_t)(id - 1), &pulse) == 0) {
                send_frame(a, RRC_FUNC_PWM_SERVO, out, rrc_pack_pwm_servo_position(id, pulse, out));
            }
        } else if (sub == RRC_SERVO_SUB_READ_DEVIATION && s->pwm_servo_get_offset) {
            int8_t offset;
            if (s->pwm_servo_get_offset(s->hw, (uint8_t)(id - 1), &offset) == 0) {
                send_frame(a, RRC_FUNC_PWM_SERVO, out, rrc_pack_pwm_servo_deviation(id, offset, out));
            }
        }
    }
}

/* 한글: FUNC5: 다중 이동은 즉시 쓰기, 나머지는 블로킹 트랜잭션 후 읽기 응답만 업로드한다. */
static void on_bus_servo(rrc_adapter_t *a, const rrc_frame_t *f)
{
    const robot_services_t *s = a->svc;
    rrc_bus_servo_move_t mv;
    bus_servo_plan_t plan;

    if (rrc_unpack_bus_servo_move(f->data, f->data_len, &mv)) {
        for (uint8_t i = 0; i < mv.count; i++) {
            if (s->bus_servo_move) {
                s->bus_servo_move(s->hw, mv.targets[i].id, mv.targets[i].pulse, mv.time_ms);
            }
        }
        return;
    }
    if (!bus_servo_plan_from_rrc(f->data, f->data_len, &plan) || !s->bus_servo_xfer) {
        return;
    }
    uint8_t reply[BUS_SERVO_MAX_PARAMS] = {0};
    uint8_t reply_len = 0;
    const int rc = s->bus_servo_xfer(s->hw, &plan, reply, &reply_len);
    if (plan.expects_reply) {
        uint8_t out[3 + BUS_SERVO_MAX_PARAMS];
        const size_t n = bus_servo_make_upload(&plan, rc == 0, reply, reply_len, out);
        send_frame(a, RRC_FUNC_BUS_SERVO, out, n);
    }
}

static void on_diag(rrc_adapter_t *a, const rrc_frame_t *f)
{
    const robot_services_t *s = a->svc;
    rrc_diag_cmd_t d;

    if (!rrc_ext_unpack_diag(f->data, f->data_len, &d)) {
        return;
    }
    switch (d.subcommand) {
    case RRC_DIAG_CLEAR_ESTOP:
        robot_clear_estop(s->robot);
        break;
    case RRC_DIAG_ESTOP:
        robot_estop(s->robot);
        break;
    case RRC_DIAG_SET_TIMEOUT:
        s->robot->cmd_timeout_ms = d.timeout_ms;
        break;
    case RRC_DIAG_SET_PID:
        if (s->set_pid) {
            s->set_pid(s->hw, d.motor, d.kp, d.ki, d.kd);
        }
        break;
    case RRC_DIAG_RAW_PWM:
        if (s->raw_pwm) {
            s->raw_pwm(s->hw, d.motor, d.pulse);
        }
        break;
    case RRC_DIAG_REQUEST_STATUS:
        if (s->request_status) {
            s->request_status(s->hw);
        }
        break;
    default:
        break;
    }
}

static void dispatch(rrc_adapter_t *a, const rrc_frame_t *f)
{
    const robot_services_t *s = a->svc;

    a->frames_ok++;
    switch (f->func) {
    case RRC_FUNC_LED: {
        rrc_led_cmd_t c;
        if (rrc_unpack_led(f->data, f->data_len, &c) && s->led_set) {
            s->led_set(s->hw, c.led_id, c.on_ms, c.off_ms, c.cycles);
        }
        break;
    }
    case RRC_FUNC_BUZZER: {
        rrc_buzzer_cmd_t c;
        if (rrc_unpack_buzzer(f->data, f->data_len, &c) && s->buzzer_set) {
            s->buzzer_set(s->hw, c.freq_hz, c.on_ms, c.off_ms, c.cycles);
        }
        break;
    }
    case RRC_FUNC_MOTOR:
        on_motor(a, f);
        break;
    case RRC_FUNC_PWM_SERVO:
        on_pwm_servo(a, f);
        break;
    case RRC_FUNC_BUS_SERVO:
        on_bus_servo(a, f);
        break;
    case RRC_FUNC_EXT_DIAG_CMD:
        on_diag(a, f);
        break;
    default:
        a->frames_unknown++;
        break;
    }
}

/* 한글: 수신 바이트를 파서에 넣고 완성된 프레임을 모두 처리한다. 버퍼가 가득 찬 채 진행이 없으면 파서를 초기화해 재동기화한다. */
void rrc_adapter_feed(rrc_adapter_t *a, const uint8_t *data, size_t len)
{
    rrc_frame_t frame;

    while (len > 0) {
        const size_t used = rrc_parser_feed(&a->parser, data, len);
        data += used;
        len -= used;
        int popped = 0;
        while (rrc_parser_next(&a->parser, &frame)) {
            dispatch(a, &frame);
            popped = 1;
        }
        if (used == 0 && !popped) { /* parser buffer full and nothing poppable: drop to resync */
            rrc_parser_init(&a->parser);
        }
    }
}

/* ---- outgoing ---- */

void rrc_adapter_send_battery(rrc_adapter_t *a, uint16_t mv)
{
    uint8_t d[3];
    send_frame(a, RRC_FUNC_SYS, d, rrc_pack_battery_mv(mv, d));
}

void rrc_adapter_send_imu(rrc_adapter_t *a, const float accel_g[3], const float gyro_dps[3])
{
    rrc_imu_sample_t s;
    uint8_t d[24];
    for (int i = 0; i < 3; i++) {
        s.accel_g[i] = accel_g[i];
        s.gyro_dps[i] = gyro_dps[i];
    }
    send_frame(a, RRC_FUNC_IMU, d, rrc_pack_imu(&s, d));
}

void rrc_adapter_send_key(rrc_adapter_t *a, uint8_t id, uint8_t ev)
{
    uint8_t d[2];
    send_frame(a, RRC_FUNC_KEY, d, rrc_pack_key_event(id, ev, d));
}

void rrc_adapter_send_gamepad(rrc_adapter_t *a, const rrc_gamepad_state_t *g)
{
    uint8_t d[7];
    send_frame(a, RRC_FUNC_GAMEPAD, d, rrc_pack_gamepad(g, d));
}

void rrc_adapter_send_sbus(rrc_adapter_t *a, const rrc_sbus_frame_t *s)
{
    uint8_t d[36];
    send_frame(a, RRC_FUNC_SBUS, d, rrc_pack_sbus(s, d));
}

void rrc_adapter_send_status(rrc_adapter_t *a, const rrc_ext_status_t *s)
{
    uint8_t d[RRC_EXT_STATUS_LEN];
    send_frame(a, RRC_FUNC_EXT_STATUS, d, rrc_ext_pack_status(s, d));
}

void rrc_adapter_send_wheel(rrc_adapter_t *a, const rrc_ext_wheel_t *w)
{
    uint8_t d[RRC_EXT_WHEEL_LEN];
    send_frame(a, RRC_FUNC_EXT_WHEEL, d, rrc_ext_pack_wheel(w, d));
}

void rrc_adapter_send_raw_hid(rrc_adapter_t *a, const uint8_t *report, size_t len)
{
    uint8_t d[33];
    send_frame(a, RRC_FUNC_EXT_RAW_HID, d, rrc_ext_pack_raw_hid(report, len, d));
}
