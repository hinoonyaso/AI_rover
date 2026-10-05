// 한글: RRC 프레임 코덱 구현(순수 C, 동적 할당 없음). 호스트/펌웨어 모두에서 쓴다.
#include "rrc_protocol.h"

#include <string.h>

// 한글: CRC-8/MAXIM(반사 다항식 0x8C, 초기값 0). 호스트(rrc_protocol.cpp)와 동일.
uint8_t rrc_crc8_maxim(const uint8_t *data, size_t len) {
    uint8_t crc = 0x00u;
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (int bit = 0; bit < 8; bit++) {
            crc = (crc & 1u) ? (uint8_t)((crc >> 1) ^ 0x8Cu) : (uint8_t)(crc >> 1);
        }
    }
    return crc;
}

// 한글: AA 55 FUNC LEN DATA CRC 프레임을 만든다. CRC는 FUNC+LEN+DATA만 계산. DATA가 255바이트를 넘으면 0을 반환.
size_t rrc_encode(uint8_t func, const uint8_t *data, size_t data_len, uint8_t *out) {
    if (data_len > RRC_MAX_DATA_LEN) {
        return 0;
    }
    out[0] = RRC_HEADER_0;
    out[1] = RRC_HEADER_1;
    out[2] = func;
    out[3] = (uint8_t)data_len;
    if (data_len > 0) {
        memcpy(&out[4], data, data_len);
    }
    uint8_t crc = rrc_crc8_maxim(&out[2], 2 + data_len);
    out[4 + data_len] = crc;
    return 4 + data_len + 1;
}

// 한글: 파서 버퍼 초기화.
void rrc_parser_init(rrc_parser_t *p) {
    p->len = 0;
}

// 한글: 입력 바이트를 내부 버퍼에 쌓는다. 버퍼가 차면 일부만 소비하므로 호출자가 소비량을 확인한다.
size_t rrc_parser_feed(rrc_parser_t *p, const uint8_t *in, size_t in_len) {
    size_t space = sizeof(p->buf) - p->len;
    size_t n = (in_len > space) ? space : in_len;
    memcpy(&p->buf[p->len], in, n);
    p->len += n;
    return n;
}

static void parser_drop_front(rrc_parser_t *p, size_t n) {
    if (n >= p->len) {
        p->len = 0;
        return;
    }
    memmove(p->buf, p->buf + n, p->len - n);
    p->len -= n;
}

// 한글: 완성되고 CRC가 맞는 프레임 하나를 꺼낸다. 깨진 프레임은 AA 한 바이트만 버리고 재동기화한다(호스트 파서와 동일).
int rrc_parser_next(rrc_parser_t *p, rrc_frame_t *out) {
    for (;;) {
        // 한글: 헤더 AA 55 탐색. 끝에 AA 단독이 남으면 다음 입력의 55를 기다리며 보존한다.
        /* find header */
        size_t idx = (size_t)-1;
        for (size_t i = 0; i + 1 < p->len; i++) {
            if (p->buf[i] == RRC_HEADER_0 && p->buf[i + 1] == RRC_HEADER_1) {
                idx = i;
                break;
            }
        }
        if (idx == (size_t)-1) {
            /* keep a trailing lone 0xAA in case the 0x55 arrives next feed */
            if (p->len > 0 && p->buf[p->len - 1] == RRC_HEADER_0) {
                p->buf[0] = RRC_HEADER_0;
                p->len = 1;
            } else {
                p->len = 0;
            }
            return 0;
        }
        if (idx > 0) {
            parser_drop_front(p, idx);
        }
        if (p->len < 4) {
            return 0; /* need FUNC+LEN */
        }
        uint8_t func = p->buf[2];
        uint8_t data_len = p->buf[3];
        size_t total = 4u + (size_t)data_len + 1u;
        if (p->len < total) {
            return 0; /* wait for more data */
        }
        uint8_t crc = rrc_crc8_maxim(&p->buf[2], 2 + data_len);
        if (crc != p->buf[4 + data_len]) {
            /* bad frame: drop just the leading 0xAA and resync, like the host parser */
            parser_drop_front(p, 1);
            continue;
        }
        out->func = func;
        out->data_len = data_len;
        memcpy(out->data, &p->buf[4], data_len);
        parser_drop_front(p, total);
        return 1;
    }
}
