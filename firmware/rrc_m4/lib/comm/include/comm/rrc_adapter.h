/* 한글: RRC 전송 어댑터: 바이트→프레임→robot_services 호출, 텔레메트리→프레임. micro-ROS와 함께 쓸 때는 fallback/debug 용도. 하드웨어/모터 로직 없음. */
/* RRC transport adapter: bytes in -> frames -> robot_services calls; telemetry out -> frames.
 * Primary use: Fallback / Debug / Factory-compat protocol next to micro-ROS. Contains no
 * hardware access and no motor logic. */
#ifndef COMM_RRC_ADAPTER_H
#define COMM_RRC_ADAPTER_H

#include <stddef.h>
#include <stdint.h>
#include "comm/robot_services.h"
#include "rrc_ext.h"
#include "rrc_funcs.h"
#include "rrc_protocol.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    const robot_services_t *svc;
    /* Writes one complete encoded frame to the link. */
    void (*tx)(void *tx_ctx, const uint8_t *frame, size_t len);
    void *tx_ctx;
    rrc_parser_t parser;
    uint32_t frames_ok;
    uint32_t frames_unknown;
} rrc_adapter_t;

void rrc_adapter_init(rrc_adapter_t *a, const robot_services_t *svc,
                      void (*tx)(void *, const uint8_t *, size_t), void *tx_ctx);
/* Feed received bytes and process every completed frame. */
void rrc_adapter_feed(rrc_adapter_t *a, const uint8_t *data, size_t len);

/* Telemetry (device -> host). */
void rrc_adapter_send_battery(rrc_adapter_t *a, uint16_t millivolts);
void rrc_adapter_send_imu(rrc_adapter_t *a, const float accel_g[3], const float gyro_dps[3]);
void rrc_adapter_send_key(rrc_adapter_t *a, uint8_t button_id, uint8_t event);
void rrc_adapter_send_gamepad(rrc_adapter_t *a, const rrc_gamepad_state_t *g);
void rrc_adapter_send_sbus(rrc_adapter_t *a, const rrc_sbus_frame_t *s);
void rrc_adapter_send_status(rrc_adapter_t *a, const rrc_ext_status_t *s);
void rrc_adapter_send_wheel(rrc_adapter_t *a, const rrc_ext_wheel_t *w);
void rrc_adapter_send_diag(rrc_adapter_t *a, const rrc_ext_diag_t *d);
void rrc_adapter_send_raw_hid(rrc_adapter_t *a, const uint8_t *report, size_t len);

#ifdef __cplusplus
}
#endif
#endif
