/* 한글: 메카넘 기구학. 바퀴 순서/부호는 jetrover_base(base_node.cpp)와 동일: 0,1=왼쪽 앞/뒤, 2,3=오른쪽 앞/뒤(오른쪽은 부호 반전). 단위는 바퀴 rev/s. */
/* Mecanum kinematics, wheel order/signs identical to jetrover_base (src/base_node.cpp
 * mecanum_rps) and Hiwonder's mecanum.py: motors 0,1 = left front/rear, 2,3 = right
 * front/rear, right side negated (mounted mirrored). Output unit is wheel rev/s. */
#ifndef CORE_MECANUM_H
#define CORE_MECANUM_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    float wheelbase;      /* m, front-rear axle distance */
    float track_width;    /* m, left-right wheel distance */
    float wheel_diameter; /* m */
} mecanum_cfg_t;

/* vx, vy in m/s (x forward, y left), wz in rad/s -> rps[4] */
void mecanum_inverse(const mecanum_cfg_t *cfg, float vx, float vy, float wz, float rps[4]);
/* Measured wheel rps[4] -> body twist (used for /wheel_states based odometry). */
void mecanum_forward(const mecanum_cfg_t *cfg, const float rps[4], float *vx, float *vy, float *wz);

#ifdef __cplusplus
}
#endif
#endif
