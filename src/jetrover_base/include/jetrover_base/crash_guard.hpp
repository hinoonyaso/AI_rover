#pragma once

#include <cstdint>
#include <vector>

namespace jetrover_base
{
namespace crash_guard
{

// Arms a last-resort stop: if the process dies from a crash signal (SEGV, ABRT,
// BUS, FPE, ILL) or a hangup/quit (SIGHUP, SIGQUIT), `frame` is written straight
// to `fd` from the signal handler, then the default action is re-raised.
// The STM32 keeps running its last motor command, so without this a crashed
// node leaves the wheels spinning. SIGKILL cannot be caught.
// `frame` must be at most kMaxFrame bytes.
constexpr std::size_t kMaxFrame = 64;

void arm(int fd, const std::vector<uint8_t> & frame);
void disarm();

}  // namespace crash_guard
}  // namespace jetrover_base
