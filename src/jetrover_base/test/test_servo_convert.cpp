// 서보 pulse <-> rad 변환 단위시험. Servo ticks <-> radians unit tests (no ROS / hardware).
#include <gtest/gtest.h>

#include <cmath>

#include "jetrover_base/servo_convert.hpp"

using namespace jetrover_base;  // NOLINT

namespace
{
// config/base.yaml과 같은 값: 240도 / 1000틱, 중심 500 / same as config/base.yaml
const double kRpt = rad_per_tick(240.0, 1000.0);
}  // namespace

TEST(ServoConvert, RadPerTick)
{
  EXPECT_NEAR(kRpt, 240.0 * M_PI / 180.0 / 1000.0, 1e-12);
  EXPECT_NEAR(kRpt * 1000.0, 4.18879, 1e-4);  // 전체 가동 범위 = 240도
}

TEST(ServoConvert, CenterIsOffset)
{
  const ServoCal cal{500.0, 1.0, 0.25, kRpt};
  EXPECT_NEAR(ticks_to_rad(cal, 500.0), 0.25, 1e-12);
}

// base.yaml 주석의 2026-10-03 기록: joint4, center 500, 110틱 -> -1.6336 rad (부호 +1 계산값).
// Recorded in base.yaml: joint4, center 500, 110 ticks -> -1.6336 rad (sign +1). Sign -1 mirrors it.
TEST(ServoConvert, KnownReading)
{
  const ServoCal pos{500.0, 1.0, 0.0, kRpt};
  EXPECT_NEAR(ticks_to_rad(pos, 110.0), -1.6336, 1e-3);
  const ServoCal neg{500.0, -1.0, 0.0, kRpt};
  EXPECT_NEAR(ticks_to_rad(neg, 110.0), 1.6336, 1e-3);
}

TEST(ServoConvert, SignFlipsDirection)
{
  const ServoCal pos{500.0, 1.0, 0.0, kRpt};
  const ServoCal neg{500.0, -1.0, 0.0, kRpt};
  EXPECT_NEAR(ticks_to_rad(pos, 700.0), -ticks_to_rad(neg, 700.0), 1e-12);
}

TEST(ServoConvert, RoundTripAllCalibrations)
{
  const double signs[] = {1.0, -1.0};
  const double centers[] = {500.0, 480.0};
  const double offsets[] = {0.0, 0.3, -0.7};
  for (double sign : signs) {
    for (double center : centers) {
      for (double off : offsets) {
        const ServoCal cal{center, sign, off, kRpt};
        for (double ticks = 0.0; ticks <= 1000.0; ticks += 125.0) {
          EXPECT_NEAR(rad_to_ticks(cal, ticks_to_rad(cal, ticks)), ticks, 1e-9);
        }
      }
    }
  }
}

// pulse 경계: 서보 범위 양 끝(0, 1000)과 안전 한계(100~900)에서 변환이 값이 튀지 않는지.
TEST(ServoConvert, BoundariesAreFinite)
{
  const ServoCal cal{500.0, 1.0, 0.0, kRpt};
  EXPECT_NEAR(ticks_to_rad(cal, 0.0), -500.0 * kRpt, 1e-12);
  EXPECT_NEAR(ticks_to_rad(cal, 1000.0), 500.0 * kRpt, 1e-12);
  EXPECT_TRUE(std::isfinite(rad_to_ticks(cal, 10.0)));
}

TEST(ClampPulse, WithinRangeTruncatesTowardZero)
{
  EXPECT_EQ(clamp_pulse(500.9, 100, 900), 500);
  EXPECT_EQ(clamp_pulse(500.0, 100, 900), 500);
}

TEST(ClampPulse, ClampsToLimits)
{
  EXPECT_EQ(clamp_pulse(-50.0, 100, 900), 100);
  EXPECT_EQ(clamp_pulse(0.0, 100, 900), 100);
  EXPECT_EQ(clamp_pulse(1200.0, 100, 900), 900);
  EXPECT_EQ(clamp_pulse(100.0, 100, 900), 100);
  EXPECT_EQ(clamp_pulse(900.0, 100, 900), 900);
}
