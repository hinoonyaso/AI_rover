// Copyright 2026 sang
// Licensed under the Apache License, Version 2.0
#include "jetrover_nav_plugins/lateral_ratio_critic.hpp"

#include <cmath>

#include "jetrover_nav_plugins/lateral_ratio.hpp"
#include "nav2_mppi_controller/tools/utils.hpp"

namespace mppi::critics
{

void LateralRatioCritic::initialize()
{
  auto getParam = parameters_handler_->getParamGetter(name_);
  double max_angle_deg = 45.0;
  getParam(power_, "cost_power", 1);
  getParam(weight_, "cost_weight", 50.0f);
  getParam(max_angle_deg, "max_angle_deg", 45.0);
  getParam(slack_, "slack", 0.02f);
  ratio_ = static_cast<float>(std::tan(max_angle_deg * M_PI / 180.0));
  RCLCPP_INFO(
    logger_,
      "LateralRatioCritic: max_angle %.1f deg (ratio %.3f), slack %.3f m/s, weight %.1f, power %u",
    max_angle_deg, ratio_, slack_, weight_, power_);
}

void LateralRatioCritic::score(CriticData & data)
{
  // Off inside the goal position tolerance so the final alignment is not hindered.
  // 한글: 목표 위치 허용오차 안에서는 계산 안 함(최종 정렬 방해 금지).
  if (!enabled_ ||
    utils::withinPositionGoalTolerance(data.goal_checker, data.state.pose.pose, data.goal))
  {
    return;
  }
  auto cost = jetrover_nav_plugins::lateralRatioCost(
    data.state.vx, data.state.vy, ratio_, slack_, data.model_dt);
  if (power_ > 1u) {
    data.costs += xt::pow(cost * weight_, power_);
  } else {
    data.costs += cost * weight_;
  }
}

}  // namespace mppi::critics

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(mppi::critics::LateralRatioCritic, mppi::critics::CriticFunction)
