// Copyright 2026 sang
// Licensed under the Apache License, Version 2.0
// 한글: LateralRatioCritic 비용 계산의 경계값 단위시험(ROS 없음).
#include <gtest/gtest.h>

#include <cmath>

#include "jetrover_nav_plugins/lateral_ratio.hpp"

using jetrover_nav_plugins::lateralRatioCost;

namespace
{
const float kRatio45 = 1.0f;  // tan(45 deg)

xt::xtensor<float, 2> row(std::initializer_list<float> v)
{
  xt::xtensor<float, 2> out = xt::zeros<float>({std::size_t{1}, v.size()});
  std::size_t i = 0;
  for (float x : v) {
    out(0, i++) = x;
  }
  return out;
}
}  // namespace

TEST(LateralRatio, WithinFortyFiveDegreesIsFree)
{
  // vx = 0.12, vy = 0.12 (exactly 45 deg) and smaller lateral: no cost
  auto c = lateralRatioCost(row({0.12f, 0.12f, 0.10f}), row({0.12f, -0.12f, 0.05f}), kRatio45, 0.0f,
    0.1f);
  EXPECT_FLOAT_EQ(c(0), 0.0f);
}

TEST(LateralRatio, ExcessIsLinearAndScaledByDt)
{
  // vx 0.05, vy 0.12 -> excess 0.07 per step, two steps, dt 0.1 -> 0.014
  auto c = lateralRatioCost(row({0.05f, 0.05f}), row({0.12f, -0.12f}), kRatio45, 0.0f, 0.1f);
  EXPECT_NEAR(c(0), 0.014f, 1e-6f);
}

TEST(LateralRatio, SlackAllowsSmallLateralAtStandstill)
{
  // vx 0, vy 0.02 with slack 0.02 -> free; vy 0.05 -> 0.03 excess
  auto c = lateralRatioCost(row({0.0f, 0.0f}), row({0.02f, 0.05f}), kRatio45, 0.02f, 1.0f);
  EXPECT_NEAR(c(0), 0.03f, 1e-6f);
}

TEST(LateralRatio, ReverseCountsAsNoForwardSpeed)
{
  // vx -0.1 must not "buy" lateral allowance: excess = |vy| = 0.05
  auto c = lateralRatioCost(row({-0.1f}), row({0.05f}), kRatio45, 0.0f, 1.0f);
  EXPECT_NEAR(c(0), 0.05f, 1e-6f);
}

TEST(LateralRatio, PureStrafeIsPenalizedMostAndBatchesAreIndependent)
{
  xt::xtensor<float, 2> vx = {{0.12f}, {0.0f}};
  xt::xtensor<float, 2> vy = {{0.06f}, {0.12f}};
  auto c = lateralRatioCost(vx, vy, kRatio45, 0.0f, 1.0f);
  ASSERT_EQ(c.size(), 2u);
  EXPECT_FLOAT_EQ(c(0), 0.0f);          // 27 deg diagonal: free
  EXPECT_NEAR(c(1), 0.12f, 1e-6f);      // pure strafe: full lateral speed
}

TEST(LateralRatio, ThirtyDegreeLimit)
{
  const float k30 = std::tan(30.0f * static_cast<float>(M_PI) / 180.0f);  // 0.577
  auto c = lateralRatioCost(row({0.12f}), row({0.10f}), k30, 0.0f, 1.0f);
  EXPECT_NEAR(c(0), 0.10f - k30 * 0.12f, 1e-6f);
}
