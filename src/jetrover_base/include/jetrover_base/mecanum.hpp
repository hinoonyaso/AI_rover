// 한글: 메카넘 기구학(순수 함수, ROS/하드웨어 불필요). base_node에서 분리해 단위시험이 가능하게 했다.
// Mecanum kinematics as pure functions so they can be unit-tested without ROS or hardware.
#pragma once

#include <vector>

#include "jetrover_base/rrc_protocol.hpp"

namespace jetrover_base
{

// Body twist [m/s, m/s, rad/s] (x forward, y left, z up).
struct BodyTwist
{
  double vx{0}, vy{0}, wz{0};
};

// Mecanum inverse kinematics (same wheel order/signs as Hiwonder's mecanum.py):
// motors 1,2 = left front/rear, 3,4 = right front/rear; the right side is mounted
// mirrored, so its command is negated. Output is wheel rev/s (board port ids 1..4).
// 한글: 역기구학. 1,2번=왼쪽 앞/뒤, 3,4번=오른쪽 앞/뒤(오른쪽은 부호 반전). 출력은 바퀴 rev/s.
// firmware/rrc_m4/lib/core/mecanum.c와 동일 수식.
std::vector<MotorCommand> mecanum_inverse(
  double vx, double vy, double wz, double wheelbase, double track_width, double wheel_diameter);

// Forward kinematics: wheel rev/s of ports 1..4 (same sign convention as the
// inverse output) -> body twist. Needed for encoder-based wheel odometry.
// 한글: 정기구학(엔코더 odom용 예정). 입력은 역기구학 출력과 같은 부호 규약의 rev/s.
BodyTwist mecanum_forward(
  const double rps[4], double wheelbase, double track_width, double wheel_diameter);

}  // namespace jetrover_base
