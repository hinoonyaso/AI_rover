// 한글: wheel_twist(EKF 입력)를 명령값으로 만들지, 엔코더 측정값으로 만들지 고르는 순수 함수(단위시험 대상).
// Chooses where wheel_twist (the EKF input) comes from: the commanded body velocity (open loop,
// vendor firmware) or the wheel speeds measured by the rrc_m4 firmware (FUNC 0x21). Pure, unit-tested.
// prd/encoder-odometry.md, decided 2026-10-10: host path = base_node reads FUNC 0x21 (RRC).
#pragma once

#include <string>

#include "jetrover_base/mecanum.hpp"

namespace jetrover_base
{

// command: always the commanded velocity (default, previous behaviour)
// encoder: always measured; stale feedback -> zero twist (never fall back to a guess)
// auto:    measured when fresh, otherwise the command (works with both firmwares)
// 한글: command=기존 동작(기본), encoder=측정값만(끊기면 0), auto=측정값 있으면 측정, 없으면 명령.
enum class TwistSource { Command, Encoder, Auto };

bool parse_twist_source(const std::string & name, TwistSource & out);
const char * twist_source_name(TwistSource source);

struct TwistChoice
{
  BodyTwist twist;
  bool from_encoder{false};
  bool feedback_stale{false};  // encoder mode without fresh feedback
};

// `commanded` must already be scaled/zeroed by the caller as before (open-loop path).
// `wheel_rps` (ports 1..4, MotorCommand sign convention) is used only when `feedback_fresh`.
TwistChoice choose_wheel_twist(
  TwistSource source, const BodyTwist & commanded, bool feedback_fresh, const double wheel_rps[4],
  double wheelbase, double track_width, double wheel_diameter);

}  // namespace jetrover_base
