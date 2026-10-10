// 한글: lib/core 호스트 단위 시험(하드웨어 불필요).
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "core/battery.h"
#include "core/blink.h"
#include "core/bus_servo.h"
#include "core/button.h"
#include "core/encoder_motor.h"
#include "core/gamepad.h"
#include "core/imu.h"
#include "core/local_drive.h"
#include "core/mecanum.h"
#include "core/pid.h"
#include "core/pwm_servo.h"
#include "core/robot_ctrl.h"
#include "core/sbus.h"

static int failures;
#define CHECK(cond, msg) do { if (!(cond)) { printf("FAIL: %s (line %d)\n", msg, __LINE__); failures++; } } while (0)
#define NEAR(a, b, tol, msg) CHECK(fabsf((a) - (b)) <= (tol), msg)

/* ---------- simulated plant: wheel speed follows PWM with a first-order lag ---------- */
typedef struct {
    float rps, k, tau;
    int pulse;
    float polarity; /* -1 simulates a reversed encoder */
    double counter; /* raw encoder ticks (unbounded) */
} plant_t;

static void plant_set_pulse(void *ctx, int pulse) { ((plant_t *)ctx)->pulse = pulse; }

static void plant_step(plant_t *p, float dt, float ticks_per_rev)
{
    const float target = p->k * (float)p->pulse / 1000.0f;
    p->rps += (target - p->rps) * dt / p->tau;
    p->counter += (double)(p->rps * p->polarity * ticks_per_rev * dt);
}

/* Feeds the unbounded counter through a 0..ticks_overflow hardware counter with overflow IRQs. */
static void feed_motor(enc_motor_t *m, plant_t *p, int32_t wrap, int64_t *hw_unwrapped_prev)
{
    const int64_t total = (int64_t)p->counter;
    while (total - (*hw_unwrapped_prev / wrap) * wrap >= wrap) { /* crossed a wrap upwards */
        enc_motor_on_overflow(m, 0);
        *hw_unwrapped_prev += wrap;
    }
    while (total - (*hw_unwrapped_prev / wrap) * wrap < 0) {
        enc_motor_on_overflow(m, 1);
        *hw_unwrapped_prev -= wrap;
    }
    enc_motor_update(m, 0.01f, total - (*hw_unwrapped_prev / wrap) * wrap);
}

// 한글: PID 수식(Hiwonder 문서)과 수치가 같은지 손계산 값으로 확인.
static void test_pid(void)
{
    rrc_pid_t pid;
    rrc_pid_init(&pid, 2.0f, 1.0f, 0.5f);
    pid.set_point = 1.0f;
    rrc_pid_update(&pid, 0.0f, 0.1f); /* err=1: 2*1 + 1*0.1 + 0.5*(1-0+0)/0.1 = 7.1 */
    NEAR(pid.output, 7.1f, 1e-4f, "pid first step");
    rrc_pid_update(&pid, 0.5f, 0.1f); /* err=.5: 1 + .05 + .5*(.5-2*0+1)/.1=7.5 -> 8.55 */
    NEAR(pid.output, 8.55f, 1e-4f, "pid second step");
}

// 한글: 1차 지연 모델의 가짜 모터로 속도 추종(정/역/상한/NaN) 확인.
static void test_enc_motor_tracks(void)
{
    plant_t p = {0, 2.0f, 0.15f, 0, 1.0f, 0};
    enc_motor_t m;
    int64_t unwrapped = 0;
    enc_motor_init(&m, 1320, 5.0f, 63.0f, 2.6f, 2.4f, 60000, 1, plant_set_pulse, &p);
    CHECK(enc_motor_set_speed(&m, 1.0f) == 0, "set speed");
    for (int i = 0; i < 400; i++) { /* 4 s */
        plant_step(&p, 0.01f, 1320.0f);
        feed_motor(&m, &p, 60000, &unwrapped);
        enc_motor_control(&m, 0.01f, 0);
    }
    NEAR(m.rps, 1.0f, 0.08f, "rps converges to set point");
    CHECK(m.fault == ENC_MOTOR_FAULT_NONE, "no fault when healthy");
    /* reverse */
    enc_motor_set_speed(&m, -1.0f);
    for (int i = 0; i < 600; i++) {
        plant_step(&p, 0.01f, 1320.0f);
        feed_motor(&m, &p, 60000, &unwrapped);
        enc_motor_control(&m, 0.01f, 0);
    }
    NEAR(m.rps, -1.0f, 0.08f, "rps converges in reverse");
    /* rps limit */
    enc_motor_set_speed(&m, 99.0f);
    NEAR(m.pid.set_point, 5.0f, 1e-6f, "set point clamped to rps_limit");
    enc_motor_set_speed(&m, NAN);
    NEAR(m.pid.set_point, 0.0f, 1e-6f, "NaN command becomes 0");
}

// 한글: 엔코더 부호가 틀린 바퀴가 목표 0에서 관성으로 돌 때(2026-10-10 실기 재현) 200 ms 안팎에 래치되는지,
//       정상 바퀴의 급반전(+4 → -4 rps)은 래치되지 않는지 확인.
static void test_enc_motor_sign_guard(void)
{
    plant_t p = {3.0f, 8.0f, 0.15f, 0, -1.0f, 0}; /* reversed encoder, wheel already coasting at 3 rps */
    enc_motor_t m;
    int64_t unwrapped = 0;
    enc_motor_init(&m, 1320, 5.0f, 63.0f, 2.6f, 2.4f, 60000, 1, plant_set_pulse, &p);
    int latched_at = -1, max_pulse = 0;
    for (int i = 0; i < 300; i++) { /* set point stays 0 (old code: full PWM forever) */
        plant_step(&p, 0.01f, 1320.0f);
        feed_motor(&m, &p, 60000, &unwrapped);
        enc_motor_control(&m, 0.01f, 0);
        if (abs(p.pulse) > max_pulse) max_pulse = abs(p.pulse);
        if (m.fault == ENC_MOTOR_FAULT_RUNAWAY && latched_at < 0) latched_at = i;
    }
    CHECK(latched_at > 0 && latched_at < 60, "sign guard latches within 0.6 s at set point 0");
    CHECK(p.pulse == 0, "pulse 0 after the sign-guard latch");

    plant_t q = {0, 8.0f, 0.15f, 0, 1.0f, 0}; /* healthy, fast wheel */
    enc_motor_t m2;
    unwrapped = 0;
    enc_motor_init(&m2, 1320, 5.0f, 63.0f, 2.6f, 2.4f, 60000, 1, plant_set_pulse, &q);
    enc_motor_set_speed(&m2, 4.0f);
    for (int i = 0; i < 300; i++) {
        plant_step(&q, 0.01f, 1320.0f);
        feed_motor(&m2, &q, 60000, &unwrapped);
        enc_motor_control(&m2, 0.01f, 0);
    }
    enc_motor_set_speed(&m2, -4.0f);
    for (int i = 0; i < 300; i++) {
        plant_step(&q, 0.01f, 1320.0f);
        feed_motor(&m2, &q, 60000, &unwrapped);
        enc_motor_control(&m2, 0.01f, 0);
    }
    CHECK(m2.fault == ENC_MOTOR_FAULT_NONE, "full reversal +4 -> -4 rps does not trip the sign guard");
    NEAR(m2.rps, -4.0f, 0.3f, "reversal reaches -4 rps");
}

// 한글: 60000 오버플로(상향/하향)를 넘어도 속도가 변하지 않는지 확인.
static void test_enc_motor_wraps(void)
{
    /* Start near the 60000 wrap so both the up-wrap and (after reversing) the down-wrap happen. */
    plant_t p = {0, 2.0f, 0.15f, 0, 1.0f, 59000.0};
    enc_motor_t m;
    int64_t unwrapped = 0;
    enc_motor_init(&m, 1320, 5.0f, 63.0f, 2.6f, 2.4f, 60000, 1, plant_set_pulse, &p);
    feed_motor(&m, &p, 60000, &unwrapped); /* baseline sample */
    m.tps = 0.0f;
    m.rps = 0.0f;
    enc_motor_set_speed(&m, 2.0f);
    for (int i = 0; i < 300; i++) {
        plant_step(&p, 0.01f, 1320.0f);
        feed_motor(&m, &p, 60000, &unwrapped);
        enc_motor_control(&m, 0.01f, 0);
    }
    CHECK(m.overflow_num == 1, "up-wrap counted once");
    CHECK(m.counter > 60000, "total count continues past the wrap");
    NEAR(m.rps, 2.0f, 0.15f, "speed unaffected by the wrap");
    enc_motor_set_speed(&m, -2.0f);
    for (int i = 0; i < 700; i++) {
        plant_step(&p, 0.01f, 1320.0f);
        feed_motor(&m, &p, 60000, &unwrapped);
        enc_motor_control(&m, 0.01f, 0);
    }
    CHECK(m.overflow_num == 0 || m.overflow_num == -1, "down-wrap counted");
    NEAR(m.rps, -2.0f, 0.15f, "speed unaffected by the down-wrap");
}

static void test_enc_motor_dead_zone_and_fault(void)
{
    plant_t p = {0};
    enc_motor_t m;
    enc_motor_init(&m, 1320, 5.0f, 1.0f, 0.0f, 0.0f, 60000, 1, plant_set_pulse, &p);
    enc_motor_set_speed(&m, 1.0f);
    enc_motor_control(&m, 0.01f, 0); /* pulse = 1, inside +-250 dead zone */
    CHECK(p.pulse == 0, "dead zone suppresses small pulses");
    enc_motor_control(&m, 0.01f, 1); /* driver fault */
    CHECK(p.pulse == 0 && m.fault == ENC_MOTOR_FAULT_DRIVER, "driver fault forces 0");
    enc_motor_control(&m, 0.01f, 0);
    CHECK(m.fault == ENC_MOTOR_FAULT_NONE, "driver fault clears when pin releases");
}

// 한글: 엔코더 부호가 반대일 때(양의 되먹임) 래치로 멈추고, encoder_sign=-1이면 정상 동작하는지 확인.
static void test_enc_motor_runaway_latch(void)
{
    plant_t p = {0, 2.0f, 0.15f, 0, -1.0f, 0}; /* reversed encoder: positive feedback */
    enc_motor_t m;
    int64_t unwrapped = 0;
    int guard_pulses_max = 0;
    enc_motor_init(&m, 1320, 5.0f, 63.0f, 2.6f, 2.4f, 60000, 1, plant_set_pulse, &p);
    enc_motor_set_speed(&m, 1.0f);
    int latched_at = -1;
    for (int i = 0; i < 1000; i++) {
        plant_step(&p, 0.01f, 1320.0f);
        feed_motor(&m, &p, 60000, &unwrapped);
        enc_motor_control(&m, 0.01f, 0);
        if (abs(p.pulse) > guard_pulses_max) guard_pulses_max = abs(p.pulse);
        if (m.fault == ENC_MOTOR_FAULT_RUNAWAY && latched_at < 0) latched_at = i;
    }
    CHECK(latched_at > 0 && latched_at < 400, "runaway latches within ~4 s");
    CHECK(p.pulse == 0, "pulse is 0 after the latch");
    CHECK(enc_motor_set_speed(&m, 1.0f) == -1, "latched motor refuses commands");
    enc_motor_clear_fault(&m);
    CHECK(enc_motor_set_speed(&m, 1.0f) == 0, "clear_fault re-arms");
    /* a healthy plant with the sign fixed in config must not latch */
    plant_t q = {0, 2.0f, 0.15f, 0, -1.0f, 0};
    enc_motor_t m2;
    unwrapped = 0;
    enc_motor_init(&m2, 1320, 5.0f, 63.0f, 2.6f, 2.4f, 60000, -1, plant_set_pulse, &q);
    enc_motor_set_speed(&m2, 1.0f);
    for (int i = 0; i < 600; i++) {
        plant_step(&q, 0.01f, 1320.0f);
        feed_motor(&m2, &q, 60000, &unwrapped);
        enc_motor_control(&m2, 0.01f, 0);
    }
    CHECK(m2.fault == ENC_MOTOR_FAULT_NONE, "encoder_sign=-1 compensates a reversed encoder");
    NEAR(m2.rps, 1.0f, 0.1f, "reversed encoder tracks with sign fix");
}

// 한글: 호스트 base_node 수식과 동일한 출력인지, 정/역 변환 왕복이 일치하는지 확인.
static void test_mecanum(void)
{
    const mecanum_cfg_t cfg = {0.216f, 0.195f, 0.097f}; /* config/base.yaml */
    float rps[4];
    const float to_rps = 1.0f / (3.14159265f * 0.097f);

    mecanum_inverse(&cfg, 0.1f, 0.0f, 0.0f, rps);
    NEAR(rps[0], 0.1f * to_rps, 1e-4f, "forward m0");
    NEAR(rps[1], 0.1f * to_rps, 1e-4f, "forward m1");
    NEAR(rps[2], -0.1f * to_rps, 1e-4f, "forward m2 mirrored");
    NEAR(rps[3], -0.1f * to_rps, 1e-4f, "forward m3 mirrored");

    mecanum_inverse(&cfg, 0.0f, 0.1f, 0.0f, rps); /* strafe left */
    NEAR(rps[0], -0.1f * to_rps, 1e-4f, "strafe m0");
    NEAR(rps[1], 0.1f * to_rps, 1e-4f, "strafe m1");
    NEAR(rps[2], -0.1f * to_rps, 1e-4f, "strafe m2");
    NEAR(rps[3], 0.1f * to_rps, 1e-4f, "strafe m3");

    float vx, vy, wz;
    mecanum_inverse(&cfg, 0.12f, -0.07f, 0.5f, rps);
    mecanum_forward(&cfg, rps, &vx, &vy, &wz);
    NEAR(vx, 0.12f, 1e-4f, "forward kinematics vx round trip");
    NEAR(vy, -0.07f, 1e-4f, "forward kinematics vy round trip");
    NEAR(wz, 0.5f, 1e-4f, "forward kinematics wz round trip");
}

static void set_pulse_noop(void *ctx, int pulse) { (void)ctx; (void)pulse; }

// 한글: 명령 timeout, e-stop, 저전압 히스테리시스, 바퀴 fault 전체 정지, 비활성 시 명령 무시 확인.
static void test_robot_ctrl(void)
{
    enc_motor_t mt[4];
    enc_motor_t *mp[4] = {&mt[0], &mt[1], &mt[2], &mt[3]};
    const mecanum_cfg_t cfg = {0.216f, 0.195f, 0.097f};
    robot_ctrl_t rc;

    for (int i = 0; i < 4; i++) enc_motor_init(&mt[i], 1320, 5.0f, 63, 2.6f, 2.4f, 60000, 1, set_pulse_noop, NULL);
    robot_init(&rc, mp, &cfg, 1);

    robot_set_velocity(&rc, 0.1f, 0, 0, 1000, ROBOT_SRC_MICROROS);
    CHECK(mt[0].pid.set_point > 0.3f, "velocity reaches motors");
    robot_tick(&rc, 1500);
    CHECK(rc.moving, "no timeout before 1 s");
    robot_tick(&rc, 2100);
    CHECK(!rc.moving && mt[0].pid.set_point == 0.0f && rc.stop_reason == ROBOT_STOP_TIMEOUT, "timeout stops wheels");

    robot_set_wheel_rps(&rc, 2, 1.5f, 5000, ROBOT_SRC_RRC);
    CHECK(mt[2].pid.set_point == 1.5f && rc.last_source == ROBOT_SRC_RRC, "per-wheel command");
    robot_stop_mask(&rc, 0x04);
    CHECK(mt[2].pid.set_point == 0.0f, "stop mask");

    robot_estop(&rc);
    robot_set_velocity(&rc, 0.1f, 0, 0, 6000, ROBOT_SRC_RRC);
    CHECK(mt[0].pid.set_point == 0.0f, "estop blocks commands");
    robot_clear_estop(&rc);
    robot_set_velocity(&rc, 0.1f, 0, 0, 6000, ROBOT_SRC_RRC);
    CHECK(mt[0].pid.set_point > 0.3f, "clear_estop re-enables");

    robot_update_battery(&rc, 9000);
    CHECK(rc.low_battery && mt[0].pid.set_point == 0.0f, "low battery stops and latches");
    robot_set_velocity(&rc, 0.1f, 0, 0, 7000, ROBOT_SRC_RRC);
    CHECK(mt[0].pid.set_point == 0.0f, "low battery blocks");
    robot_update_battery(&rc, 9800);
    CHECK(rc.low_battery, "hysteresis keeps cutoff");
    robot_update_battery(&rc, 10100);
    CHECK(!rc.low_battery, "released above clear level");

    mt[1].fault = ENC_MOTOR_FAULT_RUNAWAY;
    robot_set_velocity(&rc, 0.1f, 0, 0, 8000, ROBOT_SRC_RRC);
    robot_tick(&rc, 8010);
    CHECK(rc.stop_reason == ROBOT_STOP_MOTOR_FAULT && mt[0].pid.set_point == 0.0f, "wheel fault stops every wheel");

    robot_ctrl_t off;
    robot_init(&off, mp, &cfg, 0);
    robot_set_velocity(&off, 0.1f, 0, 0, 1, ROBOT_SRC_RRC);
    CHECK(mt[0].pid.set_point == 0.0f, "disabled robot ignores commands");
}

// 한글: NaN/Inf 명령 폐기, 한 번에 한 출처만 제어(2026-10-10, micro-ROS + RRC 폴백 대비).
static void test_robot_arbitration(void)
{
    enc_motor_t mt[4];
    enc_motor_t *mp[4] = {&mt[0], &mt[1], &mt[2], &mt[3]};
    const mecanum_cfg_t cfg = {0.216f, 0.195f, 0.097f};
    robot_ctrl_t rc;
    for (int i = 0; i < 4; i++) enc_motor_init(&mt[i], 3996, 3.0f, 63, 2.6f, 2.4f, 60000, 1, set_pulse_noop, NULL);
    robot_init(&rc, mp, &cfg, 1);

    /* non-finite: dropped, not a command */
    CHECK(robot_set_velocity(&rc, INFINITY, 0, 0, 100, ROBOT_SRC_MICROROS) == -1 && !rc.moving &&
          mt[0].pid.set_point == 0.0f, "Inf velocity dropped (used to clamp to full speed)");
    CHECK(robot_set_velocity(&rc, 0, NAN, 0, 100, ROBOT_SRC_MICROROS) == -1, "NaN velocity dropped");
    CHECK(robot_set_wheel_rps(&rc, 0, -INFINITY, 100, ROBOT_SRC_RRC) == -1 && mt[0].pid.set_point == 0.0f,
          "Inf wheel rps dropped");
    CHECK(rc.rejected_cmds == 3, "rejections counted");
    enc_motor_set_speed(&mt[3], INFINITY);
    CHECK(mt[3].pid.set_point == 0.0f, "enc_motor: Inf becomes 0, not the speed limit");

    /* single owner */
    CHECK(robot_set_velocity(&rc, 0.1f, 0, 0, 1000, ROBOT_SRC_MICROROS) == 0 && rc.owner == ROBOT_SRC_MICROROS,
          "first mover owns the wheels");
    const float sp = mt[0].pid.set_point;
    CHECK(robot_set_wheel_rps(&rc, 0, -1.0f, 1200, ROBOT_SRC_RRC) == -1 && mt[0].pid.set_point == sp,
          "other source refused while the owner is active");
    CHECK(robot_set_velocity(&rc, 0.05f, 0, 0, 1300, ROBOT_SRC_MICROROS) == 0, "owner keeps commanding");
    robot_stop_mask(&rc, 0x0F); /* anyone may stop wheels */
    CHECK(mt[0].pid.set_point == 0.0f, "stop accepted from anyone");
    robot_stop(&rc, ROBOT_STOP_COMMAND);
    CHECK(rc.owner == ROBOT_SRC_NONE, "stop releases ownership");
    CHECK(robot_set_wheel_rps(&rc, 0, 0.5f, 1400, ROBOT_SRC_RRC) == 0 && rc.owner == ROBOT_SRC_RRC,
          "after a stop another source can take over");
    /* owner goes silent -> after the timeout another source may take over even before robot_tick */
    CHECK(robot_set_velocity(&rc, 0.1f, 0, 0, 1500, ROBOT_SRC_GAMEPAD) == -1, "gamepad refused during RRC");
    CHECK(robot_set_velocity(&rc, 0.1f, 0, 0, 2500, ROBOT_SRC_GAMEPAD) == 0 && rc.owner == ROBOT_SRC_GAMEPAD,
          "silent owner (> timeout) loses the wheels");
    robot_estop(&rc);
    CHECK(rc.owner == ROBOT_SRC_NONE && rc.estop, "e-stop from anyone releases and latches");
}

static void test_blink(void)
{
    blink_t b;
    int ons = 0, prev = 0;
    blink_init(&b);
    blink_set(&b, 100, 100, 3);
    for (int ms = 0; ms < 2000; ms++) {
        const int lvl = blink_tick(&b, 1);
        if (lvl && !prev) ons++;
        prev = lvl;
    }
    CHECK(ons == 3 && b.level == 0 && !b.active, "3-cycle pattern = 3 on pulses, then off");
    blink_set(&b, 1, 0, 0);
    CHECK(blink_tick(&b, 10) == 1, "on/off=0 is solid on");
    blink_set(&b, 0, 0, 0);
    CHECK(blink_tick(&b, 10) == 0, "on=0 cancels");
    blink_set(&b, 50, 50, 0);
    int toggles = 0;
    prev = 1;
    for (int ms = 0; ms < 1000; ms++) {
        const int lvl = blink_tick(&b, 1);
        if (lvl != prev) toggles++;
        prev = lvl;
    }
    CHECK(toggles >= 19, "repeat=0 blinks forever");
}

static uint8_t run_button(button_t *b, const uint8_t *levels, int n, uint8_t *all)
{
    uint8_t last = 0;
    *all = 0;
    for (int i = 0; i < n; i++) {
        const uint8_t ev = button_tick(b, levels[i], 10);
        *all |= ev;
        if (ev) last = ev;
    }
    return last;
}

static void test_button(void)
{
    button_t b;
    uint8_t seq[300], all;

    button_init(&b);
    memset(seq, 0, sizeof(seq));
    for (int i = 10; i < 20; i++) seq[i] = 1; /* 100 ms press */
    run_button(&b, seq, 100, &all);
    CHECK((all & BUTTON_EVENT_PRESSED) && (all & BUTTON_EVENT_CLICK) && !(all & BUTTON_EVENT_DOUBLE_CLICK),
          "single click -> PRESSED + CLICK");

    button_init(&b);
    memset(seq, 0, sizeof(seq));
    for (int i = 10; i < 20; i++) seq[i] = 1;
    for (int i = 30; i < 40; i++) seq[i] = 1;
    run_button(&b, seq, 150, &all);
    CHECK((all & BUTTON_EVENT_DOUBLE_CLICK) && !(all & BUTTON_EVENT_CLICK), "two quick presses -> DOUBLE_CLICK only");

    button_init(&b);
    memset(seq, 0, sizeof(seq));
    for (int i = 10; i < 200; i++) seq[i] = 1; /* 1.9 s hold */
    run_button(&b, seq, 250, &all);
    CHECK((all & BUTTON_EVENT_LONGPRESS) && !(all & BUTTON_EVENT_CLICK), "hold -> LONGPRESS, no click on release");

    button_init(&b);
    memset(seq, 0, sizeof(seq));
    seq[10] = 1; seq[11] = 0; seq[12] = 1; seq[13] = 0; /* 10 ms glitches */
    run_button(&b, seq, 100, &all);
    CHECK(all == 0, "bounce shorter than debounce is ignored");
}

static void test_pwm_servo(void)
{
    pwm_servo_t s;
    int prev = 1500, ticks = 0;
    pwm_servo_init(&s);
    pwm_servo_set_position(&s, 2500, 1000);
    do {
        pwm_servo_tick(&s);
        CHECK(s.current_duty >= prev, "upward ramp is monotonic");
        prev = s.current_duty;
        ticks++;
    } while (s.is_running && ticks < 200);
    CHECK(ticks == 50 && s.current_duty == 2500, "1000 ms = 50 ticks, ends exactly on target");
    pwm_servo_set_position(&s, 500, 500);
    ticks = 0;
    do {
        pwm_servo_tick(&s);
        CHECK(s.current_duty <= prev, "downward ramp is monotonic");
        prev = s.current_duty;
        ticks++;
    } while (s.is_running && ticks < 200);
    CHECK(s.current_duty == 500, "downward ends on target");
    pwm_servo_set_position(&s, 9999, 1);
    CHECK(s.target_duty == 2500 && s.duration == 20, "pulse and duration are clamped");
    pwm_servo_set_offset(&s, 500);
    pwm_servo_tick(&s);
    CHECK(s.offset == 100, "offset clamped to +-100");
}

// 한글: 손으로 계산한 프레임/체크섬과 PDF 업로드 예제 배치와 일치하는지 확인.
static void test_bus_servo(void)
{
    uint8_t f[BUS_SERVO_MAX_FRAME];
    /* move servo 1 to 500 in 1000 ms: checksum = ~(1+7+1+0xF4+1+0xE8+3) = 0x16 (hand computed) */
    const size_t n = bus_servo_build_move(1, 500, 1000, f);
    const uint8_t expect[] = {0x55, 0x55, 0x01, 0x07, 0x01, 0xF4, 0x01, 0xE8, 0x03, 0x16};
    CHECK(n == sizeof(expect) && memcmp(f, expect, n) == 0, "move frame matches hand-computed bytes");

    /* position-read request frame: 55 55 05 03 1C xx, checksum ~(5+3+28)=~36=0xDB */
    const size_t n2 = bus_servo_build(5, BUS_CMD_POS_READ, NULL, 0, f);
    CHECK(n2 == 6 && f[5] == 0xDB, "pos read request checksum");

    /* reply: servo 5, cmd 28, pos 833 (0x0341): 55 55 05 05 1C 41 03 cs ; cs=~(5+5+28+0x41+3)=~(0x6E)=0x95 */
    const uint8_t reply[] = {0x55, 0x55, 0x05, 0x05, 0x1C, 0x41, 0x03, 0x95};
    bus_servo_rx_t rx;
    bus_servo_reply_t r;
    int got = 0;
    bus_servo_rx_init(&rx);
    for (size_t i = 0; i < sizeof(reply); i++) got = bus_servo_rx_feed(&rx, reply[i], &r);
    CHECK(got == 1 && r.id == 5 && r.cmd == 28 && r.nparams == 2 && r.params[0] == 0x41 && r.params[1] == 0x03,
          "reply parsed");
    uint8_t bad[sizeof(reply)];
    memcpy(bad, reply, sizeof(reply));
    bad[7] ^= 0xFF;
    got = 0;
    for (size_t i = 0; i < sizeof(bad); i++) got |= bus_servo_rx_feed(&rx, bad[i], &r);
    CHECK(got == 0, "bad checksum rejected");

    bus_servo_plan_t p;
    const uint8_t read_pos[] = {0x05, 5};
    CHECK(bus_servo_plan_from_rrc(read_pos, 2, &p) && p.cmd == BUS_CMD_POS_READ && p.expects_reply && p.id == 5, "plan 0x05");
    uint8_t up[16];
    const uint8_t pos_reply[] = {0x41, 0x03};
    const size_t un = bus_servo_make_upload(&p, 1, pos_reply, 2, up);
    const uint8_t up_expect[] = {5, 0x05, 0x00, 0x41, 0x03}; /* matches the PDF "servo 5 = 833" example */
    CHECK(un == 5 && memcmp(up, up_expect, 5) == 0, "upload matches PDF example layout");
    const size_t fn = bus_servo_make_upload(&p, 0, NULL, 0, up);
    CHECK(fn == 5 && up[2] == 0xFF, "failed read uploads -1");

    const uint8_t id_write[] = {0x10, 3, 7};
    CHECK(bus_servo_plan_from_rrc(id_write, 3, &p) && p.cmd == BUS_CMD_ID_WRITE && p.params[0] == 7 && !p.expects_reply, "plan id write");
    const uint8_t lim[] = {0x30, 2, 0x64, 0x00, 0x90, 0x03};
    CHECK(bus_servo_plan_from_rrc(lim, 6, &p) && p.cmd == BUS_CMD_ANGLE_LIMIT_WRITE && p.nparams == 4, "plan angle limit write");
    const uint8_t unload[] = {0x0B, 4}, load[] = {0x0C, 4}, tq[] = {0x0D, 4};
    CHECK(bus_servo_plan_from_rrc(unload, 2, &p) && p.params[0] == 0, "0x0B = unload (limp), verified on the robot");
    CHECK(bus_servo_plan_from_rrc(load, 2, &p) && p.params[0] == 1, "0x0C = load (hold)");
    CHECK(bus_servo_plan_from_rrc(tq, 2, &p) && p.cmd == BUS_CMD_LOAD_OR_UNLOAD_READ && p.expects_reply, "0x0D = read torque state");
    const uint8_t bogus[] = {0x77, 1};
    CHECK(!bus_servo_plan_from_rrc(bogus, 2, &p), "unknown subcommand rejected");
}

static void test_sbus(void)
{
    /* build a frame with channel i = 192 + 100*i by packing 11-bit values LSB first */
    uint8_t f[25] = {0};
    f[0] = 0x0F;
    int bit = 0;
    for (int ch = 0; ch < 16; ch++) {
        const uint16_t v = (uint16_t)(192 + 100 * ch);
        for (int b = 0; b < 11; b++, bit++) {
            if ((v >> b) & 1) f[1 + bit / 8] |= (uint8_t)(1u << (bit % 8));
        }
    }
    f[23] = 0x01 | 0x08; /* ch17 + failsafe */
    sbus_status_t st;
    CHECK(sbus_decode_frame(f, &st) == 0, "valid frame");
    for (int ch = 0; ch < 16; ch++) CHECK(st.channels[ch] == 192 + 100 * ch, "channel value");
    CHECK(st.ch17 == 1 && st.ch18 == 0 && st.signal_loss == 0 && st.fail_safe == 1, "flag bits");
    f[0] = 0x00;
    CHECK(sbus_decode_frame(f, &st) == -1, "bad header rejected");

    f[0] = 0x0F;
    sbus_stream_t s;
    sbus_stream_init(&s);
    int got = 0;
    for (int junk = 0; junk < 7; junk++) got |= sbus_stream_feed(&s, 0x55, &st);
    for (int i = 0; i < 25; i++) got |= sbus_stream_feed(&s, f[i], &st);
    CHECK(got == 1 && st.channels[15] == 192 + 1500, "stream front-end resyncs after junk");
}

static void test_gamepad(void)
{
    const uint8_t rep[8] = {128, 0, 255, 128, 0x20 | 0x02, 0x00, 0, 0}; /* hat=2, button bit5 (CROSS) */
    gamepad_state_t g;
    CHECK(gamepad_parse_report(&GAMEPAD_LAYOUT_DEFAULT, rep, 8, &g) == 0, "parse");
    CHECK(g.lx == 0 && g.ly == -128 && g.rx == 127 && g.ry == 0, "axes centred at 128");
    CHECK(g.hat == (0x08 | 2), "hat pressed");
    CHECK(g.buttons == GAMEPAD_MASK_CROSS, "button mapped");
    CHECK(gamepad_parse_report(&GAMEPAD_LAYOUT_DEFAULT, rep, 3, &g) == -1, "short report rejected");
}

// 한글: 가짜 I2C 버스: MPU6050/QMI8658 탐색과 변환을 하드웨어 없이 시험한다.
/* ---------- fake I2C bus ---------- */
typedef struct {
    uint8_t mpu_regs[256];
    uint8_t qmi_regs[256];
    int has_mpu, has_qmi;
    uint8_t last_written_reg[256];
} fakebus_t;

static int fb_read(void *ctx, uint8_t addr, uint8_t reg, uint8_t *d, size_t n)
{
    fakebus_t *f = ctx;
    if ((addr == 0x68 || addr == 0x69) && f->has_mpu && addr == 0x68) { memcpy(d, &f->mpu_regs[reg], n); return 0; }
    if (addr == 0x6B && f->has_qmi) { memcpy(d, &f->qmi_regs[reg], n); return 0; }
    return -1;
}
static int fb_write(void *ctx, uint8_t addr, uint8_t reg, const uint8_t *d, size_t n)
{
    fakebus_t *f = ctx;
    if (addr == 0x68 && f->has_mpu) { memcpy(&f->mpu_regs[reg], d, n); return 0; }
    if (addr == 0x6B && f->has_qmi) {
        memcpy(&f->qmi_regs[reg], d, n);
        if (reg == 0x60 && d[0] == 0xB0) f->qmi_regs[0x4D] = 0x80; /* soft reset done / 리셋 완료 */
        return 0;
    }
    return -1;
}
static void fb_delay(uint32_t ms) { (void)ms; }

static void test_imu(void)
{
    fakebus_t fb;
    memset(&fb, 0, sizeof(fb));
    fb.has_mpu = 1;
    fb.mpu_regs[0x75] = 0x68;
    /* accel = (0, 0, +16384) = 1 g on z ; gyro = (655, -655, 0) -> +-10 dps at 65.5 LSB/dps (rounded) */
    const int16_t ax = 0, ay = 0, az = 16384, gx = 655, gy = -655, gz = 0;
    const int16_t v[7] = {ax, ay, az, 0, gx, gy, gz};
    for (int i = 0; i < 7; i++) {
        fb.mpu_regs[0x3B + 2 * i] = (uint8_t)((uint16_t)v[i] >> 8);
        fb.mpu_regs[0x3B + 2 * i + 1] = (uint8_t)v[i];
    }
    i2c_bus_t bus = {fb_write, fb_read, fb_delay, &fb};
    imu_t imu;
    CHECK(imu_init(&imu, &bus, NULL) == 0 && imu.kind == IMU_MPU6050, "MPU6050 detected");
    CHECK(fb.mpu_regs[0x19] == 8 && fb.mpu_regs[0x6B] == 0x01 && fb.mpu_regs[0x1B] == 0x08, "MPU configured (111 Hz, +-500 dps)");
    float a[3], g[3];
    CHECK(imu_read(&imu, a, g) == 0, "read");
    NEAR(a[2], 1.0f, 1e-4f, "accel z = 1 g");
    NEAR(g[0], 10.0f, 0.01f, "gyro x");
    NEAR(g[1], -10.0f, 0.01f, "gyro y");

    const imu_axis_map_t flip = {{0, 1, 2}, {1, 1, -1}}; /* chip Z up -> board Z down */
    CHECK(imu_init(&imu, &bus, &flip) == 0, "re-init with axis map");
    imu_read(&imu, a, g);
    NEAR(a[2], -1.0f, 1e-4f, "axis map flips z");

    memset(&fb, 0, sizeof(fb));
    fb.has_qmi = 1;
    fb.qmi_regs[0x00] = 0x05;
    const int16_t q[6] = {8192, 0, 0, 0, 0, 640}; /* 1 g on x (+-4 g), 10 dps on z (64 LSB/dps) */
    for (int i = 0; i < 6; i++) {
        fb.qmi_regs[0x35 + 2 * i] = (uint8_t)q[i];
        fb.qmi_regs[0x35 + 2 * i + 1] = (uint8_t)((uint16_t)q[i] >> 8);
    }
    CHECK(imu_init(&imu, &bus, NULL) == 0 && imu.kind == IMU_QMI8658, "QMI8658 detected");
    imu_read(&imu, a, g);
    NEAR(a[0], 1.0f, 1e-4f, "QMI accel x");
    NEAR(g[2], 10.0f, 1e-3f, "QMI gyro z");
    CHECK(fb.qmi_regs[0x60] == 0xB0 && fb.qmi_regs[0x08] == 0x03, "QMI soft reset then sensors enabled");

    /* frozen data: identical raw samples -> IMU_ERR_FROZEN after IMU_FROZEN_SAMPLES, recovers on change */
    int frozen_at = -1;
    for (int i = 0; i < 40; i++) {
        if (imu_read(&imu, a, g) == IMU_ERR_FROZEN && frozen_at < 0) frozen_at = i;
    }
    CHECK(frozen_at == IMU_FROZEN_SAMPLES - 1, "frozen sensor reported after IMU_FROZEN_SAMPLES identical reads");
    fb.qmi_regs[0x35] ^= 1; /* LSB noise returns */
    CHECK(imu_read(&imu, a, g) == 0, "changing data reads fine again");
    fb.qmi_regs[0x35] ^= 1;
    CHECK(imu_read(&imu, a, g) == 0 && imu.same_count == 0, "alternating noise is never frozen");

    memset(&fb, 0, sizeof(fb));
    CHECK(imu_init(&imu, &bus, NULL) == -1 && imu.kind == IMU_NONE, "no IMU -> error, not a crash");
    CHECK(imu_read(&imu, a, g) == -1, "read without IMU fails");
}

static void test_local_drive(void)
{
    enc_motor_t mt[4];
    enc_motor_t *mp[4] = {&mt[0], &mt[1], &mt[2], &mt[3]};
    const mecanum_cfg_t cfg = {0.216f, 0.195f, 0.097f};
    robot_ctrl_t rc;
    local_drive_t ld;
    for (int i = 0; i < 4; i++) enc_motor_init(&mt[i], 1320, 5.0f, 63, 2.6f, 2.4f, 60000, 1, set_pulse_noop, NULL);
    robot_init(&rc, mp, &cfg, 1);
    local_drive_init(&ld, &rc);

    CHECK(local_drive_char(&ld, 'A', 10, ROBOT_SRC_BLUETOOTH) == 1 && mt[0].pid.set_point > 0 && mt[2].pid.set_point < 0, "A = forward");
    CHECK(rc.last_source == ROBOT_SRC_BLUETOOTH, "source recorded");
    local_drive_char(&ld, 'I', 20, ROBOT_SRC_BLUETOOTH);
    CHECK(mt[0].pid.set_point == 0.0f && rc.stop_reason == ROBOT_STOP_COMMAND, "I = stop");
    local_drive_char(&ld, 'n', 30, ROBOT_SRC_BLUETOOTH);
    CHECK(mt[0].pid.set_point < 0 && mt[1].pid.set_point > 0, "n = strafe left (same as mecanum_inverse vy>0)");
    const float before = ld.speed_mps;
    local_drive_char(&ld, 'S', 40, ROBOT_SRC_BLUETOOTH);
    CHECK(ld.speed_mps > before, "S speeds up");
    for (int i = 0; i < 20; i++) local_drive_char(&ld, 'S', 40, ROBOT_SRC_BLUETOOTH);
    CHECK(ld.speed_mps <= ld.max_mps + 1e-6f, "speed capped");
    CHECK(local_drive_char(&ld, '?', 50, ROBOT_SRC_BLUETOOTH) == 0, "unknown char ignored");
    CHECK(local_drive_atc(0, 100, 60) == 'A' && local_drive_atc(0, -100, 60) == 'E' && local_drive_atc(-100, 0, 60) == 'C' &&
          local_drive_atc(100, 100, 60) == 'H' && local_drive_atc(10, 10, 60) == 'I', "vendor A_T_C mapping");
    CHECK(local_drive_hat_char(0x08 | 0) == 'B' && local_drive_hat_char(0) == 'I', "hat -> char");
}

static void test_battery(void)
{
    battery_t b;
    battery_init(&b);
    /* vref=1500 counts (Vdda ~3.3 V), pb0 = 1100 counts -> 1210/1500*1100*11 = 9760.7 mV */
    CHECK(battery_update(&b, 1500, 1100) == 1, "accept");
    CHECK(b.millivolts >= 9760 && b.millivolts <= 9762, "mV formula");
    CHECK(battery_update(&b, 0, 1100) == 0 && battery_update(&b, 1500, 4095) == 0, "reject 0 / 4095");
    CHECK(battery_update(&b, 100, 4000) == 0, "reject > 20 V");
    for (int i = 0; i < 200; i++) battery_update(&b, 1500, 1200); /* 10.65 V */
    CHECK(b.millivolts > 10600 && b.millivolts < 10700, "filter converges");
}

int main(void)
{
    test_pid();
    test_enc_motor_tracks();
    test_enc_motor_wraps();
    test_enc_motor_dead_zone_and_fault();
    test_enc_motor_runaway_latch();
    test_enc_motor_sign_guard();
    test_mecanum();
    test_robot_ctrl();
    test_robot_arbitration();
    test_blink();
    test_button();
    test_pwm_servo();
    test_bus_servo();
    test_sbus();
    test_gamepad();
    test_imu();
    test_battery();
    test_local_drive();
    if (failures) {
        printf("%d CHECK(S) FAILED\n", failures);
        return 1;
    }
    printf("ALL CORE TESTS PASSED\n");
    return 0;
}
