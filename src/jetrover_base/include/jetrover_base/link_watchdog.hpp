// 한글: 호스트 쪽 안전 watchdog 로직(순수 클래스, 시간은 호출자가 초 단위로 넘긴다). base_node에서 분리해 단위시험이 가능하게 했다.
// Host-side safety watchdog as a pure class (caller passes time in seconds) so it can be unit-tested.
//   - STM32 heartbeat: the board streams IMU at ~100 Hz; silence > stm32_timeout means its firmware/power hung.
//   - cmd_vel timeout: while moving, no /cmd_vel for > cmd_vel_timeout stops the wheels.
// 한글: 정지 수단은 best-effort다(AGENTS.md). STM32 자체에는 명령 timeout이 없다.
#pragma once

namespace jetrover_base
{

class LinkWatchdog
{
public:
  enum class Action { None, StopStm32Silent, StopCmdTimeout };

  struct Result
  {
    Action action{Action::None};
    double silent_s{0.0};     // StopStm32Silent: how long the STM32 was silent
    bool was_moving{false};   // StopStm32Silent: moving flag before the stop (for the log)
  };

  LinkWatchdog() = default;
  LinkWatchdog(double cmd_vel_timeout_s, double stm32_timeout_s)
  : cmd_vel_timeout_(cmd_vel_timeout_s), stm32_timeout_(stm32_timeout_s) {}

  // Serial port (re)opened: restart the heartbeat clock and clear the silent latch.
  // 한글: 시리얼을 (다시) 열었을 때: heartbeat 시계를 다시 시작하고 침묵 상태를 해제한다.
  void on_open(double now_s)
  {
    last_rx_ = now_s;
    silent_ = false;
  }

  // Any valid frame from the STM32. Returns true if this ends a "silent" state (stream recovered).
  // 한글: STM32 프레임 수신. 침묵 상태였다가 복구되면 true.
  bool on_rx(double now_s)
  {
    last_rx_ = now_s;
    if (silent_) {
      silent_ = false;
      return true;
    }
    return false;
  }

  // /cmd_vel received; `moving` is whether it commands a non-zero velocity.
  // 한글: /cmd_vel 수신. moving은 0이 아닌 속도 명령인지 여부.
  void on_cmd(double now_s, bool moving)
  {
    last_cmd_ = now_s;
    moving_ = moving;
  }

  // The motors were just commanded to stop (any reason).
  // 한글: 모터에 정지를 보낸 직후 호출.
  void on_stopped() {moving_ = false;}

  // Called periodically (base_node: every 50 ms). Returns the stop action to take, if any.
  // The heartbeat only runs while the port is open and not already latched silent; the cmd_vel
  // timeout runs regardless (same behaviour as the original base_node code).
  // 한글: 주기 호출. heartbeat는 포트가 열려 있고 아직 침묵 상태가 아닐 때만 검사하고, cmd_vel timeout은 항상 검사한다.
  Result check(double now_s, bool serial_open)
  {
    Result r;
    if (serial_open && !silent_) {
      const double silent = now_s - last_rx_;
      if (silent > stm32_timeout_) {
        silent_ = true;
        r.action = Action::StopStm32Silent;
        r.silent_s = silent;
        r.was_moving = moving_;
        moving_ = false;
        return r;
      }
    }
    if (moving_ && (now_s - last_cmd_) > cmd_vel_timeout_) {
      moving_ = false;
      r.action = Action::StopCmdTimeout;
    }
    return r;
  }

  bool stm32_silent() const {return silent_;}
  bool moving() const {return moving_;}
  double cmd_vel_timeout() const {return cmd_vel_timeout_;}

private:
  double cmd_vel_timeout_{0.5};
  double stm32_timeout_{1.0};
  double last_rx_{0.0};
  double last_cmd_{0.0};
  bool moving_{false};
  bool silent_{false};
};

}  // namespace jetrover_base
