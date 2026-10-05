// 한글: 노드가 비정상 종료해도 바퀴를 세우기 위한 마지막 안전장치. STM32에는 호스트 명령 timeout이 없어서(펌웨어 개선 전) 필요하다.
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
// 한글: 시그널 핸들러에서 쓸 정지 프레임의 최대 길이(고정 배열, 동적 할당 금지).
constexpr std::size_t kMaxFrame = 64;

// 한글: 정지 프레임과 fd를 등록하고 시그널 핸들러를 설치한다(최초 1회).
void arm(int fd, const std::vector<uint8_t> & frame);
// 한글: 정상 종료 경로에서 해제한다(이후 시그널은 일반 처리).
void disarm();

}  // namespace crash_guard
}  // namespace jetrover_base
