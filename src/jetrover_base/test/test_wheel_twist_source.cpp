// wheel_twist 출처 선택 단위시험. Unit tests for the wheel_twist source selection (no ROS / hardware).
#include <gtest/gtest.h>

#include <cmath>

#include "jetrover_base/wheel_twist_source.hpp"

using namespace jetrover_base;  // NOLINT

namespace
{
constexpr double kWheelbase = 0.216;
constexpr double kTrack = 0.195;
constexpr double kDiameter = 0.097;

// Measured wheel speeds for a given body twist = inverse kinematics (what rrc_m4 reports when the
// PID tracks perfectly). 한글: PID가 완벽히 따라갈 때 펌웨어가 보고하는 바퀴 속도 = 역기구학 결과.
void wheels_for(double vx, double vy, double wz, double out[4])
{
  const auto cmds = mecanum_inverse(vx, vy, wz, kWheelbase, kTrack, kDiameter);
  for (int i = 0; i < 4; ++i) {
    out[i] = cmds[i].rps;
  }
}
}  // namespace

TEST(TwistSource, ParseNames)
{
  TwistSource s;
  ASSERT_TRUE(parse_twist_source("command", s));
  EXPECT_EQ(s, TwistSource::Command);
  ASSERT_TRUE(parse_twist_source("encoder", s));
  EXPECT_EQ(s, TwistSource::Encoder);
  ASSERT_TRUE(parse_twist_source("auto", s));
  EXPECT_EQ(s, TwistSource::Auto);
  EXPECT_FALSE(parse_twist_source("Encoder", s));
  EXPECT_FALSE(parse_twist_source("", s));
  EXPECT_STREQ(twist_source_name(TwistSource::Auto), "auto");
}

TEST(TwistSource, CommandIgnoresFeedback)
{
  const BodyTwist cmd{0.1, 0.0, 0.0};
  double wheels[4];
  wheels_for(0.0, 0.05, 0.3, wheels);
  const auto c = choose_wheel_twist(TwistSource::Command, cmd, true, wheels, kWheelbase, kTrack,
      kDiameter);
  EXPECT_FALSE(c.from_encoder);
  EXPECT_DOUBLE_EQ(c.twist.vx, 0.1);
  EXPECT_DOUBLE_EQ(c.twist.wz, 0.0);
}

TEST(TwistSource, EncoderUsesMeasuredWheels)
{
  // command says straight, wheels say strafe + turn (slip / not following): measured wins
  const BodyTwist cmd{0.1, 0.0, 0.0};
  double wheels[4];
  wheels_for(0.0, 0.05, 0.3, wheels);
  for (const auto src : {TwistSource::Encoder, TwistSource::Auto}) {
    const auto c = choose_wheel_twist(src, cmd, true, wheels, kWheelbase, kTrack, kDiameter);
    EXPECT_TRUE(c.from_encoder);
    EXPECT_NEAR(c.twist.vx, 0.0, 1e-6);
    EXPECT_NEAR(c.twist.vy, 0.05, 1e-6);
    EXPECT_NEAR(c.twist.wz, 0.3, 1e-6);
  }
}

TEST(TwistSource, StaleFeedback)
{
  const BodyTwist cmd{0.1, 0.02, 0.2};
  double wheels[4];
  wheels_for(0.5, 0.5, 0.5, wheels);  // must be ignored when stale
  const auto enc = choose_wheel_twist(TwistSource::Encoder, cmd, false, wheels, kWheelbase, kTrack,
      kDiameter);
  EXPECT_FALSE(enc.from_encoder);
  EXPECT_TRUE(enc.feedback_stale);
  EXPECT_DOUBLE_EQ(enc.twist.vx, 0.0);  // never a guess in encoder mode
  EXPECT_DOUBLE_EQ(enc.twist.wz, 0.0);
  const auto aut = choose_wheel_twist(TwistSource::Auto, cmd, false, wheels, kWheelbase, kTrack,
      kDiameter);
  EXPECT_FALSE(aut.from_encoder);
  EXPECT_FALSE(aut.feedback_stale);
  EXPECT_DOUBLE_EQ(aut.twist.vx, 0.1);  // vendor firmware: falls back to the command
  EXPECT_DOUBLE_EQ(aut.twist.vy, 0.02);
}
