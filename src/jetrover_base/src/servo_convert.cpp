#include "jetrover_base/servo_convert.hpp"

#include <algorithm>
#include <cmath>

namespace jetrover_base
{

double rad_per_tick(double range_deg, double ticks_range)
{
  return (range_deg * M_PI / 180.0) / ticks_range;
}

double ticks_to_rad(const ServoCal & cal, double ticks)
{
  return (ticks - cal.center_ticks) * cal.rad_per_tick * cal.sign + cal.offset_rad;
}

double rad_to_ticks(const ServoCal & cal, double rad)
{
  return cal.center_ticks + (rad - cal.offset_rad) / (cal.rad_per_tick * cal.sign);
}

int64_t clamp_pulse(double raw, int64_t lo, int64_t hi)
{
  return std::min<int64_t>(std::max<int64_t>(static_cast<int64_t>(raw), lo), hi);
}

}  // namespace jetrover_base
