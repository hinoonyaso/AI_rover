// 호스트 watchdog 로직 단위시험. Host watchdog logic unit tests (time is passed in, no ROS).
#include <gtest/gtest.h>

#include "jetrover_base/link_watchdog.hpp"

using jetrover_base::LinkWatchdog;
using Action = LinkWatchdog::Action;

namespace
{
LinkWatchdog make()
{
  return LinkWatchdog(0.5, 1.0);  // base.yaml 기본값 / base.yaml defaults
}
}  // namespace

TEST(LinkWatchdog, IdleDoesNothing)
{
  auto w = make();
  w.on_open(0.0);
  EXPECT_EQ(w.check(0.5, true).action, Action::None);
}

TEST(LinkWatchdog, CmdVelTimeoutStopsOnlyWhileMoving)
{
  auto w = make();
  w.on_open(0.0);
  w.on_rx(0.4);
  w.on_cmd(0.4, true);
  w.on_rx(0.8);
  EXPECT_EQ(w.check(0.8, true).action, Action::None);  // 0.4초 경과 < 0.5
  w.on_rx(1.0);
  EXPECT_EQ(w.check(1.0, true).action, Action::StopCmdTimeout);  // 0.6초 경과
  EXPECT_FALSE(w.moving());
  EXPECT_EQ(w.check(1.05, true).action, Action::None);  // 한 번만 정지
}

TEST(LinkWatchdog, ZeroVelocityCommandIsNotMoving)
{
  auto w = make();
  w.on_open(0.0);
  w.on_cmd(0.0, false);
  w.on_rx(5.0);
  EXPECT_EQ(w.check(5.0, true).action, Action::None);
}

TEST(LinkWatchdog, NewCmdResetsTimeout)
{
  auto w = make();
  w.on_open(0.0);
  for (double t = 0.1; t < 2.0; t += 0.1) {
    w.on_rx(t);
    w.on_cmd(t, true);
    EXPECT_EQ(w.check(t, true).action, Action::None);
  }
}

TEST(LinkWatchdog, Stm32SilenceStopsAndLatches)
{
  auto w = make();
  w.on_open(0.0);
  w.on_cmd(0.9, true);
  const auto r = w.check(1.2, true);  // 마지막 수신 0.0 -> 1.2초 침묵
  EXPECT_EQ(r.action, Action::StopStm32Silent);
  EXPECT_NEAR(r.silent_s, 1.2, 1e-9);
  EXPECT_TRUE(r.was_moving);
  EXPECT_TRUE(w.stm32_silent());
  EXPECT_FALSE(w.moving());
  // 래치: 침묵이 계속돼도 heartbeat 정지를 반복하지 않는다
  EXPECT_EQ(w.check(3.0, true).action, Action::None);
}

TEST(LinkWatchdog, SilenceBelowThresholdIsFine)
{
  auto w = make();
  w.on_open(0.0);
  EXPECT_EQ(w.check(0.99, true).action, Action::None);
  EXPECT_FALSE(w.stm32_silent());
}

TEST(LinkWatchdog, RxRecoversFromSilent)
{
  auto w = make();
  w.on_open(0.0);
  w.check(2.0, true);
  ASSERT_TRUE(w.stm32_silent());
  EXPECT_TRUE(w.on_rx(2.1));    // 복구 보고는 한 번만
  EXPECT_FALSE(w.on_rx(2.2));
  EXPECT_FALSE(w.stm32_silent());
  EXPECT_EQ(w.check(2.5, true).action, Action::None);
}

TEST(LinkWatchdog, ClosedPortSkipsHeartbeatButNotCmdTimeout)
{
  auto w = make();
  w.on_open(0.0);
  EXPECT_EQ(w.check(10.0, false).action, Action::None);  // 포트 닫힘: heartbeat 검사 안 함
  EXPECT_FALSE(w.stm32_silent());
  w.on_cmd(10.0, true);
  EXPECT_EQ(w.check(10.6, false).action, Action::StopCmdTimeout);  // cmd timeout은 항상 검사
}

TEST(LinkWatchdog, SilentTakesPriorityAndConsumesMoving)
{
  auto w = make();
  w.on_open(0.0);
  w.on_cmd(0.0, true);
  // 둘 다 초과: heartbeat가 먼저 정지시키고 같은 틱에 cmd timeout이 중복 발동하지 않는다
  EXPECT_EQ(w.check(2.0, true).action, Action::StopStm32Silent);
  EXPECT_EQ(w.check(2.05, true).action, Action::None);
}

TEST(LinkWatchdog, CmdWhileSilentStillTimesOut)
{
  auto w = make();
  w.on_open(0.0);
  w.check(2.0, true);  // 침묵 래치
  w.on_cmd(2.0, true);  // 침묵 중에도 명령이 들어올 수 있다
  EXPECT_EQ(w.check(2.6, true).action, Action::StopCmdTimeout);
}

TEST(LinkWatchdog, OnStoppedClearsMoving)
{
  auto w = make();
  w.on_open(0.0);
  w.on_cmd(0.0, true);
  w.on_stopped();
  w.on_rx(5.0);
  EXPECT_EQ(w.check(5.0, true).action, Action::None);
}
