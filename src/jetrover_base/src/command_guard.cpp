#include "jetrover_base/command_guard.hpp"

#include <cmath>

namespace jetrover_base
{

CmdDecision decide_cmd_vel(double vx, double vy, double wz, bool stm32_silent)
{
  if (!std::isfinite(vx) || !std::isfinite(vy) || !std::isfinite(wz)) {
    return CmdDecision::RejectNonFinite;
  }
  const bool nonzero = (vx != 0.0 || vy != 0.0 || wz != 0.0);
  if (nonzero && stm32_silent) {
    return CmdDecision::RejectStm32Silent;
  }
  return CmdDecision::Accept;
}

bool all_finite(const std::vector<double> & values)
{
  for (double v : values) {
    if (!std::isfinite(v)) {
      return false;
    }
  }
  return true;
}

namespace
{
bool positive(double v) {return std::isfinite(v) && v > 0.0;}
}  // namespace

std::string validate_base_params(
  double wheelbase, double track_width, double wheel_diameter, double max_linear,
  double max_angular, double cmd_vel_timeout, double stm32_timeout)
{
  if (!positive(wheelbase)) {return "wheelbase must be > 0";}
  if (!positive(track_width)) {return "track_width must be > 0";}
  if (!positive(wheel_diameter)) {return "wheel_diameter must be > 0";}
  if (!positive(max_linear)) {return "max_linear must be > 0";}
  if (!positive(max_angular)) {return "max_angular must be > 0";}
  if (!positive(cmd_vel_timeout)) {return "cmd_vel_timeout must be > 0";}
  if (!positive(stm32_timeout)) {return "stm32_timeout must be > 0";}
  return "";
}

std::string validate_arm_params(const ArmParams & p)
{
  if (!positive(p.servo_range_deg)) {return "arm_servo_range_deg must be > 0";}
  if (!positive(p.servo_ticks_range)) {return "arm_servo_ticks_range must be > 0";}
  if (!all_finite(p.center_ticks)) {return "arm_center_ticks must be finite";}
  if (!all_finite(p.offsets_rad)) {return "arm_joint_offsets_rad must be finite";}
  if (!all_finite(p.home_pose_rad)) {return "arm_home_pose_rad must be finite";}
  for (double s : p.signs) {
    if (s != 1.0 && s != -1.0) {return "arm_joint_signs entries must be +1 or -1";}
  }
  if (!positive(p.max_step_rad)) {return "arm_max_step_rad must be > 0";}
  if (!std::isfinite(p.move_duration_s) || p.move_duration_s < 0.0) {
    return "arm_move_duration_s must be >= 0";
  }
  if (p.pulse_min < 0) {return "arm_pulse_min must be >= 0";}
  if (p.pulse_min >= p.pulse_max) {return "arm_pulse_min must be < arm_pulse_max";}
  if (static_cast<double>(p.pulse_max) > p.servo_ticks_range) {
    return "arm_pulse_max must be <= arm_servo_ticks_range";
  }
  return "";
}

}  // namespace jetrover_base
