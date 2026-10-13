// 한글: GraspStateMachine을 base_node에 붙이는 순수 어댑터(ROS 없음). 서보 응답(위치·온도)과 "들어 올렸는가" 플래그를 보관하고,
//       상태 기계를 한 틱 돌려 출력을 주며, 팔/그리퍼 명령이 지금 허용되는지(R6 표)를 한곳에서 판정한다.
//       base_node는 이 클래스만 호출하고, 허용 판정을 흩어 놓지 않는다.
// Pure adapter that connects GraspStateMachine to base_node (no ROS). It keeps the latest servo replies (position,
// temperature) and the "object lifted" flag, runs the state machine one tick, and decides in ONE place whether an arm or
// gripper command is allowed right now (the R6 table), so the guards are not scattered over base_node.
#pragma once

#include <cstdint>
#include <vector>

#include "jetrover_base/grasp_state_machine.hpp"

namespace jetrover_base
{

// Where a command comes from. Manual = a person / a script (arm/command); Automated = MoveIt trajectories
// (arm/command_timed) and the home ramp. 한글: 사람이 낸 명령인가, 자동(궤적/홈 이동)인가.
enum class CommandSource { Manual, Automated };

// 로그/피드백용 이름 / names for logs and feedback
const char * grasp_state_name(GraspState s);
const char * grasp_fail_name(GraspFail f);

class GraspController
{
public:
  static constexpr uint8_t kGripperId = 10;

  explicit GraspController(const GraspProfile & p = GraspProfile())
  : sm_(p) {}

  bool start(double now)
  {
    // 시작 전에 받아 둔 위치·온도는 낡았을 수 있다 → 버리고 Check가 새 응답을 기다리게 한다(L1에서 82 ℃인데 5 s 전 40 ℃ 값으로
    // 시작하던 결함). A reading/temperature taken before the start can be stale: drop them so CHECK waits for fresh replies.
    have_position_ = false;
    have_temp_ = false;
    started_at_ = now;
    return sm_.start(now);
  }
  void cancel() {sm_.request_cancel();}
  bool release(double now) {return sm_.release(now);}
  bool reset() {return sm_.reset();}

  void on_position(int pulse, double reading_time)
  {
    position_ = pulse;
    position_time_ = reading_time;
    have_position_ = true;
  }
  void on_temp(double temp_c, double t)
  {
    temp_ = temp_c;
    temp_time_ = t;
    have_temp_ = true;
  }
  // -1 unknown, 0 no, 1 yes (std_msgs/Bool topic arm/object_lifted, and later a joint-pose check)
  void set_caller_lifted(int v) {arm_.caller_lifted = v;}
  void set_pose_lifted(int v) {arm_.pose_lifted = v;}

  // One state machine tick with the latest data. `temp_max_age_s`: an older temperature counts as missing.
  GraspOutput tick(double now, double temp_max_age_s = 5.0);
  const GraspOutput & last() const {return last_;}
  int last_position() const {return have_position_ ? position_ : -1;}
  double last_temp() const {return have_temp_ ? temp_ : -1.0;}
  double elapsed(double now) const {return now - started_at_;}
  GraspState state() const {return sm_.state();}
  const GraspProfile & profile() const {return sm_.profile();}

  // The ONE place that answers "may this command go out now?" (R6 table, D5). `servo_ids` are the servos the command
  // moves. Returns an empty string if allowed, else the reason.
  // 한글: 이 명령을 지금 보내도 되는가. 허용이면 빈 문자열, 아니면 거절 이유.
  std::string deny_reason(const std::vector<uint8_t> & servo_ids, CommandSource source) const;
  // Torque release / home ramp style commands that would drop or disturb the object: only in IDLE.
  std::string deny_reason_global() const;

private:
  GraspStateMachine sm_;
  GraspOutput last_;
  ArmContext arm_;
  int position_{0};
  double position_time_{0.0};
  bool have_position_{false};
  double temp_{0.0};
  double temp_time_{0.0};
  bool have_temp_{false};
  double started_at_{0.0};
};

}  // namespace jetrover_base
