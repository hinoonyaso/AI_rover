// 한글: 버스 서보 읽기 요청/응답 통계(순수 로직, 단위시험 대상). 서보별로 요청 시각과 실제 응답 도착 시각을 맞춰
//       응답 수·누락 수·요청→응답 지연·응답 간격을 센다. /joint_states 헤더 시각(재발행되는 캐시 값)을 쓰지 않는다.
// Per-servo read request/reply bookkeeping (pure, unit-tested). Matches each request time with the time its reply frame
// really arrived, so reply counts, misses, request->reply latency and reply period are measured on the wire, not
// inferred from the (re-published, cached) /joint_states header. prd/arm-control-path.md R1/R7.
#pragma once

#include <cstdint>
#include <deque>
#include <map>
#include <vector>

namespace jetrover_base
{

struct ServoStatsSnapshot
{
  uint8_t id{0};
  uint64_t requests{0};          // read requests sent
  uint64_t replies{0};           // successful reply frames matched to a request
  uint64_t failed_replies{0};    // frames the STM32 sent to say the servo did not answer (success != 0)
  uint64_t misses{0};            // requests that never got any frame (lost, or older than a newer matched reply)
  uint64_t unmatched_replies{0}; // reply frames with no outstanding request (late after a miss, or foreign)
  double last_reply_t{-1.0};     // time of the last reply frame (same clock as the inputs), -1 if none
  double mean_latency_s{0.0};
  double max_latency_s{0.0};
  double mean_period_s{0.0};     // mean time between consecutive replies
  double max_period_s{0.0};
};

class ServoStats
{
public:
  explicit ServoStats(double miss_timeout_s = 0.5)
  : miss_timeout_s_(miss_timeout_s) {}

  void record_request(uint8_t id, double t);
  // ok=false: the STM32 answered with a failure frame (it retried and the servo stayed silent). It still ends the request
  // (so it is not a lost frame) but is not a successful reading and does not refresh last_reply_t.
  // 한글: ok=false는 STM32가 "서보 무응답"을 알려 준 프레임 — 프레임 유실(misses)과 구분한다.
  void record_reply(uint8_t id, double t, bool ok = true);
  // `now` expires outstanding requests older than the miss timeout before counting.
  ServoStatsSnapshot snapshot(uint8_t id, double now);
  std::vector<uint8_t> ids() const;
  void reset();

private:
  struct Entry
  {
    ServoStatsSnapshot s;
    std::deque<double> outstanding;
    double latency_sum{0.0};
    double period_sum{0.0};
    uint64_t period_n{0};
  };
  void expire(Entry & e, double now);

  double miss_timeout_s_;
  std::map<uint8_t, Entry> entries_;
};

}  // namespace jetrover_base
