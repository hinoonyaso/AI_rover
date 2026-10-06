#include "jetrover_base/mecanum.hpp"

#include <cmath>

namespace jetrover_base
{

std::vector<MotorCommand> mecanum_inverse(
  double vx, double vy, double wz, double wheelbase, double track_width, double wheel_diameter)
{
  const double k = wz * (wheelbase + track_width) / 2.0;
  const double to_rps = 1.0 / (M_PI * wheel_diameter);

  return {
    {1, static_cast<float>((vx - vy - k) * to_rps)},
    {2, static_cast<float>((vx + vy - k) * to_rps)},
    {3, static_cast<float>(-(vx + vy + k) * to_rps)},
    {4, static_cast<float>(-(vx - vy + k) * to_rps)},
  };
}

BodyTwist mecanum_forward(
  const double rps[4], double wheelbase, double track_width, double wheel_diameter)
{
  const double to_v = M_PI * wheel_diameter;
  // 한글: 오른쪽 바퀴 부호를 되돌려 선속도로 바꾼 뒤 역기구학 식을 푼다.
  const double fl = rps[0] * to_v;
  const double rl = rps[1] * to_v;
  const double fr = -rps[2] * to_v;
  const double rr = -rps[3] * to_v;

  BodyTwist t;
  t.vx = (fl + rl + fr + rr) / 4.0;
  t.vy = (-fl + rl + fr - rr) / 4.0;
  t.wz = (-fl - rl + fr + rr) / (2.0 * (wheelbase + track_width));
  return t;
}

}  // namespace jetrover_base
