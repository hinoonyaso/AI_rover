#include "jetrover_base/crash_guard.hpp"

#include <signal.h>
#include <unistd.h>

#include <algorithm>
#include <cstring>

namespace jetrover_base
{
namespace crash_guard
{

namespace
{

// Only async-signal-safe state: plain arrays and integers, no allocation or locks.
// 한글: async-signal-safe 상태만 쓴다: 단순 배열/정수, 할당·락 없음.
volatile sig_atomic_t g_fd = -1;
uint8_t g_frame[kMaxFrame];
volatile sig_atomic_t g_len = 0;

// 한글: 잡을 치명적/종료 시그널 목록(SIGKILL은 잡을 수 없다).
constexpr int kSignals[] = {SIGSEGV, SIGABRT, SIGBUS, SIGFPE, SIGILL, SIGHUP, SIGQUIT};

// 한글: 정지 프레임을 fd에 두 번 직접 write(유실 대비)한 뒤 기본 동작을 다시 발생시켜 core dump/종료가 정상적으로 일어나게 한다.
void handler(int sig)
{
  const int fd = g_fd;
  if (fd >= 0) {
    for (int i = 0; i < 2; ++i) {
      const ssize_t n = ::write(fd, g_frame, static_cast<std::size_t>(g_len));
      (void)n;
    }
  }

  signal(sig, SIG_DFL);
  raise(sig);
}

void install_handlers()
{
  static bool installed = false;
  if (installed) {
    return;
  }
  installed = true;

  struct sigaction sa;
  std::memset(&sa, 0, sizeof(sa));
  sa.sa_handler = handler;
  sigemptyset(&sa.sa_mask);
  // 한글: 핸들러 안에서 같은 시그널이 다시 와도 막지 않는다(재발생 raise를 위해).
  sa.sa_flags = SA_NODEFER;
  for (const int sig : kSignals) {
    sigaction(sig, &sa, nullptr);
  }
}

}  // namespace

void arm(int fd, const std::vector<uint8_t> & frame)
{
  disarm();
  const std::size_t len = std::min(frame.size(), kMaxFrame);
  std::memcpy(g_frame, frame.data(), len);
  g_len = static_cast<sig_atomic_t>(len);
  g_fd = fd;
  install_handlers();
}

void disarm()
{
  g_fd = -1;
}

}  // namespace crash_guard
}  // namespace jetrover_base
