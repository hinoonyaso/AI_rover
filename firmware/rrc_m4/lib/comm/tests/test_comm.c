// 한글: lib/comm(RRC 어댑터) 호스트 단위 시험: 공식 PDF 예제 프레임을 그대로 사용한다.
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "comm/rrc_adapter.h"

static int failures;
#define CHECK(cond, msg) do { if (!(cond)) { printf("FAIL: %s (line %d)\n", msg, __LINE__); failures++; } } while (0)

typedef struct {
    uint8_t led_id; uint16_t led_on, led_off, led_cycles; int led_calls;
    uint16_t bz_freq, bz_on, bz_off, bz_cycles; int bz_calls;
    int servo_moves; uint8_t servo_idx[8]; uint16_t servo_pulse[8], servo_time[8];
    int8_t offset[4]; uint16_t pulse_now[4];
    int bus_moves; uint8_t bus_id[8]; uint16_t bus_pulse[8], bus_time;
    int xfer_calls; uint8_t xfer_cmd, xfer_id; int xfer_rc; uint8_t xfer_reply[8]; uint8_t xfer_reply_len;
    int pid_calls; uint8_t pid_motor; float kp, ki, kd;
    int raw_calls; uint8_t raw_motor; int16_t raw_pulse;
    int status_calls;
    uint32_t now;
    uint8_t tx[16][300]; size_t txlen[16]; int ntx;
} mock_t;

// 한글: mock 서비스: 호출 인자를 기록해 어댑터가 올바르게 분기했는지 확인한다.
static uint32_t m_now(void *hw) { return ((mock_t *)hw)->now; }
static void m_led(void *hw, uint8_t id, uint16_t on, uint16_t off, uint16_t cy) {
    mock_t *m = hw; m->led_id = id; m->led_on = on; m->led_off = off; m->led_cycles = cy; m->led_calls++; }
static void m_bz(void *hw, uint16_t f, uint16_t on, uint16_t off, uint16_t cy) {
    mock_t *m = hw; m->bz_freq = f; m->bz_on = on; m->bz_off = off; m->bz_cycles = cy; m->bz_calls++; }
static void m_servo(void *hw, uint8_t i, uint16_t p, uint16_t t) {
    mock_t *m = hw; m->servo_idx[m->servo_moves] = i; m->servo_pulse[m->servo_moves] = p; m->servo_time[m->servo_moves] = t; m->servo_moves++; }
static int m_servo_get(void *hw, uint8_t i, uint16_t *p) { mock_t *m = hw; *p = m->pulse_now[i]; return 0; }
static void m_servo_off(void *hw, uint8_t i, int8_t o) { ((mock_t *)hw)->offset[i] = o; }
static int m_servo_off_get(void *hw, uint8_t i, int8_t *o) { *o = ((mock_t *)hw)->offset[i]; return 0; }
static void m_bus_move(void *hw, uint8_t id, uint16_t p, uint16_t t) {
    mock_t *m = hw; m->bus_id[m->bus_moves] = id; m->bus_pulse[m->bus_moves] = p; m->bus_time = t; m->bus_moves++; }
static int m_bus_xfer(void *hw, const bus_servo_plan_t *plan, uint8_t *reply, uint8_t *rl) {
    mock_t *m = hw; m->xfer_calls++; m->xfer_cmd = plan->cmd; m->xfer_id = plan->id;
    memcpy(reply, m->xfer_reply, sizeof(m->xfer_reply)); *rl = m->xfer_reply_len; return m->xfer_rc; }
static void m_pid(void *hw, uint8_t mo, float kp, float ki, float kd) {
    mock_t *m = hw; m->pid_calls++; m->pid_motor = mo; m->kp = kp; m->ki = ki; m->kd = kd; }
static void m_raw(void *hw, uint8_t mo, int16_t p) { mock_t *m = hw; m->raw_calls++; m->raw_motor = mo; m->raw_pulse = p; }
static void m_status(void *hw) { ((mock_t *)hw)->status_calls++; }
static void m_tx(void *ctx, const uint8_t *f, size_t n) {
    mock_t *m = ctx; memcpy(m->tx[m->ntx], f, n); m->txlen[m->ntx++] = n; }

static void noop_pulse(void *c, int p) { (void)c; (void)p; }

typedef struct {
    mock_t mock;
    enc_motor_t mt[4];
    enc_motor_t *mp[4];
    robot_ctrl_t robot;
    robot_services_t svc;
    rrc_adapter_t adapter;
} rig_t;

static void rig_init(rig_t *r)
{
    const mecanum_cfg_t cfg = {0.216f, 0.195f, 0.097f};
    memset(r, 0, sizeof(*r));
    for (int i = 0; i < 4; i++) {
        enc_motor_init(&r->mt[i], 1320, 5.0f, 63, 2.6f, 2.4f, 60000, 1, noop_pulse, NULL);
        r->mp[i] = &r->mt[i];
    }
    robot_init(&r->robot, r->mp, &cfg, 1);
    r->svc.robot = &r->robot;
    r->svc.hw = &r->mock;
    r->svc.now_ms = m_now;
    r->svc.led_set = m_led;
    r->svc.buzzer_set = m_bz;
    r->svc.pwm_servo_move = m_servo;
    r->svc.pwm_servo_get_pulse = m_servo_get;
    r->svc.pwm_servo_set_offset = m_servo_off;
    r->svc.pwm_servo_get_offset = m_servo_off_get;
    r->svc.bus_servo_move = m_bus_move;
    r->svc.bus_servo_xfer = m_bus_xfer;
    r->svc.set_pid = m_pid;
    r->svc.raw_pwm = m_raw;
    r->svc.request_status = m_status;
    rrc_adapter_init(&r->adapter, &r->svc, m_tx, &r->mock);
}

static void send(rig_t *r, uint8_t func, const uint8_t *data, size_t len)
{
    uint8_t f[RRC_MAX_FRAME_LEN];
    const size_t n = rrc_encode(func, data, len, f);
    rrc_adapter_feed(&r->adapter, f, n);
}

static void test_led_buzzer(void)
{
    rig_t r; rig_init(&r);
    /* PDF: LED 1 blink 10 times, 500 ms on / 300 ms off */
    const uint8_t led[] = {0x01, 0xF4, 0x01, 0x2C, 0x01, 0x0A, 0x00};
    send(&r, RRC_FUNC_LED, led, sizeof(led));
    CHECK(r.mock.led_calls == 1 && r.mock.led_id == 1 && r.mock.led_on == 500 && r.mock.led_off == 300 && r.mock.led_cycles == 10, "LED from PDF example");
    /* PDF: buzzer 1400 Hz, 100/100 ms, 5 times */
    const uint8_t bz[] = {0x78, 0x05, 0x64, 0x00, 0x64, 0x00, 0x05, 0x00};
    send(&r, RRC_FUNC_BUZZER, bz, sizeof(bz));
    CHECK(r.mock.bz_calls == 1 && r.mock.bz_freq == 1400 && r.mock.bz_on == 100 && r.mock.bz_off == 100 && r.mock.bz_cycles == 5, "buzzer from PDF example");
}

// 한글: PDF 예제 프레임으로 모터 단일/다중/정지/마스크/timeout 확인(모터 ID는 0부터).
static void test_motor(void)
{
    rig_t r; rig_init(&r);
    r.mock.now = 100;
    /* PDF: motor 1 -> -1 r/s, motor 2 -> +2 r/s (1-based in the PDF; wire is 0-based here: ids 0 and 1) */
    const uint8_t multi[] = {0x01, 0x02, 0x00, 0x00, 0x00, 0x80, 0xBF, 0x01, 0x00, 0x00, 0x00, 0x40};
    send(&r, RRC_FUNC_MOTOR, multi, sizeof(multi));
    CHECK(fabsf(r.mt[0].pid.set_point + 1.0f) < 1e-6f && fabsf(r.mt[1].pid.set_point - 2.0f) < 1e-6f, "multi-motor command");
    CHECK(r.robot.last_source == ROBOT_SRC_RRC && r.robot.last_cmd_ms == 100, "source/time recorded");

    const uint8_t single[] = {0x00, 0x03, 0x00, 0x00, 0x80, 0x3F}; /* motor 3 -> +1.0 */
    send(&r, RRC_FUNC_MOTOR, single, sizeof(single));
    CHECK(fabsf(r.mt[3].pid.set_point - 1.0f) < 1e-6f, "single-motor command");

    const uint8_t stop_one[] = {0x02, 0x01};
    send(&r, RRC_FUNC_MOTOR, stop_one, sizeof(stop_one));
    CHECK(r.mt[1].pid.set_point == 0.0f && r.mt[0].pid.set_point != 0.0f, "stop one");

    const uint8_t stop_mask[] = {0x03, 0x05}; /* PDF: motors 0 and 2 */
    send(&r, RRC_FUNC_MOTOR, stop_mask, sizeof(stop_mask));
    CHECK(r.mt[0].pid.set_point == 0.0f && r.mt[2].pid.set_point == 0.0f && r.mt[3].pid.set_point != 0.0f, "stop mask");

    r.mock.now = 5000;
    robot_tick(&r.robot, r.mock.now);
    CHECK(r.mt[3].pid.set_point == 0.0f, "command timeout still applies to RRC commands");

    const uint8_t bad_id[] = {0x00, 0x09, 0x00, 0x00, 0x80, 0x3F};
    send(&r, RRC_FUNC_MOTOR, bad_id, sizeof(bad_id));
    CHECK(r.mt[0].pid.set_point == 0.0f, "out-of-range motor id ignored");
}

static void test_servos(void)
{
    rig_t r; rig_init(&r);
    /* PDF: servo 1 -> 1500, servo 2 -> 2500 in 2000 ms */
    const uint8_t multi[] = {0x01, 0xD0, 0x07, 0x02, 0x01, 0xDC, 0x05, 0x02, 0xC4, 0x09};
    send(&r, RRC_FUNC_PWM_SERVO, multi, sizeof(multi));
    CHECK(r.mock.servo_moves == 2 && r.mock.servo_idx[0] == 0 && r.mock.servo_pulse[0] == 1500 && r.mock.servo_time[0] == 2000 &&
          r.mock.servo_idx[1] == 1 && r.mock.servo_pulse[1] == 2500, "PWM servo multi move, ids 1-based -> idx 0-based");
    /* PDF: servo 1 to 1500 within 1 s */
    const uint8_t single[] = {0x03, 0xE8, 0x03, 0x01, 0xDC, 0x05};
    send(&r, RRC_FUNC_PWM_SERVO, single, sizeof(single));
    CHECK(r.mock.servo_moves == 3 && r.mock.servo_time[2] == 1000, "PWM servo single move");
    const uint8_t dev[] = {0x07, 0x02, 0x0A}; /* PDF: servo 2 offset +10 */
    send(&r, RRC_FUNC_PWM_SERVO, dev, sizeof(dev));
    CHECK(r.mock.offset[1] == 10, "PWM servo deviation set");
    r.mock.pulse_now[0] = 1234;
    const uint8_t rd[] = {0x05, 0x01};
    send(&r, RRC_FUNC_PWM_SERVO, rd, sizeof(rd));
    CHECK(r.mock.ntx == 1, "position read answered");
    rrc_parser_t p; rrc_frame_t f;
    rrc_parser_init(&p);
    rrc_parser_feed(&p, r.mock.tx[0], r.mock.txlen[0]);
    CHECK(rrc_parser_next(&p, &f) && f.func == RRC_FUNC_PWM_SERVO && f.data_len == 4 && f.data[0] == 1 && f.data[1] == 0x05 &&
          f.data[2] == (1234 & 0xFF) && f.data[3] == (1234 >> 8), "position upload layout");
    const uint8_t rd_dev[] = {0x09, 0x02};
    send(&r, RRC_FUNC_PWM_SERVO, rd_dev, sizeof(rd_dev));
    CHECK(r.mock.ntx == 2 && r.mock.tx[1][4] == 2 && r.mock.tx[1][4 + 2] == 10, "deviation read answered");
}

static void test_bus_servo(void)
{
    rig_t r; rig_init(&r);
    /* PDF: servo 1 -> 833, servo 2 -> 1000 in 1000 ms */
    const uint8_t mv[] = {0x01, 0xE8, 0x03, 0x02, 0x01, 0x41, 0x03, 0x02, 0xE8, 0x03};
    send(&r, RRC_FUNC_BUS_SERVO, mv, sizeof(mv));
    CHECK(r.mock.bus_moves == 2 && r.mock.bus_id[0] == 1 && r.mock.bus_pulse[0] == 833 && r.mock.bus_id[1] == 2 &&
          r.mock.bus_pulse[1] == 1000 && r.mock.bus_time == 1000, "bus servo multi move");
    /* read position of servo 5 -> upload [5, 0x05, 0, 0x41, 0x03] (PDF example) */
    r.mock.xfer_rc = 0; r.mock.xfer_reply[0] = 0x41; r.mock.xfer_reply[1] = 0x03; r.mock.xfer_reply_len = 2;
    const uint8_t rd[] = {0x05, 0x05};
    send(&r, RRC_FUNC_BUS_SERVO, rd, sizeof(rd));
    CHECK(r.mock.xfer_calls == 1 && r.mock.xfer_cmd == BUS_CMD_POS_READ && r.mock.xfer_id == 5, "position read transaction");
    const uint8_t expect[] = {0xAA, 0x55, 0x05, 0x05, 5, 0x05, 0x00, 0x41, 0x03};
    CHECK(r.mock.ntx == 1 && memcmp(r.mock.tx[0], expect, 9) == 0, "upload frame bytes");
    /* failed transaction uploads -1 */
    r.mock.xfer_rc = -1;
    send(&r, RRC_FUNC_BUS_SERVO, rd, sizeof(rd));
    CHECK(r.mock.ntx == 2 && r.mock.tx[1][6] == 0xFF, "failed read uploads -1");
    /* write command: transaction but no upload */
    const uint8_t unload[] = {0x0B, 0x01};
    send(&r, RRC_FUNC_BUS_SERVO, unload, sizeof(unload));
    CHECK(r.mock.xfer_calls == 3 && r.mock.xfer_cmd == BUS_CMD_LOAD_OR_UNLOAD_WRITE && r.mock.ntx == 2, "unload = write, no upload");
}

// 한글: 진단 명령과 견고성: 알 수 없는 FUNC, 쓰레기 바이트, 바이트 단위 입력, CRC 오류, 0xAA 홍수 후 복구.
static void test_diag_and_robustness(void)
{
    rig_t r; rig_init(&r);
    const uint8_t estop[] = {RRC_DIAG_ESTOP};
    send(&r, RRC_FUNC_EXT_DIAG_CMD, estop, 1);
    CHECK(r.robot.estop, "diag estop");
    const uint8_t clear[] = {RRC_DIAG_CLEAR_ESTOP};
    send(&r, RRC_FUNC_EXT_DIAG_CMD, clear, 1);
    CHECK(!r.robot.estop, "diag clear estop");
    const uint8_t to[] = {RRC_DIAG_SET_TIMEOUT, 0xE8, 0x03};
    send(&r, RRC_FUNC_EXT_DIAG_CMD, to, 3);
    CHECK(r.robot.cmd_timeout_ms == 1000, "diag set timeout");
    uint8_t pid[14] = {RRC_DIAG_SET_PID, 0xFF};
    const float g[3] = {10.0f, 1.5f, 0.25f};
    memcpy(&pid[2], &g[0], 4); memcpy(&pid[6], &g[1], 4); memcpy(&pid[10], &g[2], 4);
    send(&r, RRC_FUNC_EXT_DIAG_CMD, pid, sizeof(pid));
    CHECK(r.mock.pid_calls == 1 && r.mock.pid_motor == 0xFF && r.mock.kp == 10.0f && r.mock.ki == 1.5f && r.mock.kd == 0.25f, "diag set pid");
    const uint8_t raw[] = {RRC_DIAG_RAW_PWM, 2, 0x2C, 0x01}; /* 300 */
    send(&r, RRC_FUNC_EXT_DIAG_CMD, raw, sizeof(raw));
    CHECK(r.mock.raw_calls == 1 && r.mock.raw_motor == 2 && r.mock.raw_pulse == 300, "diag raw pwm");
    const uint8_t st[] = {RRC_DIAG_REQUEST_STATUS};
    send(&r, RRC_FUNC_EXT_DIAG_CMD, st, 1);
    CHECK(r.mock.status_calls == 1, "diag status request");

    /* unknown FUNC, garbage, and byte-by-byte delivery */
    send(&r, 0x7E, (const uint8_t *)"\x01\x02", 2);
    CHECK(r.adapter.frames_unknown == 1, "unknown FUNC counted and dropped");
    const uint8_t garbage[] = {0x00, 0xAA, 0xAA, 0x13, 0x37, 0xFF, 0x55};
    rrc_adapter_feed(&r.adapter, garbage, sizeof(garbage));
    uint8_t f[RRC_MAX_FRAME_LEN];
    const uint8_t led[] = {0x01, 0x64, 0x00, 0x64, 0x00, 0x03, 0x00};
    const size_t n = rrc_encode(RRC_FUNC_LED, led, sizeof(led), f);
    r.mock.led_calls = 0;
    for (size_t i = 0; i < n; i++) rrc_adapter_feed(&r.adapter, &f[i], 1);
    CHECK(r.mock.led_calls == 1, "frame after garbage, delivered one byte at a time");
    f[n - 1] ^= 0x5A; /* corrupt CRC */
    r.mock.led_calls = 0;
    rrc_adapter_feed(&r.adapter, f, n);
    CHECK(r.mock.led_calls == 0, "bad CRC rejected");
    uint8_t flood[2000];
    memset(flood, 0xAA, sizeof(flood));
    rrc_adapter_feed(&r.adapter, flood, sizeof(flood));
    rrc_adapter_feed(&r.adapter, led, 0);
    send(&r, RRC_FUNC_LED, led, sizeof(led));
    CHECK(r.mock.led_calls == 1, "adapter recovers after a flood of 0xAA");
}

static void test_telemetry(void)
{
    rig_t r; rig_init(&r);
    rrc_adapter_send_battery(&r.adapter, 12345);
    const uint8_t b[] = {0xAA, 0x55, 0x00, 0x03, 0x04, 0x39, 0x30};
    CHECK(memcmp(r.mock.tx[0], b, sizeof(b)) == 0, "battery frame (04 + u16 LE mV)");
    const float a[3] = {0, 0, -1.0f}, g[3] = {0.5f, 0, 0};
    rrc_adapter_send_imu(&r.adapter, a, g);
    CHECK(r.mock.txlen[1] == 2 + 1 + 1 + 24 + 1 && r.mock.tx[1][2] == RRC_FUNC_IMU && r.mock.tx[1][3] == 24, "imu frame shape");
    rrc_adapter_send_key(&r.adapter, 1, 0x20);
    rrc_ext_status_t s; memset(&s, 0, sizeof(s)); s.flags = RRC_STATUS_ESTOP; s.uptime_ms = 0x01020304;
    rrc_adapter_send_status(&r.adapter, &s);
    CHECK(r.mock.tx[3][2] == RRC_FUNC_EXT_STATUS && r.mock.tx[3][3] == RRC_EXT_STATUS_LEN && r.mock.tx[3][4] == RRC_STATUS_ESTOP &&
          r.mock.tx[3][4 + 8] == 0x04 && r.mock.tx[3][4 + 11] == 0x01, "status frame");
    rrc_ext_wheel_t w = {{1.0f, 0, 0, 0}, {1, 2, 3, -4}};
    rrc_adapter_send_wheel(&r.adapter, &w);
    CHECK(r.mock.tx[4][3] == RRC_EXT_WHEEL_LEN && r.mock.tx[4][4 + 16 + 12] == 0xFC, "wheel frame, int32 counters");
    rrc_ext_diag_t d; memset(&d, 0, sizeof(d));
    d.n = 2; d.task_id[0] = 0; d.min_free_words[0] = 0x0102; d.task_id[1] = 5; d.min_free_words[1] = 300;
    d.imu_samples = 7; d.imu_errors = 1; d.rejected_cmds = 0x0A0B0C0D;
    rrc_adapter_send_diag(&r.adapter, &d);
    const uint8_t *f = r.mock.tx[5];
    CHECK(f[2] == RRC_FUNC_EXT_DIAG && f[3] == 1 + 2 * 3 + 12 && f[4] == 2 && f[5] == 0 && f[6] == 0x02 && f[7] == 0x01 &&
          f[8] == 5 && f[10 + 1] == 7 && f[10 + 9] == 0x0D && f[10 + 12] == 0x0A, "diag frame (tasks + counters)");
}

int main(void)
{
    test_led_buzzer();
    test_motor();
    test_servos();
    test_bus_servo();
    test_diag_and_robustness();
    test_telemetry();
    if (failures) {
        printf("%d CHECK(S) FAILED\n", failures);
        return 1;
    }
    printf("ALL COMM TESTS PASSED\n");
    return 0;
}
