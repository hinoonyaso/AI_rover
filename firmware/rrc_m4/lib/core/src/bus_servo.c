/* 한글: 버스 서보 프레임 생성/파서/RRC FUNC5 매핑 구현. */
#include "core/bus_servo.h"

static uint8_t checksum(const uint8_t *frame_from_id, uint8_t n)
{
    uint8_t sum = 0;
    for (uint8_t i = 0; i < n; ++i) {
        sum = (uint8_t)(sum + frame_from_id[i]);
    }
    return (uint8_t)~sum;
}

size_t bus_servo_build(uint8_t id, uint8_t cmd, const uint8_t *params, uint8_t nparams, uint8_t *out)
{
    if (nparams > BUS_SERVO_MAX_PARAMS) {
        return 0;
    }
    out[0] = out[1] = 0x55;
    out[2] = id;
    out[3] = (uint8_t)(nparams + 3);
    out[4] = cmd;
    for (uint8_t i = 0; i < nparams; ++i) {
        out[5 + i] = params[i];
    }
    out[5 + nparams] = checksum(&out[2], (uint8_t)(3 + nparams));
    return (size_t)(6 + nparams);
}

size_t bus_servo_build_move(uint8_t id, uint16_t position, uint16_t time_ms, uint8_t *out)
{
    const uint8_t p[4] = {(uint8_t)position, (uint8_t)(position >> 8), (uint8_t)time_ms, (uint8_t)(time_ms >> 8)};
    return bus_servo_build(id, BUS_CMD_MOVE_TIME_WRITE, p, 4, out);
}

void bus_servo_rx_init(bus_servo_rx_t *rx)
{
    rx->len = 0;
}

/* 한글: 응답 스트림 파서: 55 55 ID LEN CMD 파라미터 체크섬. 체크섬이 틀리면 버린다. */
int bus_servo_rx_feed(bus_servo_rx_t *rx, uint8_t byte, bus_servo_reply_t *out)
{
    if (rx->len == 0 || rx->len == 1) {
        if (byte == 0x55) {
            rx->buf[rx->len++] = byte;
        } else {
            rx->len = 0;
        }
        return 0;
    }
    if (rx->len >= sizeof(rx->buf)) {
        rx->len = 0;
        return 0;
    }
    rx->buf[rx->len++] = byte;
    if (rx->len < 4) {
        return 0;
    }
    const uint8_t total = (uint8_t)(rx->buf[3] + 3); /* LEN counts ID?? no: LEN = nparams+3 -> frame = LEN+3 */
    if (rx->buf[3] < 3 || rx->buf[3] - 3 > BUS_SERVO_MAX_PARAMS) {
        rx->len = 0;
        return 0;
    }
    if (rx->len < total) {
        return 0;
    }
    rx->len = 0;
    if (checksum(&rx->buf[2], (uint8_t)(total - 3)) != rx->buf[total - 1]) {
        return 0;
    }
    out->id = rx->buf[2];
    out->cmd = rx->buf[4];
    out->nparams = (uint8_t)(rx->buf[3] - 3);
    for (uint8_t i = 0; i < out->nparams; ++i) {
        out->params[i] = rx->buf[5 + i];
    }
    return 1;
}

/* 한글: RRC FUNC5 단일 서보 요청을 서보 명령으로 변환한다. 읽기 명령은 expects_reply=1로 응답 파라미터 길이를 지정한다. */
int bus_servo_plan_from_rrc(const uint8_t *data, uint8_t len, bus_servo_plan_t *p)
{
    if (len < 2) {
        return 0;
    }
    p->subcommand = data[0];
    p->id = data[1];
    p->nparams = 0;
    p->expects_reply = 0;
    p->reply_len = 0;

    switch (data[0]) {
    case 0x05: p->cmd = BUS_CMD_POS_READ; p->expects_reply = 1; p->reply_len = 2; return len == 2;
    case 0x07: p->cmd = BUS_CMD_VIN_READ; p->expects_reply = 1; p->reply_len = 2; return len == 2;
    case 0x09: p->cmd = BUS_CMD_TEMP_READ; p->expects_reply = 1; p->reply_len = 1; return len == 2;
    /* 한글: 0x0B=토크 해제(unload), 0x0C=토크 걸기(load). 2026-10-05 실기에서 확인(호스트 base_node 상수도 이에 맞춰 수정). */
    case 0x0B: p->cmd = BUS_CMD_LOAD_OR_UNLOAD_WRITE; p->params[0] = 0; p->nparams = 1; return len == 2; /* unload */
    case 0x0C: p->cmd = BUS_CMD_LOAD_OR_UNLOAD_WRITE; p->params[0] = 1; p->nparams = 1; return len == 2; /* load */
    /* 한글: 0x0D=토크 상태 읽기(공식 board.cpp, PDF에는 없음). 응답 [id, 0x0D, ok, state], state 1=걸림(실기에서 0x0C 후 1, 0x0B 후 0 확인) */
    case 0x0D: p->cmd = BUS_CMD_LOAD_OR_UNLOAD_READ; p->expects_reply = 1; p->reply_len = 1; return len == 2;
    case 0x10: p->cmd = BUS_CMD_ID_WRITE; p->params[0] = len > 2 ? data[2] : 0; p->nparams = 1; return len == 3;
    case 0x12: p->cmd = BUS_CMD_ID_READ; p->expects_reply = 1; p->reply_len = 1; return len == 2;
    case 0x20: p->cmd = BUS_CMD_ANGLE_OFFSET_ADJUST; p->params[0] = len > 2 ? data[2] : 0; p->nparams = 1; return len == 3;
    case 0x22: p->cmd = BUS_CMD_ANGLE_OFFSET_READ; p->expects_reply = 1; p->reply_len = 1; return len == 2;
    case 0x24: p->cmd = BUS_CMD_ANGLE_OFFSET_WRITE; return len == 2; /* save */
    case 0x30: case 0x34:
        if (len != 6) {
            return 0;
        }
        p->cmd = (data[0] == 0x30) ? BUS_CMD_ANGLE_LIMIT_WRITE : BUS_CMD_VIN_LIMIT_WRITE;
        for (int i = 0; i < 4; ++i) {
            p->params[i] = data[2 + i];
        }
        p->nparams = 4;
        return 1;
    case 0x32: p->cmd = BUS_CMD_ANGLE_LIMIT_READ; p->expects_reply = 1; p->reply_len = 4; return len == 2;
    case 0x36: p->cmd = BUS_CMD_VIN_LIMIT_READ; p->expects_reply = 1; p->reply_len = 4; return len == 2;
    case 0x38: p->cmd = BUS_CMD_TEMP_MAX_LIMIT_WRITE; p->params[0] = len > 2 ? data[2] : 0; p->nparams = 1; return len == 3;
    case 0x3A: p->cmd = BUS_CMD_TEMP_MAX_LIMIT_READ; p->expects_reply = 1; p->reply_len = 1; return len == 2;
    default: return 0;
    }
}

size_t bus_servo_make_upload(const bus_servo_plan_t *plan, int success, const uint8_t *reply, uint8_t reply_len,
                             uint8_t *data_out)
{
    size_t n = 0;
    data_out[n++] = plan->id;
    data_out[n++] = plan->subcommand;
    data_out[n++] = success ? 0x00 : 0xFF; /* int8 0 = ok, -1 = fail */
    if (success && reply) {
        for (uint8_t i = 0; i < reply_len; ++i) {
            data_out[n++] = reply[i];
        }
    } else {
        for (uint8_t i = 0; i < plan->reply_len; ++i) {
            data_out[n++] = 0;
        }
    }
    return n;
}
