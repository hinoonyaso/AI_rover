// 한글: 버스 서보 pulse(ticks) <-> 관절 각도(rad) 변환(순수 함수). base_node에서 분리해 단위시험이 가능하게 했다.
// Bus-servo ticks <-> joint radians as pure functions so they can be unit-tested without ROS.
#pragma once

#include <cstdint>

namespace jetrover_base
{

// Per-joint calibration: rad = (ticks - center) * rad_per_tick * sign + offset.
// 한글: 관절별 보정값. 각도 = (ticks - 중심) * 틱당 rad * 부호 + 오프셋.
struct ServoCal
{
  double center_ticks{500.0};
  double sign{1.0};
  double offset_rad{0.0};
  double rad_per_tick{0.0};
};

// rad per tick from the servo's mechanical range (e.g. 240 deg over 1000 ticks).
// 한글: 서보 가동 범위(예: 1000틱 = 240도)에서 틱당 rad를 구한다.
double rad_per_tick(double range_deg, double ticks_range);

double ticks_to_rad(const ServoCal & cal, double ticks);
double rad_to_ticks(const ServoCal & cal, double rad);

// Truncate toward zero (like the original static_cast<int64_t>) then clamp to [lo, hi].
// 한글: 0 방향 절삭 후 [lo, hi]로 제한(원래 코드와 같은 동작). 서보 안전 한계(arm_pulse_min/max)에 쓴다.
int64_t clamp_pulse(double raw, int64_t lo, int64_t hi);

// Servo dead band compensation: the servo stops a few pulses before the commanded position, so command
// `overshoot` pulses beyond the target in the travel direction (measured 2026-10-11, checklist 14), then clamp.
// No overshoot when the target equals the current position. 한글: 서보는 명령 몇 눈금 앞에서 멈추므로
// 이동 방향으로 `overshoot`만큼 더 명령한다(현재 위치와 같으면 그대로). 결과는 [lo, hi]로 제한.
int64_t deadband_overshoot(
  int64_t target, int64_t current, int64_t overshoot, int64_t lo,
  int64_t hi);

// Read-back trim after a move: compare where the servo ended with the wanted target. Corrects gravity sag and
// whatever dead band is left. `boost` (the servo's dead band overshoot) is added again in the correcting direction:
// a shift smaller than the dead band does not move the servo at all (measured 2026-10-11). Done = close enough; Retry = send `cmd`; GiveUp = too far off (blocked/not settled).
// 한글: 이동이 끝난 뒤 읽은 위치와 목표를 비교해 처짐/남은 데드밴드를 보정한다. Done=충분히 가까움,
// Retry=cmd를 다시 보냄, GiveUp=너무 멀어 막힌 것으로 보고 포기.
enum class TrimAction { Done, Retry, GiveUp };
struct TrimResult
{
  TrimAction action;
  int64_t cmd;
};
TrimResult feedback_trim(
  int64_t target, int64_t reading, int64_t last_cmd, int64_t threshold, int64_t max_error,
  int64_t boost, int64_t lo, int64_t hi);

// Relax after the trim ends: a servo resting a few pulses short of its last command keeps driving (hunting at the edge
// of its dead band) and heats up -- servo 1 went 43 -> 67 C in 3 min at the rest pose, and 69 -> 43 C in 1.5 min after
// its target was set to its own reading (2026-10-17). Returns the reading as the new command when the leftover
// |last_cmd - reading| is in [1, max_error]; -1 when nothing should be sent (already equal, or too far off = blocked).
// 한글: 보정이 끝난 뒤 마지막 명령과 실제 위치가 몇 펄스 어긋난 채 남으면 서보가 계속 힘을 써서(헌팅) 뜨거워진다
// (2026-10-17 servo 1: 3분에 43→67 ℃, 목표를 실제 위치로 다시 명령하자 1.5분에 69→43 ℃). 남은 차이가 1..max_error면
// 실제 위치를 새 명령으로 돌려준다. 같거나 너무 멀면(막힘) -1.
int64_t relax_command(int64_t last_cmd, int64_t reading, int64_t max_error);

}  // namespace jetrover_base
