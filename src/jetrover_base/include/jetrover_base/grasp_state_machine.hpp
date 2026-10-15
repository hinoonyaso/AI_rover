// 한글: 그리퍼(ID 10) 접촉 파지 상태 기계(순수 로직, 하드웨어·ROS 없이 시험). 시간·읽기값·온도·팔 상황을 입력으로 받고
//       그리퍼 명령과 "누가 무엇을 제어해도 되는가"를 출력한다. 서보는 힘을 알려 주지 않으므로 위치 정체만으로 접촉을 판단하며,
//       그 결과가 기대한 물체인지는 접촉 위치 창과 조임 유지 확인으로 따로 판정한다(prd/arm-control-path.md R3~R6, D5~D8).
//       base_node 연결과 Action/서비스는 T6에서 한다 — 이 파일은 ROS에 의존하지 않는다.
// Gripper (ID 10) contact-grasp state machine: pure logic, no hardware, no ROS. Inputs are time, the position reading,
// the temperature and the arm situation; outputs are gripper commands and who may control what. The servo reports no
// force, so contact is only "the position stopped following the command"; whether it is the expected object is decided
// separately by a contact-position window and a hold check. Wiring into base_node / Action / service is T6.
#pragma once

#include <string>

namespace jetrover_base
{

// 상태 / states. HOLDING keeps the gripper owned after a successful grasp until an explicit release (D5).
enum class GraspState { Idle, Check, Closing, Squeeze, Holding, Releasing, Failed };

enum class GraspFail
{
  None, TempHigh, BadStart, NoContact, OutsideWindow, NoReading, Timeout, Cancelled, HoldNotStable
};

// 호출자/관절 자세가 알려 주는 "들어 올렸는가". -1 모름, 0 아니오, 1 예. 하나라도 예이거나 모르면 들어 올린 것으로 본다(열지 않는 쪽).
// Lifted = caller flag and arm-pose check; unknown or disagreeing counts as lifted (never open an object in the air).
struct ArmContext
{
  int caller_lifted{-1};
  int pose_lifted{-1};
};
bool is_lifted(const ArmContext & c);

// 프로파일 / profile. cube3cm is the ONLY validated one (T3, 2026-10-11); +16 is NOT a default for other objects.
struct GraspProfile
{
  std::string name{"cube3cm"};
  int step{12};                 // pulses per closing step (6..16, T3)
  int dead_band{8};             // lag (command - reading) above this is a contact candidate (servo dead band 3-4)
  int contact_lo{505};          // window confirmed 2026-10-15 (straight cube 520..535 in ~43 closings)
  int contact_hi{545};
  int squeeze{16};              // pulses beyond the contact (3 cm cube only)
  int closed_end{693};          // the jaws touch each other (measured 2026-10-11)
  int closed_margin{6};         // never command closer than closed_end - margin
  int open_start_max{450};      // refuse to start from a nearly closed gripper
  int step_ms{250};
  // 빠른 접근(2026-10-15): 접촉 창 아래 contact_lo - approach_margin까지 한 번에 이동한 뒤 정밀 스텝. 음수면 끔(기존 동작).
  // 이 프로파일의 물체는 그 전에 닿지 않는다는 가정 — 막히면(멈춤) 바로 실패하고 연다. base.yaml에서 켠다.
  // Fast approach: one move to contact_lo - approach_margin, then the fine steps. Negative = off (old behaviour).
  // Assumes the profile's object is not touched before that point; a stall there fails and opens at once.
  int approach_margin{-1};
  int approach_ms{800};         // duration of the approach move
  double stall_s{0.3};          // during the approach: < 2 pulses of progress for this long = blocked
  int squeeze_ms{400};
  int release_ms{1500};         // slow opening (as in the T3 tool)
  double settle_s{0.2};         // extra wait after a move before its reading counts
  double hold_s{2.0};           // observe the squeeze for this long ...
  int hold_tol{4};              // ... within this many pulses (stable grasps moved up to 4; 3 failed 1 of ~44 real)
  double timeout_s{30.0};       // approach off (code default): stepwise closing 19-21 s; base.yaml uses 20 s with it on
  double comm_loss_s{1.5};      // no fresh reading for this long = communication loss (T1: silent gaps up to 0.9 s at 20 Hz)
  double check_timeout_s{2.0};  // CHECK waits this long for the first position and temperature
  double temp_limit_c{80.0};    // above this: refuse / stop (servo cuts out itself at 85 C)
  int max_steps{80};
};

struct GraspInput
{
  double now{0.0};              // monotonic seconds
  bool has_reading{false};      // a position reading exists
  int position{0};
  double reading_time{0.0};     // when that reply frame arrived (same clock as now)
  bool has_temp{false};
  double temp_c{0.0};
  ArmContext arm;
};

struct GraspCommand
{
  bool valid{false};
  int pulse{0};
  int ms{0};
};

// 팔 관절 이동 허용 / arm joint motion: Allowed, Denied, or RecoveryOnly (a fault in the air: only an explicit move to a safe
// place is acceptable, no automatic motion).
enum class ArmMotion { Allowed, Denied, RecoveryOnly };

struct GraspOutput
{
  GraspState state{GraspState::Idle};
  GraspFail fail{GraspFail::None};
  GraspCommand command;               // at most one gripper command per update
  bool gripper_owned{false};          // true: other ID 10 commands must be refused
  ArmMotion arm_motion{ArmMotion::Allowed};
  bool success_event{false};          // true for exactly one update: the grasp is established (HOLDING reached)
  bool needs_user{false};             // a fault in the air: nothing was opened, a person / a safe place is needed
  int contact{-1};                    // contact position once found
  std::string note;                   // short reason for logs / feedback
};

class GraspStateMachine
{
public:
  explicit GraspStateMachine(const GraspProfile & p = GraspProfile());

  // Start a grasp. false = refused (not IDLE).  한글: IDLE이 아니면 거부.
  bool start(double now);
  // Cancel: during CHECK/CLOSING/SQUEEZE -> FAILED (relax), in HOLDING a fault (see fault policy), otherwise ignored.
  void request_cancel();
  // Explicit release: only in HOLDING (returns false otherwise). Opening ends in IDLE = ownership returned.
  bool release(double now);
  // Leave FAILED after the failure was reported. false if not FAILED.
  bool reset();

  GraspOutput update(const GraspInput & in);

  GraspState state() const {return state_;}
  const GraspProfile & profile() const {return p_;}

  // 누가 ID 10을 쓸 수 있는가 — IDLE일 때만 외부 명령 허용 / External gripper commands are allowed only in IDLE.
  static bool external_gripper_command_allowed(GraspState s) {return s == GraspState::Idle;}
  // 상태별 팔 관절 이동 허용(R6 표) / arm motion per state (R6 table). `fault_in_air` selects RecoveryOnly in HOLDING.
  static ArmMotion arm_motion_for(GraspState s, bool fault_in_air);

private:
  enum class Sub { Issue, Approach, WaitEval, Confirm };
  enum class Action { OpenToStart, RelaxToContact };

  GraspOutput make_output() const;
  void fail(GraspFail reason, Action action, double now, const std::string & note);
  void issue_step(double now, GraspOutput & out);
  void enter_squeeze(double now, GraspOutput & out);
  void hold_fault(
    GraspFail reason, const ArmContext & arm, double now, const std::string & note,
    GraspOutput & out);
  bool fresh_after(const GraspInput & in, double t) const
  {
    return in.has_reading && in.reading_time >= t;
  }

  GraspProfile p_;
  GraspState state_{GraspState::Idle};
  Sub sub_{Sub::Issue};
  GraspFail fail_{GraspFail::None};
  GraspCommand pending_;              // command to emit on the next output
  std::string note_;

  double t_start_{0.0};
  double t_cmd_{0.0};                 // when the last move was commanded
  double t_last_reading_{0.0};        // reading_time of the newest reading seen
  int open_start_{-1};                // gripper position when the grasp started
  int cur_{0};
  int target_{0};
  int confirm_first_{0};
  int approach_target_{-1};           // fast approach target (pulse), -1 = no approach in this grasp
  int prog_pos_{0};                   // approach progress watch: best position so far ...
  double prog_t_{0.0};                // ... and when it last advanced by >= 2 pulses
  int steps_{0};
  int contact_{-1};
  int squeeze_target_{-1};
  bool cancel_{false};
  bool got_temp_{false};
  bool success_pending_{false};
  bool fault_in_air_{false};
  bool needs_user_{false};
  double obs_start_{0.0};
  int obs_min_{0};
  int obs_max_{0};
  int obs_n_{0};
  double release_done_{0.0};
};

}  // namespace jetrover_base
