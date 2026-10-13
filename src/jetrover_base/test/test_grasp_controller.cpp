// 한글: GraspController(어댑터)의 허용 판정 표(R6)와 입력 전달 시험. 하드웨어 없음.
// Tests of the adapter's allow/deny table (R6) and input plumbing. No hardware.
#include <gtest/gtest.h>

#include <vector>

#include "jetrover_base/grasp_controller.hpp"

using namespace jetrover_base;   // NOLINT

namespace
{

struct Rig
{
  GraspController c;
  double t{50.0};
  int pos{200};
  int block{523};
  int final_pos{200};
  double done{0.0};

  GraspOutput tick(double temp = 40.0)
  {
    t += 0.05;
    if (t >= done) {
      pos = final_pos;
    }
    c.on_position(pos, t);
    c.on_temp(temp, t);
    const auto o = c.tick(t);
    if (o.command.valid) {
      final_pos = std::min(o.command.pulse, block);
      done = t + o.command.ms / 1000.0;
    }
    return o;
  }
  bool run_to(GraspState s, double limit = 60.0)
  {
    const double end = t + limit;
    while (t < end) {
      if (tick().state == s) {
        return true;
      }
    }
    return false;
  }
};

const std::vector<uint8_t> kArm{1, 2, 3, 4, 5};
const std::vector<uint8_t> kGripper{10};
const std::vector<uint8_t> kBoth{1, 10};

}  // namespace

TEST(GraspController, IdleLeavesEverythingAsBefore)
{
  Rig r;
  for (auto src : {CommandSource::Manual, CommandSource::Automated}) {
    EXPECT_EQ(r.c.deny_reason(kArm, src), "");
    EXPECT_EQ(r.c.deny_reason(kGripper, src), "");
    EXPECT_EQ(r.c.deny_reason(kBoth, src), "");
  }
  EXPECT_EQ(r.c.deny_reason_global(), "");
}

TEST(GraspController, WhileClosingTheGripperAndTheArmAreBothDenied)
{
  Rig r;
  ASSERT_TRUE(r.c.start(r.t));
  ASSERT_TRUE(r.run_to(GraspState::Closing, 5.0));
  for (auto src : {CommandSource::Manual, CommandSource::Automated}) {
    EXPECT_NE(r.c.deny_reason(kGripper, src), "");
    EXPECT_NE(r.c.deny_reason(kArm, src), "");
    EXPECT_NE(r.c.deny_reason(kBoth, src), "");
  }
  EXPECT_NE(r.c.deny_reason_global(), "");
}

TEST(GraspController, HoldingAllowsArmMotionButNeverTheGripper)
{
  Rig r;
  ASSERT_TRUE(r.c.start(r.t));
  ASSERT_TRUE(r.run_to(GraspState::Holding));
  for (auto src : {CommandSource::Manual, CommandSource::Automated}) {
    EXPECT_EQ(r.c.deny_reason(kArm, src), "") << "MoveIt must be able to carry the object";
    EXPECT_NE(r.c.deny_reason(kGripper, src), "");
    EXPECT_NE(r.c.deny_reason(kBoth, src),
      "") << "a command that touches ID 10 is refused as a whole";
  }
  EXPECT_NE(r.c.deny_reason_global(), "") << "torque release / home move would drop the object";
  // ID 10 stays refused for as long as we hold
  for (int i = 0; i < 300; ++i) {
    r.tick();
    ASSERT_NE(r.c.deny_reason(kGripper, CommandSource::Manual), "");
  }
}

TEST(GraspController, FaultInTheAirAllowsOnlyManualRecoveryMoves)
{
  Rig r;
  ASSERT_TRUE(r.c.start(r.t));
  ASSERT_TRUE(r.run_to(GraspState::Holding));
  r.c.set_caller_lifted(1);
  r.c.cancel();
  for (int i = 0; i < 5; ++i) {
    r.tick();
  }
  ASSERT_TRUE(r.c.last().needs_user);
  EXPECT_EQ(r.c.deny_reason(kArm, CommandSource::Manual), "");
  EXPECT_NE(r.c.deny_reason(kArm, CommandSource::Automated), "");
  EXPECT_NE(r.c.deny_reason(kGripper, CommandSource::Manual), "");
}

TEST(GraspController, ReleaseReturnsTheGripperToEveryone)
{
  Rig r;
  ASSERT_TRUE(r.c.start(r.t));
  ASSERT_TRUE(r.run_to(GraspState::Holding));
  ASSERT_TRUE(r.c.release(r.t));
  ASSERT_TRUE(r.run_to(GraspState::Idle, 5.0));
  EXPECT_EQ(r.c.deny_reason(kGripper, CommandSource::Manual), "");
  EXPECT_EQ(r.c.deny_reason(kGripper, CommandSource::Automated), "");
  EXPECT_EQ(r.c.deny_reason_global(), "");
}

TEST(GraspController, FailedKeepsTheGripperUntilReset)
{
  Rig r;
  r.block = 700;   // nothing to grasp: NoContact
  ASSERT_TRUE(r.c.start(r.t));
  ASSERT_TRUE(r.run_to(GraspState::Failed));
  EXPECT_NE(r.c.deny_reason(kGripper, CommandSource::Manual), "");
  EXPECT_NE(r.c.deny_reason(kArm, CommandSource::Manual), "");
  ASSERT_TRUE(r.c.reset());
  EXPECT_EQ(r.c.deny_reason(kGripper, CommandSource::Manual), "");
}

TEST(GraspController, ATemperatureOlderThanTheLimitCountsAsMissing)
{
  GraspController c;
  ASSERT_TRUE(c.start(10.0));
  c.on_position(200, 10.0);
  c.on_temp(40.0, 4.0);            // 6 s old at t=10, limit 5 s
  c.tick(10.0, 5.0);
  EXPECT_EQ(c.state(), GraspState::Check);     // no usable temperature yet: it does not start blind
  c.on_temp(40.0, 10.1);
  c.on_position(200, 10.1);
  const auto o = c.tick(10.2, 5.0);
  EXPECT_EQ(o.state, GraspState::Closing);
}

TEST(GraspController, NamesAreStableBecauseTheyGoIntoActionResultsAndTopics)
{
  EXPECT_STREQ(grasp_state_name(GraspState::Holding), "Holding");
  EXPECT_STREQ(grasp_state_name(GraspState::Idle), "Idle");
  EXPECT_STREQ(grasp_fail_name(GraspFail::OutsideWindow), "OutsideWindow");
  EXPECT_STREQ(grasp_fail_name(GraspFail::None), "");
}

TEST(GraspController, LastReadingsAndElapsedForFeedback)
{
  GraspController c;
  EXPECT_EQ(c.last_position(), -1);
  EXPECT_LT(c.last_temp(), 0.0);
  ASSERT_TRUE(c.start(10.0));
  c.on_position(321, 10.2);
  c.on_temp(47.0, 10.2);
  EXPECT_EQ(c.last_position(), 321);
  EXPECT_DOUBLE_EQ(c.last_temp(), 47.0);
  EXPECT_NEAR(c.elapsed(12.5), 2.5, 1e-9);
}

TEST(GraspController, ReadingsTakenBeforeTheStartAreNotUsed)
{
  // Regression (found in the L1 run, 2026-10-14): a 40 C temperature received 3 s before the start let a grasp begin
  // although the gripper was really at 82 C, and an old position became the "start" position.
  GraspController c;
  c.on_position(450, 5.0);          // old position, would be > open_start_max anyway
  c.on_temp(40.0, 8.0);             // 2 s old at the start, inside the 5 s age limit
  ASSERT_TRUE(c.start(10.0));
  auto o = c.tick(10.1);
  EXPECT_EQ(o.state, GraspState::Check) << "must wait for a fresh position and temperature";
  EXPECT_FALSE(o.command.valid);
  EXPECT_EQ(c.last_position(), -1);
  c.on_position(200, 10.2);
  o = c.tick(10.3);
  EXPECT_EQ(o.state,
    GraspState::Check) << "a position alone is not enough: the temperature is still unknown";
  c.on_temp(82.0, 10.3);            // the real, hot value
  o = c.tick(10.4);
  EXPECT_EQ(o.state, GraspState::Failed);
  EXPECT_EQ(o.fail, GraspFail::TempHigh);
  EXPECT_FALSE(o.command.valid);
}
