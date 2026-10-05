/* 한글: 메카넘 역/정기구학 구현(base_node.cpp와 동일 수식, 테스트로 동치 확인). */
#include "core/mecanum.h"

#define MECANUM_PI 3.14159265358979f

void mecanum_inverse(const mecanum_cfg_t *cfg, float vx, float vy, float wz, float rps[4])
{
    const float k = wz * (cfg->wheelbase + cfg->track_width) / 2.0f;
    const float to_rps = 1.0f / (MECANUM_PI * cfg->wheel_diameter);

    rps[0] = (vx - vy - k) * to_rps;
    rps[1] = (vx + vy - k) * to_rps;
    rps[2] = -(vx + vy + k) * to_rps;
    rps[3] = -(vx - vy + k) * to_rps;
}

void mecanum_forward(const mecanum_cfg_t *cfg, const float rps[4], float *vx, float *vy, float *wz)
{
    const float wheel_circ = MECANUM_PI * cfg->wheel_diameter; /* m per rev */
    const float q = wheel_circ / 4.0f;
    const float k = -(rps[0] + rps[1] + rps[2] + rps[3]) * q;

    *vx = (rps[0] + rps[1] - rps[2] - rps[3]) * q;
    *vy = (rps[1] - rps[0] + rps[3] - rps[2]) * q;
    *wz = 2.0f * k / (cfg->wheelbase + cfg->track_width);
}
