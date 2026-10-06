// 명령 검증/파라미터 fail-fast 단위시험. Command guard and parameter validation unit tests.
#include <gtest/gtest.h>

#include <algorithm>
#include <cmath>
#include <limits>

#include "jetrover_base/command_guard.hpp"

using namespace jetrover_base;  // NOLINT

namespace
{
const double kNan = std::numeric_limits<double>::quiet_NaN();
const double kInf = std::numeric_limits<double>::infinity();
}  // namespace

TEST(DecideCmdVel, NormalIsAccepted)
{
  EXPECT_EQ(decide_cmd_vel(0.1, 0.0, 0.2, false), CmdDecision::Accept);
}

TEST(DecideCmdVel, NonFiniteIsRejectedInAnyField)
{
  EXPECT_EQ(decide_cmd_vel(kNan, 0, 0, false), CmdDecision::RejectNonFinite);
  EXPECT_EQ(decide_cmd_vel(0, kNan, 0, false), CmdDecision::RejectNonFinite);
  EXPECT_EQ(decide_cmd_vel(0, 0, kNan, false), CmdDecision::RejectNonFinite);
  EXPECT_EQ(decide_cmd_vel(kInf, 0, 0, false), CmdDecision::RejectNonFinite);
  EXPECT_EQ(decide_cmd_vel(0, -kInf, 0, false), CmdDecision::RejectNonFinite);
  // 유한한 값이 섞여 있어도 하나라도 NaN이면 거부
  EXPECT_EQ(decide_cmd_vel(0.1, 0.1, kNan, false), CmdDecision::RejectNonFinite);
}

// std::clamp(NaN, lo, hi)는 NaN을 그대로 돌려준다 -> 반드시 clamp 전에 거부해야 하는 이유.
TEST(DecideCmdVel, WhyNanMustBeRejectedBeforeClamp)
{
  EXPECT_TRUE(std::isnan(std::clamp(kNan, -0.2, 0.2)));
}

TEST(DecideCmdVel, NonZeroRejectedWhileStm32Silent)
{
  EXPECT_EQ(decide_cmd_vel(0.1, 0, 0, true), CmdDecision::RejectStm32Silent);
  EXPECT_EQ(decide_cmd_vel(0, 0.05, 0, true), CmdDecision::RejectStm32Silent);
  EXPECT_EQ(decide_cmd_vel(0, 0, -0.3, true), CmdDecision::RejectStm32Silent);
}

TEST(DecideCmdVel, ZeroAlwaysAcceptedEvenWhileSilent)
{
  EXPECT_EQ(decide_cmd_vel(0, 0, 0, true), CmdDecision::Accept);
  EXPECT_EQ(decide_cmd_vel(-0.0, 0, 0, true), CmdDecision::Accept);
}

TEST(DecideCmdVel, NonFiniteWinsOverSilent)
{
  EXPECT_EQ(decide_cmd_vel(kNan, 0, 0, true), CmdDecision::RejectNonFinite);
}

TEST(AllFinite, Basics)
{
  EXPECT_TRUE(all_finite({}));
  EXPECT_TRUE(all_finite({0.0, -1.5, 3.0}));
  EXPECT_FALSE(all_finite({0.0, kNan}));
  EXPECT_FALSE(all_finite({kInf}));
}

TEST(ValidateBaseParams, DefaultsAreValid)
{
  EXPECT_EQ(validate_base_params(0.216, 0.195, 0.097, 0.2, 1.0, 0.5, 1.0), "");
}

TEST(ValidateBaseParams, EachBadValueIsReported)
{
  EXPECT_NE(validate_base_params(0.0, 0.195, 0.097, 0.2, 1.0, 0.5, 1.0), "");
  EXPECT_NE(validate_base_params(0.216, -0.1, 0.097, 0.2, 1.0, 0.5, 1.0), "");
  EXPECT_NE(validate_base_params(0.216, 0.195, 0.0, 0.2, 1.0, 0.5, 1.0), "");   // wheel_diameter 0
  EXPECT_NE(validate_base_params(0.216, 0.195, 0.097, 0.0, 1.0, 0.5, 1.0), "");
  EXPECT_NE(validate_base_params(0.216, 0.195, 0.097, 0.2, 0.0, 0.5, 1.0), "");
  EXPECT_NE(validate_base_params(0.216, 0.195, 0.097, 0.2, 1.0, -0.5, 1.0), "");  // 음수 timeout
  EXPECT_NE(validate_base_params(0.216, 0.195, 0.097, 0.2, 1.0, 0.5, 0.0), "");
  EXPECT_NE(validate_base_params(kNan, 0.195, 0.097, 0.2, 1.0, 0.5, 1.0), "");
}

namespace
{
ArmParams good_arm()
{
  ArmParams p;
  p.center_ticks = {500, 500, 500, 500, 500, 500};
  p.signs = {1, 1, -1, 1, 1, 1};
  p.offsets_rad = {0, 0, 0, 0, 0, 0};
  p.home_pose_rad = {0.0, -0.553, 1.688, 1.671, 0.017, 0.0};
  return p;
}
}  // namespace

TEST(ValidateArmParams, DefaultsAreValid)
{
  EXPECT_EQ(validate_arm_params(good_arm()), "");
}

TEST(ValidateArmParams, BadValuesAreReported)
{
  auto p = good_arm();
  p.servo_ticks_range = 0;
  EXPECT_NE(validate_arm_params(p), "");

  p = good_arm();
  p.servo_range_deg = -240;
  EXPECT_NE(validate_arm_params(p), "");

  p = good_arm();
  p.signs[2] = 0.0;  // sign 0 -> 0으로 나누기
  EXPECT_NE(validate_arm_params(p), "");

  p = good_arm();
  p.signs[0] = 2.0;
  EXPECT_NE(validate_arm_params(p), "");

  p = good_arm();
  p.pulse_min = 900;
  p.pulse_max = 100;  // min > max
  EXPECT_NE(validate_arm_params(p), "");

  p = good_arm();
  p.pulse_min = p.pulse_max = 500;  // min == max
  EXPECT_NE(validate_arm_params(p), "");

  p = good_arm();
  p.pulse_min = -1;
  EXPECT_NE(validate_arm_params(p), "");

  p = good_arm();
  p.pulse_max = 1001;  // 서보 ticks 범위 초과
  EXPECT_NE(validate_arm_params(p), "");

  p = good_arm();
  p.home_pose_rad[1] = kNan;
  EXPECT_NE(validate_arm_params(p), "");

  p = good_arm();
  p.center_ticks[0] = kInf;
  EXPECT_NE(validate_arm_params(p), "");

  p = good_arm();
  p.max_step_rad = 0.0;
  EXPECT_NE(validate_arm_params(p), "");

  p = good_arm();
  p.move_duration_s = -1.0;
  EXPECT_NE(validate_arm_params(p), "");
}
