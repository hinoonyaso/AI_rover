#include "jetrover_base/grasp_controller.hpp"

#include <algorithm>
#include <string>

namespace jetrover_base
{

const char * grasp_state_name(GraspState s)
{
  switch (s) {
    case GraspState::Idle: return "Idle";
    case GraspState::Check: return "Check";
    case GraspState::Closing: return "Closing";
    case GraspState::Squeeze: return "Squeeze";
    case GraspState::Holding: return "Holding";
    case GraspState::Releasing: return "Releasing";
    case GraspState::Failed: return "Failed";
  }
  return "Unknown";
}

const char * grasp_fail_name(GraspFail f)
{
  switch (f) {
    case GraspFail::None: return "";
    case GraspFail::TempHigh: return "TempHigh";
    case GraspFail::BadStart: return "BadStart";
    case GraspFail::NoContact: return "NoContact";
    case GraspFail::OutsideWindow: return "OutsideWindow";
    case GraspFail::NoReading: return "NoReading";
    case GraspFail::Timeout: return "Timeout";
    case GraspFail::Cancelled: return "Cancelled";
    case GraspFail::HoldNotStable: return "HoldNotStable";
  }
  return "Unknown";
}

GraspOutput GraspController::tick(double now, double temp_max_age_s)
{
  GraspInput in;
  in.now = now;
  in.has_reading = have_position_;
  in.position = position_;
  in.reading_time = position_time_;
  in.has_temp = have_temp_ && now - temp_time_ <= temp_max_age_s;
  in.temp_c = temp_;
  in.arm = arm_;
  last_ = sm_.update(in);
  return last_;
}

std::string GraspController::deny_reason(
  const std::vector<uint8_t> & ids,
  CommandSource source) const
{
  const GraspState s = sm_.state();
  if (s == GraspState::Idle) {
    return "";   // 파지 중이 아니면 기존 동작 그대로 / nothing grasping: unchanged behaviour
  }
  const bool gripper = std::find(ids.begin(), ids.end(), kGripperId) != ids.end();
  const bool arm = std::any_of(ids.begin(), ids.end(), [](uint8_t id) {return id != kGripperId;});
  if (gripper) {
    // The grasp owns ID 10 in every state except IDLE, until an explicit release (D5).
    return "gripper is owned by the grasp (" + last_.note + "); use arm/release";
  }
  if (arm) {
    switch (GraspStateMachine::arm_motion_for(s, last_.arm_motion == ArmMotion::RecoveryOnly)) {
      case ArmMotion::Allowed:
        return "";
      case ArmMotion::RecoveryOnly:
        // A fault in the air: no automatic motion, but a person may move the arm to a safe place.
        return source ==
               CommandSource::Manual ? "" :
               "grasp fault in the air: only manual recovery moves are allowed";
      case ArmMotion::Denied:
        return "arm motion denied while the grasp is in this state";
    }
  }
  return "";
}

std::string GraspController::deny_reason_global() const
{
  return sm_.state() ==
         GraspState::Idle ? "" :
         "a grasp is active: torque release / home move would drop or disturb the object";
}

}  // namespace jetrover_base
