#include "jetrover_base/grasp_state_machine.hpp"

#include <algorithm>
#include <cstdlib>
#include <string>

namespace jetrover_base
{

bool is_lifted(const ArmContext & c)
{
  // Any "yes" or any "unknown" counts as lifted; only two explicit "no" mean the object is near the ground.
  // 한글: 하나라도 예이거나 모르면 들어 올린 것으로 본다(열지 않는 쪽). 둘 다 명시적으로 아니오일 때만 지면 근처.
  if (c.caller_lifted == 1 || c.pose_lifted == 1) {
    return true;
  }
  return !(c.caller_lifted == 0 && c.pose_lifted == 0);
}

ArmMotion GraspStateMachine::arm_motion_for(GraspState s, bool fault_in_air)
{
  switch (s) {
    case GraspState::Idle:
      return ArmMotion::Allowed;
    case GraspState::Holding:
      return fault_in_air ? ArmMotion::RecoveryOnly : ArmMotion::Allowed;
    default:
      return ArmMotion::Denied;   // CHECK / CLOSING / SQUEEZE / RELEASING / FAILED (R6 table)
  }
}

GraspStateMachine::GraspStateMachine(const GraspProfile & p)
: p_(p) {}

bool GraspStateMachine::start(double now)
{
  if (state_ != GraspState::Idle) {
    return false;
  }
  fail_ = GraspFail::None;
  note_ = "check";
  pending_ = GraspCommand();
  sub_ = Sub::Issue;
  t_start_ = now;
  t_cmd_ = now;
  t_last_reading_ = now;
  open_start_ = -1;
  cur_ = target_ = confirm_first_ = 0;
  steps_ = 0;
  contact_ = -1;
  approach_target_ = -1;
  squeeze_target_ = -1;
  cancel_ = false;
  success_pending_ = false;
  fault_in_air_ = false;
  needs_user_ = false;
  got_temp_ = false;
  obs_n_ = 0;
  state_ = GraspState::Check;
  return true;
}

void GraspStateMachine::request_cancel()
{
  if (state_ == GraspState::Check || state_ == GraspState::Closing ||
    state_ == GraspState::Squeeze ||
    state_ == GraspState::Holding)
  {
    cancel_ = true;
  }
}

bool GraspStateMachine::release(double now)
{
  if (state_ != GraspState::Holding || open_start_ < 0) {
    return false;
  }
  pending_ = GraspCommand{true, open_start_, p_.release_ms};
  release_done_ = now + p_.release_ms / 1000.0 + p_.settle_s;
  state_ = GraspState::Releasing;
  cancel_ = false;
  note_ = "release requested";
  return true;
}

bool GraspStateMachine::reset()
{
  if (state_ != GraspState::Failed) {
    return false;
  }
  state_ = GraspState::Idle;
  fail_ = GraspFail::None;
  note_ = "reset";
  contact_ = -1;
  needs_user_ = false;
  fault_in_air_ = false;
  return true;
}

GraspOutput GraspStateMachine::make_output() const
{
  GraspOutput o;
  o.state = state_;
  o.fail = fail_;
  o.gripper_owned = !external_gripper_command_allowed(state_);
  o.arm_motion = arm_motion_for(state_, fault_in_air_);
  o.needs_user = needs_user_;
  o.contact = contact_;
  o.note = note_;
  return o;
}

void GraspStateMachine::fail(GraspFail reason, Action action, double now, const std::string & note)
{
  (void)now;
  state_ = GraspState::Failed;
  fail_ = reason;
  note_ = note;
  // Nothing moved yet (no start position / contact) -> no command. Otherwise relax to the contact or reopen to the start.
  // 한글: 아직 움직이지 않았으면 명령 없음. 접촉 위치까지 풀거나(RelaxToContact) 처음 위치로 연다(OpenToStart).
  if (action == Action::RelaxToContact && contact_ >= 0) {
    pending_ = GraspCommand{true, contact_, p_.release_ms};
  } else if (open_start_ >= 0 && steps_ > 0) {
    pending_ = GraspCommand{true, open_start_, p_.release_ms};
  } else {
    pending_ = GraspCommand();
  }
}

void GraspStateMachine::issue_step(double now, GraspOutput & out)
{
  const int limit = p_.closed_end - p_.closed_margin;
  target_ = cur_ + p_.step;
  if (target_ > limit || steps_ >= p_.max_steps) {
    fail(GraspFail::NoContact, Action::OpenToStart, now, "no contact before the closed end");
    return;
  }
  out.command = GraspCommand{true, target_, p_.step_ms};
  t_cmd_ = now;
  sub_ = Sub::WaitEval;
  ++steps_;
}

void GraspStateMachine::enter_squeeze(double now, GraspOutput & out)
{
  // Never squeeze beyond the closed end (A6). 한글: 닫힘 끝 너머로 조이지 않는다.
  squeeze_target_ = std::min(contact_ + p_.squeeze, p_.closed_end - p_.closed_margin);
  out.command = GraspCommand{true, squeeze_target_, p_.squeeze_ms};
  t_cmd_ = now;
  obs_start_ = now + p_.squeeze_ms / 1000.0 + p_.settle_s;
  obs_n_ = 0;
  state_ = GraspState::Squeeze;
  note_ = "squeeze";
}

void GraspStateMachine::hold_fault(
  GraspFail reason, const ArmContext & arm, double now, const std::string & note, GraspOutput & out)
{
  if (fault_in_air_) {
    return;   // already latched: stay where we are until an explicit release
  }
  fail_ = reason;
  note_ = note;
  if (is_lifted(arm)) {
    // 공중: 열지 않는다. 이동 중지(복구 이동만), 조임 유지, 사용자 개입.
    // In the air: do NOT open. Stop automatic motion (recovery moves only), keep the squeeze, ask for a person.
    fault_in_air_ = true;
    needs_user_ = true;
    return;
  }
  // Near the ground: opening is safe.  한글: 지면 근처에서는 열어도 안전하다.
  out.command = GraspCommand{true, open_start_, p_.release_ms};
  release_done_ = now + p_.release_ms / 1000.0 + p_.settle_s;
  state_ = GraspState::Releasing;
}

GraspOutput GraspStateMachine::update(const GraspInput & in)
{
  GraspOutput out;
  if (in.has_reading) {
    t_last_reading_ = std::max(t_last_reading_, in.reading_time);
  }
  const bool temp_high = in.has_temp && in.temp_c >= p_.temp_limit_c;
  const bool active = state_ == GraspState::Check || state_ == GraspState::Closing ||
    state_ == GraspState::Squeeze;

  if (active) {
    // 공통 중단 조건 / common stop conditions (cancel > temperature > timeout > communication loss)
    const Action relax = contact_ >= 0 ? Action::RelaxToContact : Action::OpenToStart;
    if (cancel_) {
      cancel_ = false;
      fail(GraspFail::Cancelled, relax, in.now, "cancelled");
    } else if (temp_high) {
      fail(GraspFail::TempHigh, relax, in.now, "gripper temperature at or above the limit");
    } else if (state_ == GraspState::Check && in.now - t_start_ > p_.check_timeout_s &&
      (open_start_ < 0 || !got_temp_))
    {
      fail(GraspFail::NoReading, Action::OpenToStart, in.now,
          "no position or temperature reading at the start");
    } else if (in.now - t_start_ > p_.timeout_s) {
      fail(GraspFail::Timeout, relax, in.now, "grasp took too long");
    } else if (state_ != GraspState::Check && in.now - t_last_reading_ > p_.comm_loss_s) {
      fail(GraspFail::NoReading, relax, in.now, "no fresh position reading");
    }
  }

  if (state_ == GraspState::Check) {
    if (in.has_temp && !temp_high) {
      got_temp_ = true;
    }
    if (open_start_ < 0 && in.has_reading) {
      open_start_ = in.position;
      if (open_start_ > p_.open_start_max) {
        fail(GraspFail::BadStart, Action::OpenToStart, in.now, "gripper is nearly closed already");
      }
    }
    if (state_ == GraspState::Check && open_start_ >= 0 && got_temp_) {
      cur_ = open_start_;
      state_ = GraspState::Closing;
      sub_ = Sub::Issue;
      note_ = "closing";
      const int approach_to = p_.contact_lo - p_.approach_margin;
      if (p_.approach_margin >= 0 && approach_to > open_start_ + p_.step) {
        // 빠른 접근: 한 번에 이동하고 진행을 지켜본다 / fast approach: one move, progress watched
        approach_target_ = approach_to;
        target_ = approach_to;
        out.command = GraspCommand{true, approach_to, p_.approach_ms};
        t_cmd_ = in.now;
        prog_pos_ = open_start_;
        prog_t_ = in.now;
        // 스텝으로 센다: fail()은 steps_ > 0일 때만 시작 위치로 다시 연다(막힌 서보가 계속 누르지 않게)
        // count it as a step: fail() reopens only when steps_ > 0 (a stalled servo must not keep squeezing)
        ++steps_;
        sub_ = Sub::Approach;
        note_ = "approaching";
      } else {
        issue_step(in.now, out);
      }
    }
  } else if (state_ == GraspState::Closing && sub_ == Sub::Approach) {
    // 막힘 = stall_s 동안 2펄스 미만 진행인데 목표에 못 미침 → 이 프로파일보다 큰 물체로 보고 실패·열기.
    // Blocked = under 2 pulses of progress for stall_s while short of the target: larger object than the
    // profile expects -> fail and open (a stalled servo squeezes hard, so do not wait for the move to end).
    if (fresh_after(in, t_cmd_)) {
      if (in.position >= prog_pos_ + 2) {
        prog_pos_ = in.position;
        prog_t_ = in.reading_time;
      }
      const bool short_of_target = approach_target_ - in.position > p_.dead_band;
      const bool done = in.reading_time >= t_cmd_ + p_.approach_ms / 1000.0 + p_.settle_s;
      if (short_of_target &&
        (done || (in.now - t_cmd_ >= p_.stall_s && in.now - prog_t_ >= p_.stall_s)))
      {
        contact_ = in.position;
        fail(GraspFail::OutsideWindow, Action::OpenToStart, in.now,
            "blocked during the fast approach (object larger than the profile?)");
      } else if (done) {
        cur_ = in.position;
        note_ = "closing";
        issue_step(in.now, out);
      }
    }
  } else if (state_ == GraspState::Closing) {
    const double eval_after = t_cmd_ + p_.step_ms / 1000.0 + p_.settle_s;
    if (sub_ == Sub::WaitEval && fresh_after(in, eval_after)) {
      const int lag = target_ - in.position;
      cur_ = in.position;
      if (lag > p_.dead_band) {          // candidate: send the same target again and see whether it gives
        confirm_first_ = in.position;
        out.command = GraspCommand{true, target_, p_.step_ms};
        t_cmd_ = in.now;
        sub_ = Sub::Confirm;
      } else {
        issue_step(in.now, out);
      }
    } else if (sub_ == Sub::Confirm && fresh_after(in, eval_after)) {
      if (std::abs(in.position - confirm_first_) <= 1) {
        contact_ = in.position;
        if (contact_ >= p_.contact_lo && contact_ <= p_.contact_hi) {
          enter_squeeze(in.now, out);
        } else {
          fail(GraspFail::OutsideWindow, Action::OpenToStart, in.now,
              "contact outside the accepted window");
        }
      } else {
        cur_ = in.position;
        issue_step(in.now, out);
      }
    }
  } else if (state_ == GraspState::Squeeze) {
    if (fresh_after(in, obs_start_)) {
      if (obs_n_ == 0) {
        obs_min_ = obs_max_ = in.position;
      } else {
        obs_min_ = std::min(obs_min_, in.position);
        obs_max_ = std::max(obs_max_, in.position);
      }
      ++obs_n_;
    }
    if (in.now >= obs_start_ + p_.hold_s) {
      if (obs_n_ == 0) {
        fail(GraspFail::NoReading, Action::RelaxToContact, in.now,
            "no reading while holding the squeeze");
      } else if (obs_max_ - obs_min_ > p_.hold_tol) {
        // 실제 흔들림을 남긴다(hold_tol 확정 근거로 다시 볼 수 있게) / keep the measured spread for later review
        fail(GraspFail::HoldNotStable, Action::RelaxToContact, in.now,
            "the squeeze did not hold still (spread " + std::to_string(obs_max_ - obs_min_) +
            " > " + std::to_string(p_.hold_tol) + " pulses)");
      } else {
        state_ = GraspState::Holding;
        success_pending_ = true;
        note_ = "grasp established";
      }
    }
  } else if (state_ == GraspState::Holding) {
    if (cancel_) {
      cancel_ = false;
      hold_fault(GraspFail::Cancelled, in.arm, in.now, "cancel while holding", out);
    } else if (temp_high) {
      hold_fault(GraspFail::TempHigh, in.arm, in.now, "temperature limit while holding", out);
    } else if (in.now - t_last_reading_ > p_.comm_loss_s) {
      hold_fault(GraspFail::NoReading, in.arm, in.now, "communication loss while holding", out);
    }
  } else if (state_ == GraspState::Releasing) {
    if (in.now >= release_done_) {
      state_ = GraspState::Idle;
      note_ = "released";
      contact_ = -1;
      needs_user_ = false;
      fault_in_air_ = false;
    }
  }

  // 대기 중이던 명령(release(), fail())을 이번 출력에 싣는다 / flush a command queued by release() or fail()
  GraspOutput result = make_output();
  result.command = out.command.valid ? out.command : pending_;
  pending_ = GraspCommand();
  if (state_ == GraspState::Holding && fault_in_air_) {
    result.needs_user = true;
  }
  if (success_pending_) {
    result.success_event = true;
    success_pending_ = false;
  }
  // The Releasing branch above may have switched to IDLE: report the final state, then forget the reason.
  if (state_ == GraspState::Idle) {
    fail_ = GraspFail::None;
  }
  return result;
}

}  // namespace jetrover_base
