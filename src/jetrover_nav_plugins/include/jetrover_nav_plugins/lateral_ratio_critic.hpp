// Copyright 2026 sang
// Licensed under the Apache License, Version 2.0
#ifndef JETROVER_NAV_PLUGINS__LATERAL_RATIO_CRITIC_HPP_
#define JETROVER_NAV_PLUGINS__LATERAL_RATIO_CRITIC_HPP_

#include "nav2_mppi_controller/critic_function.hpp"

namespace mppi::critics
{

/**
 * Penalizes trajectory parts whose lateral speed exceeds tan(max_angle_deg) times the forward
 * speed, so a mecanum base moves at most max_angle_deg off its heading (the front-only depth
 * camera, horizontal FOV about +-41 deg, keeps seeing the direction of travel). Inside it the
 * robot may slide diagonally freely. Soft constraint (a cost), verified on the robot.
 * Lives in mppi::critics because MPPI looks critics up as "mppi::critics::<name>".
 * 한글: 옆 속도가 tan(최대각) x 전진 속도를 넘는 궤적에 벌점 -> 진행 방향을 몸 정면 45도 이내로.
 * 비용이라 절대 보장은 아니며 실기로 검증한다. MPPI가 이름 앞에 mppi::critics::를 붙여 찾으므로 이 네임스페이스.
 */
class LateralRatioCritic : public CriticFunction
{
public:
  void initialize() override;
  void score(CriticData & data) override;

protected:
  unsigned int power_{1};
  float weight_{50.0f};
  float ratio_{1.0f};   // tan(max_angle_deg)
  float slack_{0.02f};  // m/s of lateral speed always allowed (start-up corrections) / 항상 허용하는 옆 속도
};

}  // namespace mppi::critics

#endif  // JETROVER_NAV_PLUGINS__LATERAL_RATIO_CRITIC_HPP_
