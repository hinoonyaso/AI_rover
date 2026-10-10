#include "jetrover_base/wheel_twist_source.hpp"

namespace jetrover_base
{

bool parse_twist_source(const std::string & name, TwistSource & out)
{
  if (name == "command") {
    out = TwistSource::Command;
  } else if (name == "encoder") {
    out = TwistSource::Encoder;
  } else if (name == "auto") {
    out = TwistSource::Auto;
  } else {
    return false;
  }
  return true;
}

const char * twist_source_name(TwistSource source)
{
  switch (source) {
    case TwistSource::Encoder:
      return "encoder";
    case TwistSource::Auto:
      return "auto";
    case TwistSource::Command:
    default:
      return "command";
  }
}

TwistChoice choose_wheel_twist(
  TwistSource source, const BodyTwist & commanded, bool feedback_fresh, const double wheel_rps[4],
  double wheelbase, double track_width, double wheel_diameter)
{
  TwistChoice c;
  const bool want_encoder = source == TwistSource::Encoder || source == TwistSource::Auto;
  if (want_encoder && feedback_fresh) {
    c.twist = mecanum_forward(wheel_rps, wheelbase, track_width, wheel_diameter);
    c.from_encoder = true;
  } else if (source == TwistSource::Encoder) {
    c.feedback_stale = true;  // twist stays zero / 측정이 끊기면 추정하지 않고 0
  } else {
    c.twist = commanded;
  }
  return c;
}

}  // namespace jetrover_base
