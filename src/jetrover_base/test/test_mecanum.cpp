// 메카넘 기구학 단위시험. Mecanum kinematics unit tests (no ROS / hardware).
#include <gtest/gtest.h>

#include <cmath>

#include "jetrover_base/mecanum.hpp"

using namespace jetrover_base;  // NOLINT

namespace
{
// config/base.yaml과 같은 형상값 / same geometry as config/base.yaml
constexpr double kWheelbase = 0.216;
constexpr double kTrack = 0.195;
constexpr double kDiameter = 0.097;
const double kToRps = 1.0 / (M_PI * kDiameter);

std::vector<MotorCommand> ik(double vx, double vy, double wz)
{
  return mecanum_inverse(vx, vy, wz, kWheelbase, kTrack, kDiameter);
}
}  // namespace

TEST(MecanumInverse, PortIdsAreOneToFour)
{
  const auto m = ik(0.1, 0, 0);
  ASSERT_EQ(m.size(), 4u);
  for (int i = 0; i < 4; ++i) {
    EXPECT_EQ(m[i].id, i + 1);
  }
}

// 전진: 왼쪽 +, 오른쪽 -(미러 장착) / forward: left +, right negated
TEST(MecanumInverse, ForwardSigns)
{
  const auto m = ik(0.1, 0, 0);
  EXPECT_NEAR(m[0].rps, 0.1 * kToRps, 1e-5);
  EXPECT_NEAR(m[1].rps, 0.1 * kToRps, 1e-5);
  EXPECT_NEAR(m[2].rps, -0.1 * kToRps, 1e-5);
  EXPECT_NEAR(m[3].rps, -0.1 * kToRps, 1e-5);
}

// 왼쪽 옆이동(+vy): 앞왼쪽 -, 뒤왼쪽 +, 앞오른쪽 -, 뒤오른쪽 +
TEST(MecanumInverse, StrafeLeftSigns)
{
  const auto m = ik(0, 0.1, 0);
  EXPECT_LT(m[0].rps, 0);
  EXPECT_GT(m[1].rps, 0);
  EXPECT_LT(m[2].rps, 0);
  EXPECT_GT(m[3].rps, 0);
}

// 제자리 좌회전(+wz): 왼쪽 바퀴는 후진(rps -), 오른쪽 바퀴는 전진이지만 미러 장착이라 rps도 -. 4개 모두 음수.
// Rotate left: left wheels reverse, right wheels forward (= negative rps due to mirroring) -> all negative.
TEST(MecanumInverse, RotateLeftSigns)
{
  for (const auto & c : ik(0, 0, 1.0)) {
    EXPECT_LT(c.rps, 0);
  }
}

TEST(MecanumInverse, ZeroIsZero)
{
  for (const auto & c : ik(0, 0, 0)) {
    EXPECT_EQ(c.rps, 0.0f);
  }
}

TEST(MecanumInverse, LinearInSpeed)
{
  const auto a = ik(0.05, 0.02, 0.3);
  const auto b = ik(0.10, 0.04, 0.6);
  for (int i = 0; i < 4; ++i) {
    EXPECT_NEAR(b[i].rps, 2.0 * a[i].rps, 1e-5);
  }
}

// IK -> FK 왕복이 원래 속도를 복원해야 한다 (엔코더 odom의 전제).
TEST(MecanumRoundTrip, ForwardInvertsInverse)
{
  const double cases[][3] = {
    {0.2, 0, 0}, {0, 0.15, 0}, {0, 0, 1.0}, {0.1, -0.08, 0.5}, {-0.2, 0.2, -1.0}, {0, 0, 0}};
  for (const auto & c : cases) {
    const auto m = ik(c[0], c[1], c[2]);
    const double rps[4] = {m[0].rps, m[1].rps, m[2].rps, m[3].rps};
    const auto t = mecanum_forward(rps, kWheelbase, kTrack, kDiameter);
    EXPECT_NEAR(t.vx, c[0], 1e-5);
    EXPECT_NEAR(t.vy, c[1], 1e-5);
    EXPECT_NEAR(t.wz, c[2], 1e-5);
  }
}
