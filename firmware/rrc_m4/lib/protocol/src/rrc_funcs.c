// 한글: FUNC별 팩/언팩 구현. 바이트 배치는 공식 PDF/문서와 실기 캡처 기준.
#include "rrc_funcs.h"

#include <string.h>

/* ---- little-endian helpers (portable; don't assume struct packing/host endianness) ---- */
// 한글: 리틀엔디안 읽기/쓰기 헬퍼(구조체 패킹/호스트 엔디안에 의존하지 않음).
static uint16_t rd_u16le(const uint8_t *p) { return (uint16_t)(p[0] | (p[1] << 8)); }
static void wr_u16le(uint8_t *p, uint16_t v) { p[0] = (uint8_t)(v & 0xFF); p[1] = (uint8_t)(v >> 8); }
static void wr_i16le(uint8_t *p, int16_t v) { wr_u16le(p, (uint16_t)v); }
static void wr_f32le(uint8_t *p, float v) {
    uint32_t bits;
    memcpy(&bits, &v, sizeof(bits));
    p[0] = (uint8_t)(bits & 0xFF);
    p[1] = (uint8_t)((bits >> 8) & 0xFF);
    p[2] = (uint8_t)((bits >> 16) & 0xFF);
    p[3] = (uint8_t)((bits >> 24) & 0xFF);
}
static float rd_f32le(const uint8_t *p) {
    uint32_t bits = (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
    float v;
    memcpy(&v, &bits, sizeof(v));
    return v;
}

/* ---- FUNC 0x00 ---- */
// 한글: FUNC0 배터리: 04 + u16 LE mV(벤더 PDF에 없고 실기로 확인한 값).
size_t rrc_pack_battery_mv(uint16_t millivolts, uint8_t *data_out) {
    data_out[0] = 0x04;
    wr_u16le(&data_out[1], millivolts);
    return 3;
}

/* ---- FUNC 0x01 ---- */
// 한글: FUNC1 LED: led_id u8 + 켜짐/꺼짐 ms + 반복 횟수(u16×3). 길이가 7이 아니면 거부.
int rrc_unpack_led(const uint8_t *data, uint8_t len, rrc_led_cmd_t *out) {
    if (len != 7) return 0;
    out->led_id = data[0];
    out->on_ms = rd_u16le(&data[1]);
    out->off_ms = rd_u16le(&data[3]);
    out->cycles = rd_u16le(&data[5]);
    return 1;
}

/* ---- FUNC 0x02 ---- */
// 한글: FUNC2 부저: 주파수 + 켜짐/꺼짐 ms + 반복(u16×4, 총 8바이트).
int rrc_unpack_buzzer(const uint8_t *data, uint8_t len, rrc_buzzer_cmd_t *out) {
    if (len != 8) return 0;
    out->freq_hz = rd_u16le(&data[0]);
    out->on_ms = rd_u16le(&data[2]);
    out->off_ms = rd_u16le(&data[4]);
    out->cycles = rd_u16le(&data[6]);
    return 1;
}

/* ---- FUNC 0x03 ---- */
// 한글: FUNC3 다중 속도 설정(서브커맨드 0x01): N개의 (모터 id u8, rps float32). 길이가 2+5N과 다르면 거부.
int rrc_unpack_motor(const uint8_t *data, uint8_t len, rrc_motor_cmd_t *out) {
    if (len < 2) return 0;
    uint8_t sub = data[0];
    uint8_t count = data[1];
    if (sub != RRC_SERVO_SUB_MOVE_MULTI) return 0;
    if (count > RRC_MOTOR_MAX_COUNT) return 0;
    if ((size_t)len != 2u + (size_t)count * 5u) return 0;
    out->subcommand = sub;
    out->count = count;
    const uint8_t *p = &data[2];
    for (uint8_t i = 0; i < count; i++) {
        out->speeds[i].id = p[0];
        out->speeds[i].rps = rd_f32le(&p[1]);
        p += 5;
    }
    return 1;
}

int rrc_unpack_motor_ex(const uint8_t *data, uint8_t len, rrc_motor_cmd_ex_t *out) {
    if (len < 2) return 0;
    memset(out, 0, sizeof(*out));
    out->subcommand = data[0];
    switch (data[0]) {
    case RRC_MOTOR_SUB_SET_SINGLE:
        if (len != 6) return 0;
        out->count = 1;
        out->speeds[0].id = data[1];
        out->speeds[0].rps = rd_f32le(&data[2]);
        return 1;
    case RRC_MOTOR_SUB_SET_MULTI: {
        rrc_motor_cmd_t m;
        if (!rrc_unpack_motor(data, len, &m)) return 0;
        out->count = m.count;
        for (uint8_t i = 0; i < m.count; i++) out->speeds[i] = m.speeds[i];
        return 1;
    }
    case RRC_MOTOR_SUB_STOP_ONE:
        if (len != 2) return 0;
        out->stop_id = data[1];
        return 1;
    case RRC_MOTOR_SUB_STOP_MASK:
        if (len != 2) return 0;
        out->stop_mask = data[1];
        return 1;
    default:
        return 0;
    }
}

/* ---- FUNC 0x04 ---- */
// 한글: FUNC4 다중 이동: 시간 ms, 개수, N×(id, 펄스 us 500~2500).
int rrc_unpack_pwm_servo_move_multi(const uint8_t *data, uint8_t len, rrc_pwm_servo_move_multi_t *out) {
    if (len < 4) return 0;
    if (data[0] != RRC_SERVO_SUB_MOVE_MULTI) return 0;
    uint8_t count = data[3];
    if (count > RRC_PWM_SERVO_MAX_COUNT) return 0;
    if ((size_t)len != 4u + (size_t)count * 3u) return 0;
    out->time_ms = rd_u16le(&data[1]);
    out->count = count;
    const uint8_t *p = &data[4];
    for (uint8_t i = 0; i < count; i++) {
        out->targets[i].id = p[0];
        out->targets[i].pulse = rd_u16le(&p[1]);
        p += 3;
    }
    return 1;
}

int rrc_unpack_pwm_servo_move_single(const uint8_t *data, uint8_t len, rrc_pwm_servo_move_single_t *out) {
    if (len != 6) return 0;
    if (data[0] != RRC_SERVO_SUB_MOVE_SINGLE) return 0;
    out->time_ms = rd_u16le(&data[1]);
    out->id = data[3];
    out->pulse = rd_u16le(&data[4]);
    return 1;
}

int rrc_unpack_pwm_servo_read_request(const uint8_t *data, uint8_t len, uint8_t *subcommand, uint8_t *servo_id) {
    if (len != 2) return 0;
    if (data[0] != RRC_SERVO_SUB_READ_POSITION && data[0] != RRC_SERVO_SUB_READ_DEVIATION) return 0;
    *subcommand = data[0];
    *servo_id = data[1];
    return 1;
}

int rrc_unpack_pwm_servo_set_deviation(const uint8_t *data, uint8_t len, uint8_t *servo_id, int8_t *deviation) {
    if (len != 3) return 0;
    if (data[0] != RRC_SERVO_SUB_SET_DEVIATION) return 0;
    *servo_id = data[1];
    *deviation = (int8_t)data[2];
    return 1;
}

size_t rrc_pack_pwm_servo_position(uint8_t servo_id, uint16_t pulse, uint8_t *data_out) {
    data_out[0] = servo_id;
    data_out[1] = RRC_SERVO_SUB_READ_POSITION;
    wr_u16le(&data_out[2], pulse);
    return 4;
}

size_t rrc_pack_pwm_servo_deviation(uint8_t servo_id, int8_t deviation, uint8_t *data_out) {
    data_out[0] = servo_id;
    /* PDF text shows 0x05 here too (likely a copy/paste artifact, see header
     * comment) -- callers should treat this byte's exact value as unverified. */
    data_out[1] = RRC_SERVO_SUB_READ_POSITION;
    data_out[2] = (uint8_t)deviation;
    return 3;
}

/* ---- FUNC 0x05 ---- */
// 한글: FUNC5 다중 이동: 시간 ms, 개수, N×(id, 펄스 0~1000 = 0~240도).
int rrc_unpack_bus_servo_move(const uint8_t *data, uint8_t len, rrc_bus_servo_move_t *out) {
    if (len < 4) return 0;
    if (data[0] != RRC_SERVO_SUB_MOVE_MULTI) return 0;
    uint8_t count = data[3];
    if (count > RRC_BUS_SERVO_MAX_COUNT) return 0;
    if ((size_t)len != 4u + (size_t)count * 3u) return 0;
    out->time_ms = rd_u16le(&data[1]);
    out->count = count;
    const uint8_t *p = &data[4];
    for (uint8_t i = 0; i < count; i++) {
        out->targets[i].id = p[0];
        out->targets[i].pulse = rd_u16le(&p[1]);
        p += 3;
    }
    return 1;
}

int rrc_unpack_bus_servo_read_position(const uint8_t *data, uint8_t len, uint8_t *servo_id) {
    if (len != 2) return 0;
    if (data[0] != RRC_SERVO_SUB_READ_POSITION) return 0;
    *servo_id = data[1];
    return 1;
}

// 한글: 버스 서보 위치 응답: id, 05, success(0 정상/-1 실패), 위치 int16 LE.
size_t rrc_pack_bus_servo_position(uint8_t servo_id, int8_t success, int16_t pulse, uint8_t *data_out) {
    data_out[0] = servo_id;
    data_out[1] = RRC_SERVO_SUB_READ_POSITION;
    data_out[2] = (uint8_t)success;
    wr_i16le(&data_out[3], pulse);
    return 5;
}

/* ---- FUNC 0x06 ---- */
size_t rrc_pack_key_event(uint8_t button_id, uint8_t event, uint8_t *data_out) {
    data_out[0] = button_id;
    data_out[1] = event;
    return 2;
}

/* ---- FUNC 0x07 ---- */
// 한글: FUNC7 IMU: float32 6개(가속도 g ×3, 자이로 deg/s ×3), 센서 원시 축.
size_t rrc_pack_imu(const rrc_imu_sample_t *sample, uint8_t *data_out) {
    wr_f32le(&data_out[0], sample->accel_g[0]);
    wr_f32le(&data_out[4], sample->accel_g[1]);
    wr_f32le(&data_out[8], sample->accel_g[2]);
    wr_f32le(&data_out[12], sample->gyro_dps[0]);
    wr_f32le(&data_out[16], sample->gyro_dps[1]);
    wr_f32le(&data_out[20], sample->gyro_dps[2]);
    return 24;
}

/* ---- FUNC 0x08 ---- */
// 한글: FUNC8 게임패드 7바이트: 버튼 u16, hat, 왼/오른 스틱 x,y(int8).
size_t rrc_pack_gamepad(const rrc_gamepad_state_t *state, uint8_t *data_out) {
    wr_u16le(&data_out[0], state->buttons);
    data_out[2] = state->hat;
    data_out[3] = (uint8_t)state->lx;
    data_out[4] = (uint8_t)state->ly;
    data_out[5] = (uint8_t)state->rx;
    data_out[6] = (uint8_t)state->ry;
    return 7;
}

/* ---- FUNC 0x09 ---- */
// 한글: FUNC9 SBUS 36바이트: 채널 int16×16 + ch17/ch18/신호 손실/failsafe.
size_t rrc_pack_sbus(const rrc_sbus_frame_t *frame, uint8_t *data_out) {
    for (int i = 0; i < 16; i++) {
        wr_i16le(&data_out[i * 2], frame->channels[i]);
    }
    data_out[32] = frame->ch17;
    data_out[33] = frame->ch18;
    data_out[34] = frame->signal_loss;
    data_out[35] = frame->fail_safe;
    return 36;
}
