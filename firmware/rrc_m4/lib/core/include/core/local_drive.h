/* 한글: 벤더의 한 글자 제어 프로토콜(블루투스 앱/게임패드/SBUS)로 MCU가 직접 주행하는 기능. LOCAL_DRIVE_ENABLE일 때만 사용(기본은 호스트가 주행). */
/* MCU-side driving from the vendor's single-character control protocol (Bluetooth app, USB gamepad,
 * SBUS). Compiled in always, used only when LOCAL_DRIVE_ENABLE is set (the host normally owns motion).
 * Characters (program analysis 3.17 appendix): A fwd, E back, C spin left, G spin right, B/H forward
 * arcs left/right, D/F backward arcs, n/l lateral left/right (mecanum), I stop, S/j speed +/-. */
#ifndef CORE_LOCAL_DRIVE_H
#define CORE_LOCAL_DRIVE_H

#include <stdint.h>
#include "core/robot_ctrl.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    robot_ctrl_t *robot;
    float speed_mps, step_mps, min_mps, max_mps, wz_rad_s;
} local_drive_t;

void local_drive_init(local_drive_t *ld, robot_ctrl_t *robot);
/* Returns 1 if the character was a motion/speed command. */
int local_drive_char(local_drive_t *ld, char c, uint32_t now_ms, robot_cmd_source_t src);
/* Vendor A_T_C: stick (x, y) -> direction char 'A'..'H' or 'I' (centre). */
char local_drive_atc(int x, int y, int threshold);
/* Gamepad hat (vendor encoding, bit3 = pressed) -> direction char, 'I' if released. */
char local_drive_hat_char(uint8_t hat);

#ifdef __cplusplus
}
#endif
#endif
