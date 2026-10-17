#include "jetrover_base/servo_stats.hpp"

#include <algorithm>

namespace jetrover_base
{

void ServoStats::expire(Entry & e, double now)
{
  while (!e.outstanding.empty() && now - e.outstanding.front() > miss_timeout_s_) {
    e.outstanding.pop_front();
    e.s.misses++;
  }
}

void ServoStats::record_request(uint8_t id, double t)
{
  auto & e = entries_[id];
  e.s.id = id;
  expire(e, t);
  e.outstanding.push_back(t);
  e.s.requests++;
}

void ServoStats::record_reply(uint8_t id, double t, bool ok)
{
  auto & e = entries_[id];
  e.s.id = id;
  expire(e, t);
  if (e.outstanding.empty()) {
    e.s.unmatched_replies++;
    return;
  }
  // The bus answers in order: a reply belongs to the NEWEST outstanding request, every older one was lost.
  // (Matching the oldest one would inflate the latency of everything after a single loss.)
  // 한글: 응답은 순서대로 온다 → 가장 최근 요청과 짝짓고, 더 오래된 요청은 유실로 센다.
  const double req_t = e.outstanding.back();
  e.s.misses += e.outstanding.size() - 1;
  e.outstanding.clear();
  if (!ok) {
    e.s.failed_replies++;
    return;
  }
  const double latency = t - req_t;
  e.s.replies++;
  e.latency_sum += latency;
  e.s.max_latency_s = std::max(e.s.max_latency_s, latency);
  if (e.s.last_reply_t >= 0.0) {
    const double period = t - e.s.last_reply_t;
    e.period_sum += period;
    e.period_n++;
    e.s.max_period_s = std::max(e.s.max_period_s, period);
  }
  e.s.last_reply_t = t;
}

void ServoStats::record_invalid(uint8_t id, double t)
{
  auto & e = entries_[id];
  e.s.id = id;
  expire(e, t);
  if (e.outstanding.empty()) {
    e.s.unmatched_replies++;
    return;
  }
  e.s.misses += e.outstanding.size() - 1;
  e.outstanding.clear();
  e.s.invalid_replies++;
}

ServoStatsSnapshot ServoStats::snapshot(uint8_t id, double now)
{
  auto & e = entries_[id];
  e.s.id = id;
  expire(e, now);
  ServoStatsSnapshot out = e.s;
  out.mean_latency_s = e.s.replies ? e.latency_sum / static_cast<double>(e.s.replies) : 0.0;
  out.mean_period_s = e.period_n ? e.period_sum / static_cast<double>(e.period_n) : 0.0;
  return out;
}

std::vector<uint8_t> ServoStats::ids() const
{
  std::vector<uint8_t> out;
  for (const auto & kv : entries_) {
    out.push_back(kv.first);
  }
  return out;
}

void ServoStats::reset()
{
  entries_.clear();
}

}  // namespace jetrover_base
