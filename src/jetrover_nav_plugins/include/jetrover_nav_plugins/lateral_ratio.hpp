// Copyright 2026 sang
// Licensed under the Apache License, Version 2.0
//
// Pure cost math of LateralRatioCritic (no ROS), unit-tested in test/test_lateral_ratio.cpp.
// 한글: LateralRatioCritic의 비용 계산(ROS 없음). 단위시험 대상.
#ifndef JETROVER_NAV_PLUGINS__LATERAL_RATIO_HPP_
#define JETROVER_NAV_PLUGINS__LATERAL_RATIO_HPP_

#include <xtensor/xmath.hpp>
#include <xtensor/xreducer.hpp>
#include <xtensor/xtensor.hpp>

namespace jetrover_nav_plugins
{

// Per-trajectory cost of exceeding the diagonal limit: sum over time of
//   max(0, |vy| - k * max(vx, 0) - slack) * dt
// vx, vy: [batch, time_steps]. k = tan(max_angle). Reverse (vx < 0) counts as no forward speed.
// 한글: 궤적별로 |vy|가 k*vx(+여유)를 넘는 양을 시간에 걸쳐 합한다. 후진(vx<0)은 전진 0으로 본다.
inline xt::xtensor<float, 1> lateralRatioCost(
  const xt::xtensor<float, 2> & vx, const xt::xtensor<float, 2> & vy,
  float k, float slack, float dt)
{
  auto forward = xt::maximum(vx, 0.0f);
  auto excess = xt::maximum(xt::fabs(vy) - k * forward - slack, 0.0f);
  return xt::sum(excess, {1}, xt::evaluation_strategy::immediate) * dt;
}

}  // namespace jetrover_nav_plugins

#endif  // JETROVER_NAV_PLUGINS__LATERAL_RATIO_HPP_
