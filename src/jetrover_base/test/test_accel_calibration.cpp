#include <gtest/gtest.h>
#include <limits>
#include "jetrover_base/accel_calibration.hpp"

TEST(AccelCalibration, DefaultsPreserveAndAppliesOffsetBeforeScale)
{
  using namespace jetrover_base;
  EXPECT_TRUE(valid_accel_calibration({0, 0, 0}, {1, 1, 1}));
  const auto result = calibrate_accel({2, -3, 9}, {1, -1, 1}, {2, 0.5, 1});
  EXPECT_DOUBLE_EQ(result[0], 2);
  EXPECT_DOUBLE_EQ(result[1], -1);
  EXPECT_DOUBLE_EQ(result[2], 8);
}

TEST(AccelCalibration, RejectsInvalidShapeNanAndBounds)
{
  using namespace jetrover_base;
  EXPECT_FALSE(valid_accel_calibration({0}, {1, 1, 1}));
  EXPECT_FALSE(valid_accel_calibration({0, 0, 0}, {1, 0, 1}));
  EXPECT_FALSE(valid_accel_calibration({0, 0, std::numeric_limits<double>::quiet_NaN()}, {1, 1, 1}));
}
