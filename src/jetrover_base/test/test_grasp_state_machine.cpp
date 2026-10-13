// 한글: GraspStateMachine 시나리오 시험(순수 로직, 하드웨어 없음). 시뮬레이션 그리퍼가 명령을 따라가다 물체(block)에서 멈춘다.
//       이 시험은 하드웨어 증거가 아니다 — 실기 검증은 T6. (prd/arm-control-path-test-plan.md T5, A1~A10)
// Scenario tests for GraspStateMachine against a simulated gripper (not hardware evidence; real robot = T6).
#include <gtest/gtest.h>

#include <algorithm>
#include <random>
#include <vector>

#include "jetrover_base/grasp_state_machine.hpp"

using namespace jetrover_base;   // NOLINT

namespace
{

// Simulated gripper: follows a command after `ms` unless it meets `block`; the jaws touch at 693; 3-pulse dead band.
struct Sim
{
  explicit Sim(GraspProfile p = GraspProfile(), int block_pos = -1, unsigned seed = 1)
  : sm(p), block(block_pos), rng(seed) {}

  GraspStateMachine sm;
  double t{100.0};
  int pos{200};
  int block;
  int final_pos{200};
  double done_at{0.0};
  double drop{0.0};                 // probability that a reading is missing
  bool silent{false};               // no readings at all
  double temp{40.0};
  bool has_temp{true};
  int wobble{0};                    // added to the reading (simulates a squeeze that does not hold still)
  ArmContext arm;
  std::mt19937 rng;
  std::vector<GraspCommand> cmds;
  GraspOutput last;

  void apply(const GraspCommand & c)
  {
    cmds.push_back(c);
    int stop = std::min(c.pulse, 693);
    if (block >= 0) {
      stop = std::min(stop, block);
    }
    if (std::abs(stop - pos) > 3) {
      final_pos = stop;
    }
    done_at = t + c.ms / 1000.0;
  }

  GraspOutput tick(double dt = 0.05)
  {
    t += dt;
    if (t >= done_at) {
      pos = final_pos;
    }
    GraspInput in;
    in.now = t;
    std::uniform_real_distribution<double> u(0.0, 1.0);
    in.has_reading = !silent && u(rng) >= drop;
    in.position = pos + wobble;
    in.reading_time = t;
    in.has_temp = has_temp;
    in.temp_c = temp;
    in.arm = arm;
    last = sm.update(in);
    if (last.command.valid) {
      apply(last.command);
    }
    return last;
  }

  // Tick until `pred` or the limit; returns whether `pred` became true.
  template<class F>
  bool run_until(F pred, double limit_s = 60.0)
  {
    const double end = t + limit_s;
    while (t < end) {
      tick();
      if (pred(last)) {
        return true;
      }
    }
    return false;
  }
  bool run_to(GraspState s, double limit_s = 60.0)
  {
    return run_until([s](const GraspOutput & o) {return o.state == s;}, limit_s);
  }
  int max_pulse() const
  {
    int m = 0;
    for (const auto & c : cmds) {
      m = std::max(m, c.pulse);
    }
    return m;
  }
};

GraspProfile profile() {return GraspProfile();}

}  // namespace

// ---------------------------------------------------------------------------------------------- A1 normal grasp
TEST(Grasp, NormalGraspReachesHoldingAndKeepsTheGripper)
{
  Sim s(profile(), 523);
  ASSERT_TRUE(s.sm.start(s.t));
  int success_events = 0;
  ASSERT_TRUE(s.run_until([&](const GraspOutput & o) {
      success_events += o.success_event; return o.state == GraspState::Holding;
                                                                                                                               }));
  EXPECT_EQ(success_events, 1);
  EXPECT_NEAR(s.last.contact, 523, 4);
  EXPECT_TRUE(s.last.gripper_owned);
  EXPECT_EQ(s.last.arm_motion, ArmMotion::Allowed);       // HOLDING: the arm may carry the object
  EXPECT_FALSE(s.last.needs_user);
  // the squeeze command is contact + 16 (cube3cm only)
  EXPECT_EQ(s.cmds.back().pulse, s.last.contact + 16);
  // stays HOLDING and keeps ownership, no further success event
  for (int i = 0; i < 400; ++i) {
    s.tick();
    ASSERT_EQ(s.last.state, GraspState::Holding);
    ASSERT_TRUE(s.last.gripper_owned);
    ASSERT_FALSE(s.last.success_event);
  }
}

TEST(Grasp, NearbyContactsInsideTheWindowAreAccepted)
{
  for (int block : {520, 525, 532, 535}) {
    Sim s(profile(), block);
    ASSERT_TRUE(s.sm.start(s.t));
    EXPECT_TRUE(s.run_to(GraspState::Holding)) << block;
  }
}

// ----------------------------------------------------------------------- A2 empty close / outside window / bad start
TEST(Grasp, EmptyCloseFailsWithoutSqueezeAndReopens)
{
  Sim s(profile(), -1);
  ASSERT_TRUE(s.sm.start(s.t));
  ASSERT_TRUE(s.run_to(GraspState::Failed));
  EXPECT_EQ(s.last.fail, GraspFail::NoContact);
  EXPECT_LE(s.max_pulse(), 693 - 6);                       // never commanded into the closed end (A6)
  ASSERT_TRUE(s.cmds.back().valid);
  EXPECT_EQ(s.cmds.back().pulse, 200);                     // reopened to the start position
  EXPECT_TRUE(s.last.gripper_owned);                       // still owned until reset()
  EXPECT_EQ(s.last.arm_motion, ArmMotion::Denied);
  EXPECT_TRUE(s.sm.reset());
  EXPECT_EQ(s.sm.state(), GraspState::Idle);
}

TEST(Grasp, ContactOutsideTheWindowIsNotSqueezed)
{
  for (int block : {300, 440, 480, 560, 585, 640}) {      // fingers, a tilted cube (T3: 382, 492), a larger object
    Sim s(profile(), block);
    ASSERT_TRUE(s.sm.start(s.t));
    ASSERT_TRUE(s.run_to(GraspState::Failed)) << block;
    EXPECT_EQ(s.last.fail, GraspFail::OutsideWindow) << block;
    EXPECT_EQ(s.cmds.back().pulse, 200) << block;          // reopened, not squeezed
    // The closing steps may command one step (12) beyond the contact -- that is how the block is found. A squeeze
    // (contact + 16) must never be commanded. 한글: 닫기 단계는 접촉보다 한 스텝 앞까지 명령할 수 있다(막힘을 발견하는 방법). 조임은 금지.
    for (const auto & c : s.cmds) {
      EXPECT_LE(c.pulse, s.last.contact + s.sm.profile().step) << block;
      EXPECT_NE(c.pulse, s.last.contact + s.sm.profile().squeeze) << block;
    }
  }
}

TEST(Grasp, NearlyClosedStartIsRefusedWithoutMoving)
{
  Sim s(profile(), -1);
  s.pos = s.final_pos = 600;
  ASSERT_TRUE(s.sm.start(s.t));
  ASSERT_TRUE(s.run_to(GraspState::Failed, 5.0));
  EXPECT_EQ(s.last.fail, GraspFail::BadStart);
  EXPECT_TRUE(s.cmds.empty());
}

// ---------------------------------------------------------------------------------------------- A3 missing readings
TEST(Grasp, ReadingLossDuringClosingStopsInsteadOfGuessing)
{
  Sim s(profile(), 523);
  ASSERT_TRUE(s.sm.start(s.t));
  ASSERT_TRUE(s.run_until([](const GraspOutput & o) {return o.state == GraspState::Closing;}, 5.0));
  s.silent = true;
  ASSERT_TRUE(s.run_to(GraspState::Failed, 10.0));
  EXPECT_EQ(s.last.fail, GraspFail::NoReading);
  EXPECT_EQ(s.last.contact, -1);                           // it never reported a contact it did not see
}

TEST(Grasp, RandomReadingDropsNeverProduceAWrongOrFalseContact)
{
  int holding = 0, failed = 0;
  for (unsigned seed = 0; seed < 150; ++seed) {
    {   // a cube: either grasped at the right place or stopped; never a wrong contact
      Sim s(profile(), 523, seed);
      s.drop = 0.3;
      ASSERT_TRUE(s.sm.start(s.t));
      s.run_until([](const GraspOutput & o) {
          return o.state == GraspState::Holding || o.state == GraspState::Failed;
                                                                                                                    },
        90.0);
      if (s.last.state == GraspState::Holding) {
        ++holding;
        EXPECT_NEAR(s.last.contact, 523, 5) << seed;
      } else {
        ++failed;
        EXPECT_TRUE(s.last.fail == GraspFail::NoReading || s.last.fail == GraspFail::Timeout ||
          s.last.fail == GraspFail::HoldNotStable) << seed;
      }
    }
    {   // nothing there: a contact would be a false one
      Sim s(profile(), -1, seed);
      s.drop = 0.3;
      ASSERT_TRUE(s.sm.start(s.t));
      s.run_until([](const GraspOutput & o) {
          return o.state == GraspState::Failed || o.state == GraspState::Holding;
                                                                                                                    },
        90.0);
      EXPECT_EQ(s.last.state, GraspState::Failed) << seed;
      EXPECT_NE(s.last.fail, GraspFail::OutsideWindow) << seed;
      EXPECT_EQ(s.last.contact, -1) << seed;
    }
  }
  EXPECT_GT(holding, 0);
  EXPECT_EQ(holding + failed, 150);
}

// ---------------------------------------------------------------------------------------------- A4 temperature
TEST(Grasp, HotGripperRefusesToStartWithoutAnyCommand)
{
  Sim s(profile(), 523);
  s.temp = 80.0;
  ASSERT_TRUE(s.sm.start(s.t));
  ASSERT_TRUE(s.run_to(GraspState::Failed, 5.0));
  EXPECT_EQ(s.last.fail, GraspFail::TempHigh);
  EXPECT_TRUE(s.cmds.empty());
}

TEST(Grasp, NoTemperatureReadingAtTheStartRefusesToStart)
{
  Sim s(profile(), 523);
  s.has_temp = false;
  ASSERT_TRUE(s.sm.start(s.t));
  ASSERT_TRUE(s.run_to(GraspState::Failed, 10.0));
  EXPECT_EQ(s.last.fail, GraspFail::NoReading);
  EXPECT_TRUE(s.cmds.empty());
}

TEST(Grasp, TemperatureRisingWhileClosingOpensToTheStart)
{
  Sim s(profile(), 523);
  ASSERT_TRUE(s.sm.start(s.t));
  ASSERT_TRUE(s.run_until([](const GraspOutput & o) {return o.state == GraspState::Closing;}, 5.0));
  s.run_until([&](const GraspOutput &) {return s.cmds.size() >= 4;}, 10.0);
  s.temp = 81.0;
  ASSERT_TRUE(s.run_to(GraspState::Failed, 5.0));
  EXPECT_EQ(s.last.fail, GraspFail::TempHigh);
  EXPECT_EQ(s.cmds.back().pulse, 200);
}

TEST(Grasp, TemperatureRisingDuringTheSqueezeRelaxesToTheContact)
{
  Sim s(profile(), 523);
  ASSERT_TRUE(s.sm.start(s.t));
  ASSERT_TRUE(s.run_to(GraspState::Squeeze));
  const int contact = s.last.contact;
  s.temp = 85.0;
  ASSERT_TRUE(s.run_to(GraspState::Failed, 5.0));
  EXPECT_EQ(s.last.fail, GraspFail::TempHigh);
  EXPECT_EQ(s.cmds.back().pulse, contact);                 // squeeze released, object not dropped from a height
}

TEST(Grasp, TimeoutStopsAndReopens)
{
  GraspProfile p = profile();
  p.timeout_s = 4.0;
  Sim s(p, -1);
  ASSERT_TRUE(s.sm.start(s.t));
  ASSERT_TRUE(s.run_to(GraspState::Failed, 10.0));
  EXPECT_EQ(s.last.fail, GraspFail::Timeout);
  EXPECT_EQ(s.cmds.back().pulse, 200);
}

// ---------------------------------------------------------------------------------------------- A5 fault policy
TEST(Grasp, CancelWhileClosingOpensToTheStart)
{
  Sim s(profile(), 523);
  ASSERT_TRUE(s.sm.start(s.t));
  s.run_until([&](const GraspOutput &) {return s.cmds.size() >= 5;}, 10.0);
  s.sm.request_cancel();
  ASSERT_TRUE(s.run_to(GraspState::Failed, 2.0));
  EXPECT_EQ(s.last.fail, GraspFail::Cancelled);
  EXPECT_EQ(s.cmds.back().pulse, 200);
}

TEST(Grasp, CancelDuringTheSqueezeRelaxesToTheContact)
{
  Sim s(profile(), 523);
  ASSERT_TRUE(s.sm.start(s.t));
  ASSERT_TRUE(s.run_to(GraspState::Squeeze));
  const int contact = s.last.contact;
  s.sm.request_cancel();
  ASSERT_TRUE(s.run_to(GraspState::Failed, 2.0));
  EXPECT_EQ(s.last.fail, GraspFail::Cancelled);
  EXPECT_EQ(s.cmds.back().pulse, contact);
}

TEST(Grasp, SqueezeThatDoesNotHoldStillFailsAndRelaxes)
{
  Sim s(profile(), 523);
  ASSERT_TRUE(s.sm.start(s.t));
  ASSERT_TRUE(s.run_to(GraspState::Squeeze));
  int k = 0;
  while (s.last.state == GraspState::Squeeze && k < 200) {
    s.wobble = (k++ % 20 < 10) ? 0 : 6;                   // 6-pulse swings > hold_tol 3
    s.tick();
  }
  ASSERT_EQ(s.last.state, GraspState::Failed);
  EXPECT_EQ(s.last.fail, GraspFail::HoldNotStable);
}

TEST(Grasp, SmallJitterInsideTheHoldToleranceIsAccepted)
{
  Sim s(profile(), 523);
  ASSERT_TRUE(s.sm.start(s.t));
  ASSERT_TRUE(s.run_to(GraspState::Squeeze));
  int k = 0;
  while (s.last.state == GraspState::Squeeze && k < 200) {
    s.wobble = (k++ % 20 < 10) ? 0 : 3;
    s.tick();
  }
  EXPECT_EQ(s.last.state, GraspState::Holding);
}

namespace
{
Sim holding_sim(ArmContext arm)
{
  Sim s(profile(), 523);
  EXPECT_TRUE(s.sm.start(s.t));
  EXPECT_TRUE(s.run_to(GraspState::Holding));
  s.arm = arm;
  return s;
}
}  // namespace

TEST(Grasp, FaultWhileHoldingNearTheGroundOpensTheGripper)
{
  Sim s = holding_sim(ArmContext{0, 0});
  const size_t before = s.cmds.size();
  s.sm.request_cancel();
  ASSERT_TRUE(s.run_to(GraspState::Releasing, 1.0));
  ASSERT_GT(s.cmds.size(), before);
  EXPECT_EQ(s.cmds.back().pulse, 200);
  ASSERT_TRUE(s.run_to(GraspState::Idle, 5.0));
  EXPECT_FALSE(s.last.gripper_owned);                      // ownership came back
}

TEST(Grasp, FaultWhileHoldingInTheAirNeverOpens)
{
  struct Case {int caller; int pose; const char * what;};
  const Case cases[] = {{1, 1, "both lifted"}, {-1, -1, "unknown"},
    {0, 1, "caller says low, pose says high"},
    {1, 0, "caller says high, pose says low"}, {-1, 0, "pose low, caller unknown"},
    {0, -1, "caller low, pose unknown"}};
  for (const auto & c : cases) {
    for (int kind = 0; kind < 3; ++kind) {                // cancel, comm loss, temperature
      Sim s = holding_sim(ArmContext{c.caller, c.pose});
      const size_t before = s.cmds.size();
      if (kind == 0) {
        s.sm.request_cancel();
      } else if (kind == 1) {
        s.silent = true;
      } else {
        s.temp = 83.0;
      }
      s.run_until([](const GraspOutput & o) {return o.needs_user;}, 5.0);
      EXPECT_EQ(s.last.state, GraspState::Holding) << c.what << " kind " << kind;
      EXPECT_TRUE(s.last.needs_user) << c.what << " kind " << kind;
      EXPECT_EQ(s.last.arm_motion, ArmMotion::RecoveryOnly) << c.what;
      EXPECT_TRUE(s.last.gripper_owned) << c.what;
      for (int i = 0; i < 200; ++i) {
        s.tick();
      }
      EXPECT_EQ(s.cmds.size(),
        before) << "a command was sent in the air: " << c.what << " kind " << kind;
    }
  }
}

TEST(Grasp, FaultWhileHoldingNearTheGroundOnCommLossAndHeatAlsoOpens)
{
  for (int kind = 0; kind < 2; ++kind) {
    Sim s = holding_sim(ArmContext{0, 0});
    if (kind == 0) {
      s.silent = true;
    } else {
      s.temp = 82.0;
    }
    ASSERT_TRUE(s.run_to(GraspState::Releasing, 5.0)) << kind;
    EXPECT_EQ(s.cmds.back().pulse, 200) << kind;
  }
}

// ---------------------------------------------------------------------------------------------- A7 release / ownership
TEST(Grasp, ReleaseIsOnlyAcceptedInHoldingAndReturnsOwnership)
{
  Sim s(profile(), 523);
  EXPECT_FALSE(s.sm.release(s.t));                         // IDLE
  ASSERT_TRUE(s.sm.start(s.t));
  EXPECT_FALSE(s.sm.start(s.t));                           // already running
  EXPECT_FALSE(s.sm.release(s.t));                         // CHECK/CLOSING
  ASSERT_TRUE(s.run_to(GraspState::Holding));
  ASSERT_TRUE(s.sm.release(s.t));
  ASSERT_TRUE(s.run_to(GraspState::Releasing, 1.0));
  EXPECT_TRUE(s.last.gripper_owned);                       // still ours while opening
  EXPECT_EQ(s.last.arm_motion, ArmMotion::Denied);
  ASSERT_TRUE(s.run_to(GraspState::Idle, 5.0));
  EXPECT_EQ(s.cmds.back().pulse, 200);
  EXPECT_FALSE(s.last.gripper_owned);
  EXPECT_TRUE(GraspStateMachine::external_gripper_command_allowed(s.last.state));
  EXPECT_TRUE(s.sm.start(s.t));                            // a new grasp can start
}

TEST(Grasp, ExplicitReleaseOpensEvenAfterAnInTheAirFault)
{
  Sim s = holding_sim(ArmContext{1, 1});
  s.sm.request_cancel();
  ASSERT_TRUE(s.run_until([](const GraspOutput & o) {return o.needs_user;}, 2.0));
  s.arm = ArmContext{0, 0};                                // the operator has put the object down
  ASSERT_TRUE(s.sm.release(s.t));
  ASSERT_TRUE(s.run_to(GraspState::Idle, 5.0));
  EXPECT_EQ(s.cmds.back().pulse, 200);
}

TEST(Grasp, FailedStateKeepsTheGripperUntilReset)
{
  Sim s(profile(), -1);
  ASSERT_TRUE(s.sm.start(s.t));
  ASSERT_TRUE(s.run_to(GraspState::Failed));
  for (int i = 0; i < 50; ++i) {
    s.tick();
    ASSERT_EQ(s.last.state, GraspState::Failed);
    ASSERT_TRUE(s.last.gripper_owned);
  }
  EXPECT_FALSE(s.sm.start(s.t));
  EXPECT_TRUE(s.sm.reset());
  EXPECT_FALSE(s.sm.reset());
}

// ---------------------------------------------------------------------------------------------- A6 limits
TEST(Grasp, SqueezeNeverGoesBeyondTheClosedEnd)
{
  GraspProfile p = profile();
  p.contact_hi = 690;
  p.squeeze = 60;                                          // would be 740 without the clamp
  Sim s(p, 670);
  ASSERT_TRUE(s.sm.start(s.t));
  ASSERT_TRUE(s.run_to(GraspState::Squeeze));
  EXPECT_LE(s.max_pulse(), 693 - 6);
}

// ---------------------------------------------------------------------------------------------- A8 control table
TEST(Grasp, ControlTableMatchesR6)
{
  const struct {GraspState s; bool ext; ArmMotion arm;} t[] = {
    {GraspState::Idle, true, ArmMotion::Allowed},
    {GraspState::Check, false, ArmMotion::Denied},
    {GraspState::Closing, false, ArmMotion::Denied},
    {GraspState::Squeeze, false, ArmMotion::Denied},
    {GraspState::Holding, false, ArmMotion::Allowed},
    {GraspState::Releasing, false, ArmMotion::Denied},
    {GraspState::Failed, false, ArmMotion::Denied}};
  for (const auto & r : t) {
    EXPECT_EQ(GraspStateMachine::external_gripper_command_allowed(r.s), r.ext);
    EXPECT_EQ(GraspStateMachine::arm_motion_for(r.s, false), r.arm);
  }
  EXPECT_EQ(GraspStateMachine::arm_motion_for(GraspState::Holding, true), ArmMotion::RecoveryOnly);
}

TEST(Grasp, LiftedIsConservative)
{
  EXPECT_FALSE(is_lifted(ArmContext{0, 0}));
  for (int a : {-1, 0, 1}) {
    for (int b : {-1, 0, 1}) {
      if (!(a == 0 && b == 0)) {
        EXPECT_TRUE(is_lifted(ArmContext{a, b})) << a << "," << b;
      }
    }
  }
}

TEST(Grasp, CancelInIdleIsIgnored)
{
  Sim s(profile(), 523);
  s.sm.request_cancel();
  ASSERT_TRUE(s.sm.start(s.t));
  EXPECT_TRUE(s.run_to(GraspState::Holding));
}
