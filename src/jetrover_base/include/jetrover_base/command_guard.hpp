// 한글: 모터/팔 명령 입력 검증과 시작 시 파라미터 검증(순수 함수, ROS/하드웨어 불필요).
// Input guards for motor/arm commands and fail-fast parameter validation, as pure functions
// so the safety decisions can be unit-tested without ROS or hardware.
#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace jetrover_base
{

// What to do with an incoming /cmd_vel.
// 한글: 들어온 /cmd_vel을 어떻게 처리할지.
enum class CmdDecision
{
  Accept,
  RejectNonFinite,     // NaN/Inf: std::clamp does NOT sanitize NaN, so it must be rejected before clamping
  RejectStm32Silent,   // non-zero motion while the STM32 stream is silent: refuse (zero/stop is still allowed)
};

// Raw (pre-clamp) velocity. A zero command is always accepted (it is the safe direction), even
// while the STM32 is silent. A rejected command must not be cached, so a stale motion command can
// never come back to life when the stream recovers: only a fresh /cmd_vel moves the robot again.
// 한글: 0 명령은 침묵 중에도 항상 허용(정지 방향). 거부된 명령은 저장하지 않아서, STM32가 복구돼도 예전 명령이 되살아나지 않는다.
CmdDecision decide_cmd_vel(double vx, double vy, double wz, bool stm32_silent);

// All values finite (no NaN/Inf). Used for arm/command JointState positions.
// 한글: 모든 값이 유한한지(NaN/Inf 없음). arm/command 위치 검사에 쓴다.
bool all_finite(const std::vector<double> & values);

// Fail-fast parameter validation. Return an empty string when valid, else a description of the first
// problem. The node refuses to start on an error instead of "running roughly".
// 한글: 시작 시 파라미터 검증. 문제가 없으면 빈 문자열, 있으면 첫 문제 설명. 노드는 잘못된 설정으로 대충 돌지 않고 시작을 거부한다.
std::string validate_base_params(
  double wheelbase, double track_width, double wheel_diameter, double max_linear,
  double max_angular, double cmd_vel_timeout, double stm32_timeout);

struct ArmParams
{
  double servo_range_deg{240.0};
  double servo_ticks_range{1000.0};
  std::vector<double> center_ticks;
  std::vector<double> signs;
  std::vector<double> offsets_rad;
  std::vector<double> home_pose_rad;
  double max_step_rad{0.35};
  double move_duration_s{2.0};
  int64_t pulse_min{100};
  int64_t pulse_max{900};
};

std::string validate_arm_params(const ArmParams & p);

}  // namespace jetrover_base
