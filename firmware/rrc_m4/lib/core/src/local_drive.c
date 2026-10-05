/* 한글: 한 글자 명령→속도 변환 구현(A 전진, E 후진, C/G 제자리 회전, n/l 좌/우 평행이동, I 정지, S/j 속도 증감). */
#include "core/local_drive.h"

void local_drive_init(local_drive_t *ld, robot_ctrl_t *robot)
{
    ld->robot = robot;
    ld->speed_mps = 0.10f;
    ld->step_mps = 0.05f;
    ld->min_mps = 0.05f;
    ld->max_mps = 0.30f;
    ld->wz_rad_s = 1.0f;
}

int local_drive_char(local_drive_t *ld, char c, uint32_t now_ms, robot_cmd_source_t src)
{
    const float v = ld->speed_mps, w = ld->wz_rad_s;
    float vx = 0, vy = 0, wz = 0;

    switch (c) {
    case 'A': vx = v; break;
    case 'E': vx = -v; break;
    case 'C': wz = w; break;
    case 'G': wz = -w; break;
    case 'B': vx = v; wz = w * 0.5f; break;
    case 'H': vx = v; wz = -w * 0.5f; break;
    case 'D': vx = -v; wz = -w * 0.5f; break;
    case 'F': vx = -v; wz = w * 0.5f; break;
    case 'n': vy = v; break;
    case 'l': vy = -v; break;
    case 'I': robot_stop(ld->robot, ROBOT_STOP_COMMAND); return 1;
    case 'S':
        ld->speed_mps = ld->speed_mps + ld->step_mps > ld->max_mps ? ld->max_mps : ld->speed_mps + ld->step_mps;
        return 1;
    case 'j':
        ld->speed_mps = ld->speed_mps - ld->step_mps < ld->min_mps ? ld->min_mps : ld->speed_mps - ld->step_mps;
        return 1;
    default: return 0;
    }
    robot_set_velocity(ld->robot, vx, vy, wz, now_ms, src);
    return 1;
}

char local_drive_atc(int x, int y, int th)
{
    if (x < -th) return y < -th ? 'D' : (y > th ? 'B' : 'C');
    if (x > th) return y < -th ? 'F' : (y > th ? 'H' : 'G');
    return y < -th ? 'E' : (y > th ? 'A' : 'I');
}

char local_drive_hat_char(uint8_t hat)
{
    return (hat & 0x08) ? (char)((((hat & 0x07) + 1) & 0x07) + 0x41) : 'I';
}
