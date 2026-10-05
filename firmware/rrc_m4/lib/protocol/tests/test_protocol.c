// 한글: 호스트 단위 시험(하드웨어/크로스 툴체인 불필요). 골든 벡터는 PDF 예제와 실기에서 확인한 프레임이다.
/* Host-native unit tests: no target hardware or cross toolchain needed.
 * Golden vectors come from two places:
 *  - firmware_source/"RRC Communication Protocol...pdf" worked examples
 *  - bytes this project actually sent to the real robot in this session
 *    (buzzer beep, bus servo move) and confirmed worked (audible beep,
 *    servo moved) -- see the conversation / troubleshooting history.
 */
#include <stdio.h>
#include <string.h>

#include "rrc_funcs.h"
#include "rrc_protocol.h"

static int failures = 0;

#define CHECK(cond, msg) do { \
    if (!(cond)) { \
        printf("FAIL: %s (%s:%d)\n", msg, __FILE__, __LINE__); \
        failures++; \
    } \
} while (0)

// 한글: 표준 CRC-8/MAXIM 검증값("123456789" → 0xA1).
static void test_crc8_maxim_check_value(void) {
    /* Standard MAXIM/DOW-CRC check value for the ASCII string "123456789". */
    const uint8_t check[] = "123456789";
    CHECK(rrc_crc8_maxim(check, 9) == 0xA1, "crc8_maxim check value");
}

// 한글: 실제 로봇에 보내 소리가 난 프레임을 그대로 회귀시험으로 남긴 것.
static void test_buzzer_real_capture(void) {
    /* Frame this project actually sent to the robot: freq=1400Hz, on=200ms,
     * off=100ms, cycles=2 -- produced an audible beep on real hardware. */
    const uint8_t expected[] = {0xAA, 0x55, 0x02, 0x08, 0x78, 0x05, 0xC8, 0x00,
                                 0x64, 0x00, 0x02, 0x00, 0xBF};
    uint8_t data[8];
    data[0] = 0x78; data[1] = 0x05; /* 1400 */
    data[2] = 0xC8; data[3] = 0x00; /* 200 */
    data[4] = 0x64; data[5] = 0x00; /* 100 */
    data[6] = 0x02; data[7] = 0x00; /* 2 */

    uint8_t out[RRC_MAX_FRAME_LEN];
    size_t n = rrc_encode(RRC_FUNC_BUZZER, data, sizeof(data), out);
    CHECK(n == sizeof(expected), "buzzer frame length");
    CHECK(memcmp(out, expected, sizeof(expected)) == 0, "buzzer frame bytes match real capture");

    rrc_buzzer_cmd_t cmd;
    CHECK(rrc_unpack_buzzer(data, sizeof(data), &cmd), "buzzer unpack ok");
    CHECK(cmd.freq_hz == 1400 && cmd.on_ms == 200 && cmd.off_ms == 100 && cmd.cycles == 2,
          "buzzer unpack values");
}

// 한글: 공식 PDF 예제(LED 10회, 500ms 켜짐/300ms 꺼짐)와 일치하는지 확인.
static void test_led_pdf_example(void) {
    /* PDF example 2: blink 10x, on 500ms, off 300ms. */
    uint8_t data[7] = {0x01, 0xF4, 0x01, 0x2C, 0x01, 0x0A, 0x00};
    rrc_led_cmd_t cmd;
    CHECK(rrc_unpack_led(data, sizeof(data), &cmd), "led unpack ok");
    CHECK(cmd.led_id == 1 && cmd.on_ms == 500 && cmd.off_ms == 300 && cmd.cycles == 10,
          "led unpack values match PDF example");
}

static void test_motor_roundtrip(void) {
    /* 4 wheels, ids 0..3, mixed signs -- matches jetrover_base's wire format. */
    uint8_t data[2 + 4 * 5];
    data[0] = RRC_SERVO_SUB_MOVE_MULTI;
    data[1] = 4;
    float speeds[4] = {0.2f, 0.2f, -0.2f, -0.2f};
    for (int i = 0; i < 4; i++) {
        data[2 + i * 5] = (uint8_t)i;
        memcpy(&data[2 + i * 5 + 1], &speeds[i], 4);
    }
    rrc_motor_cmd_t cmd;
    CHECK(rrc_unpack_motor(data, sizeof(data), &cmd), "motor unpack ok");
    CHECK(cmd.count == 4, "motor count");
    for (int i = 0; i < 4; i++) {
        CHECK(cmd.speeds[i].id == (uint8_t)i, "motor id");
        CHECK(cmd.speeds[i].rps == speeds[i], "motor rps");
    }
}

static void test_pwm_servo_pdf_example(void) {
    /* "Control servo 1 to rotate to 90 deg within 1s, pulse 1500". */
    uint8_t data[6] = {0x03, 0xE8, 0x03, 0x01, 0xDC, 0x05};
    rrc_pwm_servo_move_single_t cmd;
    CHECK(rrc_unpack_pwm_servo_move_single(data, sizeof(data), &cmd), "pwm single unpack ok");
    CHECK(cmd.time_ms == 1000 && cmd.id == 1 && cmd.pulse == 1500, "pwm single values");
}

static void test_bus_servo_pdf_example(void) {
    /* "Control bus servo 1 and 2 to 833 and 1000 pulse within 1s". */
    uint8_t data[10] = {0x01, 0xE8, 0x03, 0x02, 0x01, 0x41, 0x03, 0x02, 0xE8, 0x03};
    rrc_bus_servo_move_t cmd;
    CHECK(rrc_unpack_bus_servo_move(data, sizeof(data), &cmd), "bus servo unpack ok");
    CHECK(cmd.time_ms == 1000 && cmd.count == 2, "bus servo header");
    CHECK(cmd.targets[0].id == 1 && cmd.targets[0].pulse == 833, "bus servo target 1");
    CHECK(cmd.targets[1].id == 2 && cmd.targets[1].pulse == 1000, "bus servo target 2");
}

static void test_bus_servo_position_real_capture(void) {
    /* This project actually read servo 10's position live: success=0, pulse=507. */
    uint8_t data[5];
    size_t n = rrc_pack_bus_servo_position(10, 0, 507, data);
    CHECK(n == 5, "bus servo position pack length");
    uint8_t servo_id;
    CHECK(rrc_unpack_bus_servo_read_position((uint8_t[]){0x05, 10}, 2, &servo_id), "bus servo read request unpack");
    CHECK(servo_id == 10, "bus servo read request id");
}

static void test_imu_roundtrip(void) {
    rrc_imu_sample_t sample = {
        .accel_g = {0.171f, 0.026f, -0.960f},
        .gyro_dps = {-9.902f, -12.182f, 0.760f},
    };
    uint8_t data[24];
    CHECK(rrc_pack_imu(&sample, data) == 24, "imu pack length");

    uint8_t frame[RRC_MAX_FRAME_LEN];
    size_t flen = rrc_encode(RRC_FUNC_IMU, data, 24, frame);

    rrc_parser_t parser;
    rrc_parser_init(&parser);
    rrc_parser_feed(&parser, frame, flen);
    rrc_frame_t out;
    CHECK(rrc_parser_next(&parser, &out) == 1, "imu frame parses");
    CHECK(out.func == RRC_FUNC_IMU && out.data_len == 24, "imu frame header");
    CHECK(memcmp(out.data, data, 24) == 0, "imu frame payload round-trip");
}

static void test_gamepad_pack(void) {
    rrc_gamepad_state_t state = {.buttons = 0x1234, .hat = 5, .lx = -10, .ly = 20, .rx = -30, .ry = 40};
    uint8_t data[7];
    CHECK(rrc_pack_gamepad(&state, data) == 7, "gamepad pack length");
    CHECK(data[0] == 0x34 && data[1] == 0x12, "gamepad buttons LE");
    CHECK(data[2] == 5, "gamepad hat");
    CHECK((int8_t)data[3] == -10 && (int8_t)data[4] == 20 && (int8_t)data[5] == -30 && (int8_t)data[6] == 40,
          "gamepad stick values");
}

static int16_t rd_i16le_test(const uint8_t *p) { return (int16_t)(p[0] | (p[1] << 8)); }

static void test_sbus_pack(void) {
    rrc_sbus_frame_t frame = {0};
    for (int i = 0; i < 16; i++) frame.channels[i] = (int16_t)(1000 + i);
    frame.ch17 = 1; frame.ch18 = 0; frame.signal_loss = 0; frame.fail_safe = 0;
    uint8_t data[36];
    CHECK(rrc_pack_sbus(&frame, data) == 36, "sbus pack length");
    CHECK(rd_i16le_test(&data[0]) == 1000, "sbus channel 0");
    CHECK(data[32] == 1, "sbus ch17");
}

static void test_parser_resync_on_corrupt_frame(void) {
    /* A corrupted frame (bad CRC) followed by a valid one -- parser must drop
     * only the corrupt bytes and still recover the valid frame, matching
     * jetrover_base's host-side parser behavior. */
    uint8_t good[RRC_MAX_FRAME_LEN];
    uint8_t data[3] = {0x04, 0x05, 0x06};
    size_t glen = rrc_encode(RRC_FUNC_KEY, data, 3, good);

    uint8_t stream[RRC_MAX_FRAME_LEN * 2];
    size_t pos = 0;
    /* corrupt frame: valid header/len, garbage data, wrong crc */
    stream[pos++] = 0xAA; stream[pos++] = 0x55; stream[pos++] = 0x06; stream[pos++] = 0x02;
    stream[pos++] = 0xDE; stream[pos++] = 0xAD; stream[pos++] = 0x00; /* bad crc */
    memcpy(&stream[pos], good, glen);
    pos += glen;

    rrc_parser_t parser;
    rrc_parser_init(&parser);
    rrc_parser_feed(&parser, stream, pos);
    rrc_frame_t out;
    int got = rrc_parser_next(&parser, &out);
    CHECK(got == 1, "parser recovers after corrupt frame");
    if (got) {
        CHECK(out.func == RRC_FUNC_KEY && out.data_len == 3, "recovered frame header");
    }
}

int main(void) {
    test_crc8_maxim_check_value();
    test_buzzer_real_capture();
    test_led_pdf_example();
    test_motor_roundtrip();
    test_pwm_servo_pdf_example();
    test_bus_servo_pdf_example();
    test_bus_servo_position_real_capture();
    test_imu_roundtrip();
    test_gamepad_pack();
    test_sbus_pack();
    test_parser_resync_on_corrupt_frame();

    if (failures == 0) {
        printf("ALL TESTS PASSED\n");
        return 0;
    }
    printf("%d TEST(S) FAILED\n", failures);
    return 1;
}
