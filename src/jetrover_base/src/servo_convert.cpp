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

int64_t deadband_overshoot(
  int64_t target, int64_t current, int64_t overshoot, int64_t lo,
  int64_t hi)
{
  const int64_t n = std::max<int64_t>(overshoot, 0);
  const int64_t cmd = target > current ? target + n : target < current ? target - n : target;
  return std::min<int64_t>(std::max<int64_t>(cmd, lo), hi);
}

TrimResult feedback_trim(
  int64_t target, int64_t reading, int64_t last_cmd, int64_t threshold, int64_t max_error,
  int64_t boost, int64_t lo, int64_t hi)
{
  const int64_t err = target - reading;
  const int64_t mag = err < 0 ? -err : err;
  if (mag < threshold) {
    return {TrimAction::Done, last_cmd};
  }
  if (mag > max_error) {
    return {TrimAction::GiveUp, last_cmd};
  }
  return {TrimAction::Retry,
    std::min<int64_t>(std::max<int64_t>(last_cmd + err + (err > 0 ? boost : -boost), lo), hi)};
}

int64_t relax_command(int64_t last_cmd, int64_t reading, int64_t max_error)
{
  const int64_t d = last_cmd > reading ? last_cmd - reading : reading - last_cmd;
  return (d >= 1 && d <= max_error) ? reading : -1;
}

}  // namespace jetrover_base
