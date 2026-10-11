#include <gtest/gtest.h>

#include "jetrover_base/servo_stats.hpp"

using jetrover_base::ServoStats;

TEST(ServoStats, MatchesRepliesAndMeasuresLatencyAndPeriod)
{
  ServoStats s(0.5);
  for (int i = 0; i < 5; ++i) {
    const double t = i * 1.0;
    s.record_request(3, t);
    s.record_reply(3, t + 0.02);
  }
  const auto snap = s.snapshot(3, 5.0);
  EXPECT_EQ(snap.requests, 5u);
  EXPECT_EQ(snap.replies, 5u);
  EXPECT_EQ(snap.misses, 0u);
  EXPECT_NEAR(snap.mean_latency_s, 0.02, 1e-9);
  EXPECT_NEAR(snap.max_latency_s, 0.02, 1e-9);
  EXPECT_NEAR(snap.mean_period_s, 1.0, 1e-9);
  EXPECT_NEAR(snap.last_reply_t, 4.02, 1e-9);
}

TEST(ServoStats, UnansweredRequestBecomesAMissAfterTheTimeout)
{
  ServoStats s(0.5);
  s.record_request(1, 0.0);          // never answered
  s.record_request(1, 1.0);          // expires the first one
  s.record_reply(1, 1.03);
  auto snap = s.snapshot(1, 1.1);
  EXPECT_EQ(snap.requests, 2u);
  EXPECT_EQ(snap.replies, 1u);
  EXPECT_EQ(snap.misses, 1u);
  s.record_request(1, 2.0);          // outstanding, not yet a miss
  EXPECT_EQ(s.snapshot(1, 2.2).misses, 1u);
  EXPECT_EQ(s.snapshot(1, 2.6).misses, 2u);   // snapshot expires it
}

TEST(ServoStats, ReplyMatchesTheNewestRequestAndOlderOnesAreLost)
{
  // Requests every 0.3 s with a 0.5 s timeout (20 Hz): the first request is lost, the second is answered in 5 ms.
  // Matching the oldest request would report 0.305 s of latency; the newest-match rule reports the real 5 ms.
  ServoStats s(0.5);
  s.record_request(4, 0.0);
  s.record_request(4, 0.3);
  s.record_reply(4, 0.305);
  const auto snap = s.snapshot(4, 0.4);
  EXPECT_EQ(snap.replies, 1u);
  EXPECT_EQ(snap.misses, 1u);
  EXPECT_NEAR(snap.max_latency_s, 0.005, 1e-9);
}

TEST(ServoStats, FailureFrameEndsTheRequestButIsNotAReading)
{
  ServoStats s(0.5);
  s.record_request(3, 0.0);
  s.record_reply(3, 0.04, false);    // STM32: servo did not answer
  s.record_request(3, 1.0);
  s.record_reply(3, 1.004, true);
  const auto snap = s.snapshot(3, 1.1);
  EXPECT_EQ(snap.requests, 2u);
  EXPECT_EQ(snap.replies, 1u);
  EXPECT_EQ(snap.failed_replies, 1u);
  EXPECT_EQ(snap.misses, 0u);        // a failure frame is not a lost frame
  EXPECT_NEAR(snap.last_reply_t, 1.004, 1e-9);
  EXPECT_NEAR(snap.mean_latency_s, 0.004, 1e-9);
}

TEST(ServoStats, LateReplyAfterAMissIsUnmatchedNotAReply)
{
  ServoStats s(0.5);
  s.record_request(2, 0.0);
  s.record_reply(2, 0.9);            // came after the 0.5 s timeout
  const auto snap = s.snapshot(2, 1.0);
  EXPECT_EQ(snap.misses, 1u);
  EXPECT_EQ(snap.replies, 0u);
  EXPECT_EQ(snap.unmatched_replies, 1u);
  EXPECT_LT(snap.last_reply_t, 0.0);  // a late/unmatched reply does not refresh the "last reply" time
}

TEST(ServoStats, ServosAreIndependentAndMaxValuesTracked)
{
  ServoStats s(0.5);
  s.record_request(1, 0.0);
  s.record_reply(1, 0.01);
  s.record_request(1, 1.0);
  s.record_reply(1, 1.20);
  s.record_request(10, 0.0);
  const auto a = s.snapshot(1, 2.0);
  const auto g = s.snapshot(10, 2.0);
  EXPECT_NEAR(a.max_latency_s, 0.20, 1e-9);
  EXPECT_NEAR(a.max_period_s, 1.19, 1e-9);
  EXPECT_EQ(g.replies, 0u);
  EXPECT_EQ(g.misses, 1u);
  EXPECT_EQ(s.ids().size(), 2u);
}

TEST(ServoStats, UnrequestedReplyIsCountedSeparately)
{
  ServoStats s;
  s.record_reply(5, 1.0);
  const auto snap = s.snapshot(5, 1.0);
  EXPECT_EQ(snap.replies, 0u);
  EXPECT_EQ(snap.unmatched_replies, 1u);
}
