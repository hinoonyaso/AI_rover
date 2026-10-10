#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <deque>
#include <functional>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

#include "geometry_msgs/msg/twist.hpp"
#include "geometry_msgs/msg/twist_with_covariance_stamped.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "sensor_msgs/msg/battery_state.hpp"
#include "sensor_msgs/msg/imu.hpp"
#include "sensor_msgs/msg/joint_state.hpp"
#include "std_msgs/msg/bool.hpp"
#include "trajectory_msgs/msg/joint_trajectory.hpp"
#include "rclcpp/rclcpp.hpp"

#include "jetrover_base/command_guard.hpp"
#include "jetrover_base/crash_guard.hpp"
#include "jetrover_base/link_watchdog.hpp"
#include "jetrover_base/mecanum.hpp"
#include "jetrover_base/wheel_twist_source.hpp"
#include "jetrover_base/rrc_protocol.hpp"
#include "jetrover_base/serial_port.hpp"
#include "jetrover_base/servo_convert.hpp"

using namespace std::chrono_literals;

namespace jetrover_base
{

// Opens the STM32 serial link, parses RRC frames, publishes the STM32 IMU as
// sensor_msgs/Imu on imu/data_raw, drives the mecanum chassis from /cmd_vel and
// publishes open-loop odometry on odom_raw. Also polls the arm's bus servo
// positions (FUNC 0x05) at a low rate and publishes them as sensor_msgs/JointState
// on joint_states, so jetrover_description's URDF (which has real arm/gripper
// links as of 2026-10-03) reflects the physical arm pose instead of a fixed
// default. center_ticks/joint_signs/joint_offsets_rad default to a generic
// guess (center=500 = mid-scale of the servo's 0-1000 pulse range, sign=+1,
// offset=0) and are NOT yet calibrated against this robot's actual arm -- see
// checklist/PROJECT_CHECKLIST.md section 14.
//
// The STM32 sends no encoder or wheel-speed feedback, so odom_raw integrates the
// velocity that was commanded (same approach as Hiwonder's odom_publisher). Its pose
// drifts freely and is for debugging only: the EKF is fed the twist alone through
// wheel_twist, so an open-loop position can never leak into the filter.
//
// The STM32 keeps running the last motor command it received, so a watchdog
// stops the wheels whenever /cmd_vel goes quiet, and on shutdown.
// 한글: STM32 시리얼 링크를 열고 RRC 프레임을 파싱해 IMU(imu/data_raw)·배터리를 발행하고, /cmd_vel로 메카넘 섀시를 구동하며 open-loop 오도메트리(odom_raw)를 낸다. 팔 버스 서보 위치도 5Hz 정도로 폴링해 joint_states로 발행한다. STM32가 엔코더/바퀴 속도를 안 보내므로 odom_raw는 "명령 속도 적분"이라 디버깅용이고, EKF에는 twist만 넣는다. STM32는 마지막 모터 명령을 계속 실행하므로 /cmd_vel이 끊기거나 종료할 때 워치독이 바퀴를 세운다.
class BaseNode : public rclcpp::Node
{
public:
  BaseNode()
  : Node("base_node")
  {
    // 한글: 파라미터 선언: 시리얼 포트(by-id 경로는 재부팅해도 안 바뀜), baudrate 1Mbps, 폴링 주기 5ms. 값은 config/base.yaml에서 덮어쓴다.
    port_name_ = declare_parameter<std::string>(
      "port", "/dev/serial/by-id/usb-1a86_USB_Single_Serial_596F003889-if00");
    baudrate_ = declare_parameter<int>("baudrate", 1000000);
    const int poll_period_ms = declare_parameter<int>("poll_period_ms", 5);

    // 한글: 섀시 형상과 속도 제한. max_linear/max_angular는 /cmd_vel을 호스트에서 자르는 안전 한도다.
    wheelbase_ = declare_parameter<double>("wheelbase", 0.216);
    track_width_ = declare_parameter<double>("track_width", 0.195);
    wheel_diameter_ = declare_parameter<double>("wheel_diameter", 0.097);
    max_linear_ = declare_parameter<double>("max_linear", 0.2);
    max_angular_ = declare_parameter<double>("max_angular", 1.0);
    cmd_vel_timeout_ = declare_parameter<double>("cmd_vel_timeout", 0.5);
    stm32_timeout_ = declare_parameter<double>("stm32_timeout", 1.0);
    // Optionally send the "stop motors" frame (0x03, all 4) after speed 0. Off by default: on the
    // floor it did not stop the wheel hum it was added for (troubleshooting/032).
    // 한글: 정지 프레임 추가 전송(기본 끔). 바닥에서 바퀴 울림을 멈추지 못했다.
    motor_stop_frame_on_stop_ = declare_parameter<bool>("motor_stop_frame_on_stop", false);
    // 한글: 잘못된 형상/타임아웃 설정이면 대충 돌지 않고 시작을 거부한다(fail-fast, main()에서 잡아 종료).
    // Fail fast on bad geometry/timeouts instead of running roughly (caught in main()).
    const std::string base_err = validate_base_params(
      wheelbase_, track_width_, wheel_diameter_, max_linear_, max_angular_, cmd_vel_timeout_,
      stm32_timeout_);
    if (!base_err.empty()) {
      throw std::invalid_argument("invalid parameter: " + base_err);
    }
    watchdog_ = LinkWatchdog(cmd_vel_timeout_, stm32_timeout_);

    imu_frame_ = declare_parameter<std::string>("imu_frame", "imu_link");
    gravity_ = declare_parameter<double>("gravity", 9.80665);
    // 한글: 자이로 bias(변환된 base_link 축, rad/s). 길이가 3이 아니면 0으로 대체한다.
    gyro_bias_ = declare_parameter<std::vector<double>>("gyro_bias", {0.0, 0.0, 0.0});
    if (gyro_bias_.size() != 3) {
      RCLCPP_WARN(get_logger(), "gyro_bias must have 3 elements; using zeros");
      gyro_bias_ = {0.0, 0.0, 0.0};
    }

    imu_pub_ = create_publisher<sensor_msgs::msg::Imu>("imu/data_raw", rclcpp::SensorDataQoS());
    battery_pub_ = create_publisher<sensor_msgs::msg::BatteryState>("battery_state", 10);
    low_battery_volts_ = declare_parameter<double>("low_battery_volts", 10.0);

    odom_frame_ = declare_parameter<std::string>("odom_frame", "odom");
    base_frame_ = declare_parameter<std::string>("base_frame", "base_footprint");
    odom_linear_scale_ = declare_parameter<double>("odom_linear_scale", 1.0);
    odom_lateral_scale_ = declare_parameter<double>("odom_lateral_scale", 1.0);
    odom_angular_scale_ = declare_parameter<double>("odom_angular_scale", 1.0);
    const double odom_rate = declare_parameter<double>("odom_rate", 50.0);
    // Where wheel_twist comes from (prd/encoder-odometry.md, decided 2026-10-10: RRC path).
    // command = commanded velocity (default, vendor firmware behaviour); encoder = measured wheel speeds
    // from the rrc_m4 firmware (FUNC 0x21); auto = measured when fresh, else command.
    // 한글: wheel_twist 출처. 기본 command(기존 동작), encoder/auto는 자체 펌웨어의 측정 바퀴 속도 사용.
    const auto source_name = declare_parameter<std::string>("wheel_twist_source", "command");
    if (!parse_twist_source(source_name, twist_source_)) {
      throw std::invalid_argument("wheel_twist_source must be command, encoder or auto: " +
          source_name);
    }
    wheel_feedback_timeout_ = declare_parameter<double>("wheel_feedback_timeout", 0.2);
    // Twist variance [vx, vy, wz] used when the twist comes from the encoders (E5, 2026-10-10).
    wheel_twist_cov_encoder_ = declare_parameter<std::vector<double>>(
      "wheel_twist_covariance_encoder", {1.0e-4, 2.0e-4, 1.0e-3});
    if (wheel_twist_cov_encoder_.size() != 3) {
      throw std::invalid_argument("wheel_twist_covariance_encoder needs 3 values [vx, vy, wz]");
    }
    RCLCPP_INFO(get_logger(), "wheel_twist source: %s", twist_source_name(twist_source_));
    // Switchable at runtime (ros2 param set /base_node wheel_twist_source encoder) so a Before/After
    // comparison changes only the odometry source, not the running stack (E6, 2026-10-10).
    // 한글: 실행 중 변경 가능 — 개선 전후 비교에서 다른 것은 그대로 두고 odom 출처만 바꾸기 위해.
    param_cb_ = add_on_set_parameters_callback(
      [this](const std::vector<rclcpp::Parameter> & params) {
        rcl_interfaces::msg::SetParametersResult result;
        result.successful = true;
        for (const auto & p : params) {
          if (p.get_name() != "wheel_twist_source") {
            continue;
          }
          TwistSource next;
          if (p.get_type() != rclcpp::ParameterType::PARAMETER_STRING ||
          !parse_twist_source(p.as_string(), next))
          {
            result.successful = false;
            result.reason = "wheel_twist_source must be command, encoder or auto";
            return result;
          }
          twist_source_ = next;
          RCLCPP_INFO(get_logger(), "wheel_twist source -> %s", twist_source_name(next));
        }
        return result;
      });
    odom_pub_ = create_publisher<nav_msgs::msg::Odometry>("odom_raw", 10);
    twist_pub_ = create_publisher<geometry_msgs::msg::TwistWithCovarianceStamped>(
      "wheel_twist", 10);
    last_odom_time_ = now();
    // 한글: odom_raw 발행 타이머(기본 50Hz). 명령 속도를 적분한다.
    odom_timer_ = create_wall_timer(
      std::chrono::duration<double>(1.0 / odom_rate), [this]() {publish_odom();});

    cmd_vel_sub_ = create_subscription<geometry_msgs::msg::Twist>(
      "cmd_vel", 1, [this](geometry_msgs::msg::Twist::ConstSharedPtr msg) {on_cmd_vel(*msg);});

    timer_ = create_wall_timer(std::chrono::milliseconds(poll_period_ms), [this]() {poll();});
    stats_timer_ = create_wall_timer(1s, [this]() {log_stats();});
    watchdog_timer_ = create_wall_timer(50ms, [this]() {watchdog();});

    // 한글: 로봇팔 관련: 위치 읽기(joint_states)는 기본 켜짐, 팔 구동(arm_command_enabled)은 기본 꺼짐(안전).
    publish_arm_joint_states_ = declare_parameter<bool>("publish_arm_joint_states", true);
    if (publish_arm_joint_states_) {
      arm_joint_names_ = declare_parameter<std::vector<std::string>>(
        "arm_joint_names", {"joint1", "joint2", "joint3", "joint4", "joint5", "r_joint"});
      const auto servo_ids_param = declare_parameter<std::vector<int64_t>>(
        "arm_servo_ids", {1, 2, 3, 4, 5, 10});
      arm_servo_ids_.assign(servo_ids_param.begin(), servo_ids_param.end());
      arm_center_ticks_ = declare_parameter<std::vector<double>>(
        "arm_center_ticks", {500.0, 500.0, 500.0, 500.0, 500.0, 500.0});
      arm_joint_signs_ = declare_parameter<std::vector<double>>(
        "arm_joint_signs", {1.0, 1.0, 1.0, 1.0, 1.0, 1.0});
      arm_joint_offsets_rad_ = declare_parameter<std::vector<double>>(
        "arm_joint_offsets_rad", {0.0, 0.0, 0.0, 0.0, 0.0, 0.0});
      const double servo_range_deg = declare_parameter<double>("arm_servo_range_deg", 240.0);
      const double servo_ticks_range = declare_parameter<double>("arm_servo_ticks_range", 1000.0);
      arm_rad_per_tick_ = rad_per_tick(servo_range_deg, servo_ticks_range);
      const double arm_poll_hz = declare_parameter<double>("arm_poll_hz", 5.0);

      if (arm_joint_names_.size() != arm_servo_ids_.size() ||
        arm_joint_names_.size() != arm_center_ticks_.size() ||
        arm_joint_names_.size() != arm_joint_signs_.size() ||
        arm_joint_names_.size() != arm_joint_offsets_rad_.size())
      {
        RCLCPP_ERROR(
          get_logger(),
          "arm_joint_names/arm_servo_ids/arm_center_ticks/arm_joint_signs/"
          "arm_joint_offsets_rad length mismatch; disabling arm joint state publishing");
        publish_arm_joint_states_ = false;
      } else {
        joint_state_pub_ = create_publisher<sensor_msgs::msg::JointState>("joint_states", 10);
        arm_poll_timer_ = create_wall_timer(
          std::chrono::duration<double>(1.0 / std::max(1.0, arm_poll_hz)),
          [this]() {poll_next_arm_servo();});
        joint_state_timer_ = create_wall_timer(
          std::chrono::duration<double>(1.0 / std::max(1.0, arm_poll_hz)),
          [this]() {publish_arm_joint_states();});

        // 한글: 팔 구동 가드: 한 번에 움직일 수 있는 각도(arm_max_step_rad)와 펄스 범위(100~900)를 제한해 잘못된 명령이 관절을 때리지 못하게 한다.
        // Arm motion is off by default: the first software-driven arm move on this robot
        // (checklist 14). Every guard below exists so a bad command can't slam a joint.
        arm_command_enabled_ = declare_parameter<bool>("arm_command_enabled", false);
        arm_move_duration_s_ = declare_parameter<double>("arm_move_duration_s", 2.0);
        arm_max_step_rad_ = declare_parameter<double>("arm_max_step_rad", 0.35);
        arm_pulse_min_ = declare_parameter<int64_t>("arm_pulse_min", 100);
        arm_pulse_max_ = declare_parameter<int64_t>("arm_pulse_max", 900);
        arm_move_home_on_start_ = declare_parameter<bool>("arm_move_home_on_start", false);
        arm_home_pose_rad_ = declare_parameter<std::vector<double>>(
          "arm_home_pose_rad", {0.0, 0.0, 0.0, 0.0, 0.0, 0.0});
        if (arm_home_pose_rad_.size() != arm_joint_names_.size()) {
          RCLCPP_ERROR(get_logger(), "arm_home_pose_rad length mismatch; home move disabled");
          arm_move_home_on_start_ = false;
        }
        ArmParams arm_params;
        arm_params.servo_range_deg = servo_range_deg;
        arm_params.servo_ticks_range = servo_ticks_range;
        arm_params.center_ticks = arm_center_ticks_;
        arm_params.signs = arm_joint_signs_;
        arm_params.offsets_rad = arm_joint_offsets_rad_;
        arm_params.home_pose_rad = arm_home_pose_rad_;
        arm_params.max_step_rad = arm_max_step_rad_;
        arm_params.move_duration_s = arm_move_duration_s_;
        arm_params.pulse_min = arm_pulse_min_;
        arm_params.pulse_max = arm_pulse_max_;
        const std::string arm_err = validate_arm_params(arm_params);
        if (!arm_err.empty()) {
          throw std::invalid_argument("invalid parameter: " + arm_err);
        }
        if (arm_command_enabled_ && arm_move_home_on_start_) {
          arm_home_timer_ = create_wall_timer(2500ms, [this]() {arm_home_tick();});
          RCLCPP_WARN(get_logger(), "Arm will ramp to home pose after startup");
        }
        if (arm_command_enabled_) {
          arm_cmd_sub_ = create_subscription<sensor_msgs::msg::JointState>(
            "arm/command", 1,
            [this](sensor_msgs::msg::JointState::ConstSharedPtr msg) {on_arm_command(*msg);});
          arm_tx_timer_ = create_wall_timer(150ms, [this]() {pump_arm_tx_queue();});
          // 한글: MoveIt 실행 브리지용. 점마다 이동 시간(time_from_start)을 지정할 수 있다. 검증/클램프는 arm/command와 동일.
          // Timed variant for the MoveIt execution bridge: the first point's time_from_start sets
          // the move duration; every guard is the same as arm/command.
          arm_timed_sub_ = create_subscription<trajectory_msgs::msg::JointTrajectory>(
            "arm/command_timed", 1,
            [this](trajectory_msgs::msg::JointTrajectory::ConstSharedPtr msg) {
              on_arm_command_timed(*msg);
            });
          arm_torque_sub_ = create_subscription<std_msgs::msg::Bool>(
            "arm/torque", 1,
            [this](std_msgs::msg::Bool::ConstSharedPtr msg) {set_arm_torque(msg->data);});
          RCLCPP_WARN(get_logger(), "Arm command input ENABLED on arm/command, arm/torque");
        }
      }
    }
  }

  // 한글: 종료 시 반드시 모터를 정지하고 crash guard를 해제한다.
  ~BaseNode() override
  {
    stop_motors();
    crash_guard::disarm();
  }

private:
  // 한글: 5ms마다 시리얼을 읽어 파서에 넣고 완성된 패킷을 처리한다. 오류가 나면 포트를 닫고 다음 틱에 다시 연다(USB 재연결 대응).
  void poll()
  {
    if (!serial_.is_open() && !try_open()) {
      return;
    }

    uint8_t buffer[512];
    while (true) {
      const int n = serial_.read(buffer, sizeof(buffer), 0);
      if (n < 0) {
        RCLCPP_ERROR(get_logger(), "Serial error: %s (will reopen)", serial_.last_error().c_str());
        crash_guard::disarm();
        serial_.close();
        return;
      }
      if (n == 0) {
        return;
      }

      parser_.feed(buffer, static_cast<std::size_t>(n));

      RrcPacket packet;
      while (parser_.next(packet)) {
        note_rx();
        ++packet_counts_[packet.function];
        handle_packet(packet);
      }
    }
  }

  // 한글: 시리얼을 열고 즉시 정지 명령을 보낸다(이전 세션의 잔여 명령 제거). 비정상 종료 대비 정지 프레임을 crash guard에 등록한다.
  bool try_open()
  {
    if (serial_.open(port_name_, baudrate_)) {
      RCLCPP_INFO(get_logger(), "Opened %s @ %d", port_name_.c_str(), baudrate_);
      watchdog_.on_open(now().seconds());
      stop_motors();
      const auto stop_frame = build_motor_packet({{1, 0.0f}, {2, 0.0f}, {3, 0.0f}, {4, 0.0f}});
      crash_guard::arm(serial_.fd(), stop_frame);
      return true;
    }
    RCLCPP_WARN_THROTTLE(
      get_logger(), *get_clock(), 2000, "Cannot open serial: %s", serial_.last_error().c_str());
    return false;
  }

  // 한글: /cmd_vel 수신: 속도를 제한하고 시각을 기록한 뒤 모터 명령을 보낸다. 오도메트리 적분용으로 명령값도 저장한다.
  void on_cmd_vel(const geometry_msgs::msg::Twist & msg)
  {
    // 한글: 먼저 검증한다. std::clamp는 NaN을 걸러주지 않으므로 NaN/Inf는 clamp 전에 거부하고 정지한다.
    // STM32가 침묵 중일 때의 0이 아닌 명령도 거부(저장 안 함 -> 복구 후 예전 명령이 되살아나지 않는다).
    // Validate first: std::clamp does not sanitize NaN, so reject NaN/Inf before clamping and stop.
    // Non-zero motion while the STM32 is silent is rejected too (and not cached).
    const CmdDecision decision =
      decide_cmd_vel(msg.linear.x, msg.linear.y, msg.angular.z, watchdog_.stm32_silent());
    if (decision == CmdDecision::RejectNonFinite) {
      RCLCPP_ERROR_THROTTLE(
        get_logger(), *get_clock(), 2000, "cmd_vel rejected: non-finite value (NaN/Inf), stopping");
      stop_motors();
      return;
    }
    if (decision == CmdDecision::RejectStm32Silent) {
      RCLCPP_WARN_THROTTLE(
        get_logger(), *get_clock(), 2000,
        "cmd_vel rejected: STM32 is silent, holding stop until it recovers");
      stop_motors();
      return;
    }
    const double vx = std::clamp(msg.linear.x, -max_linear_, max_linear_);
    const double vy = std::clamp(msg.linear.y, -max_linear_, max_linear_);
    const double wz = std::clamp(msg.angular.z, -max_angular_, max_angular_);

    watchdog_.on_cmd(now().seconds(), vx != 0.0 || vy != 0.0 || wz != 0.0);
    cmd_vx_ = vx;
    cmd_vy_ = vy;
    cmd_wz_ = wz;
    send_motors(
      mecanum_inverse(vx, vy, wz, wheelbase_, track_width_, wheel_diameter_));
  }

  // Integrates the commanded body velocity (open loop) and publishes it.
  // 한글: 명령 속도를 적분해 odom_raw와 wheel_twist를 발행한다. STM32가 멈췄거나 시리얼이 닫혔으면 속도는 0으로 본다. 공분산이 큰 이유: 실제 속도가 아니라 명령값이라서.
  void publish_odom()
  {
    const rclcpp::Time stamp = now();
    const double dt = (stamp - last_odom_time_).seconds();
    last_odom_time_ = stamp;

    const bool driving = serial_.is_open() && !watchdog_.stm32_silent();
    BodyTwist commanded;
    commanded.vx = driving ? cmd_vx_ * odom_linear_scale_ : 0.0;
    commanded.vy = driving ? cmd_vy_ * odom_linear_scale_ * odom_lateral_scale_ : 0.0;
    commanded.wz = driving ? cmd_wz_ * odom_angular_scale_ : 0.0;
    const bool feedback_fresh = driving && last_wheel_feedback_s_ > 0.0 &&
      stamp.seconds() - last_wheel_feedback_s_ <= wheel_feedback_timeout_;
    const TwistChoice choice = choose_wheel_twist(
      twist_source_, commanded, feedback_fresh, wheel_rps_, wheelbase_, track_width_,
        wheel_diameter_);
    if (choice.feedback_stale) {
      RCLCPP_WARN_THROTTLE(
        get_logger(), *get_clock(), 2000,
        "wheel_twist_source=encoder but no fresh FUNC 0x21 wheel feedback (vendor firmware?): twist 0");
    }
    const double vx = choice.twist.vx;
    const double vy = choice.twist.vy;
    const double wz = choice.twist.wz;

    odom_x_ += (vx * std::cos(odom_yaw_) - vy * std::sin(odom_yaw_)) * dt;
    odom_y_ += (vx * std::sin(odom_yaw_) + vy * std::cos(odom_yaw_)) * dt;
    odom_yaw_ += wz * dt;

    nav_msgs::msg::Odometry msg;
    msg.header.stamp = stamp;
    msg.header.frame_id = odom_frame_;
    msg.child_frame_id = base_frame_;
    msg.pose.pose.position.x = odom_x_;
    msg.pose.pose.position.y = odom_y_;
    msg.pose.pose.orientation.z = std::sin(odom_yaw_ / 2.0);
    msg.pose.pose.orientation.w = std::cos(odom_yaw_ / 2.0);
    msg.twist.twist.linear.x = vx;
    msg.twist.twist.linear.y = vy;
    msg.twist.twist.angular.z = wz;

    // Pose covariance (odom_raw pose is never fused). Twist: large for the open-loop command,
    // measured values for the encoder source (below). 한글: twist 공분산은 출처별로 다르게.
    msg.pose.covariance[0] = 0.05;
    msg.pose.covariance[7] = 0.05;
    msg.pose.covariance[35] = 0.1;
    if (choice.from_encoder) {
      // Measured wheel speeds (E5, 2026-10-10): instantaneous vx std 0.004 m/s on the floor, 1 m bias
      // +0.24 % / strafe -0.48 % (encoder_odom_e4_20261010.md) -> std 0.01 / 0.014 m/s with margin.
      // 한글: 엔코더 속도의 분산(실측 근거). 명령값일 때는 아래 큰 값 유지.
      msg.twist.covariance[0] = wheel_twist_cov_encoder_[0];
      msg.twist.covariance[7] = wheel_twist_cov_encoder_[1];
      msg.twist.covariance[35] = wheel_twist_cov_encoder_[2];
    } else {
      msg.twist.covariance[0] = 0.05;
      msg.twist.covariance[7] = 0.05;
      msg.twist.covariance[35] = 0.1;
    }

    odom_pub_->publish(msg);

    geometry_msgs::msg::TwistWithCovarianceStamped twist;
    twist.header.stamp = stamp;
    twist.header.frame_id = base_frame_;
    twist.twist = msg.twist;
    twist_pub_->publish(twist);
  }

  void note_rx()
  {
    if (watchdog_.on_rx(now().seconds())) {
      RCLCPP_INFO(get_logger(), "STM32 stream recovered");
    }
  }

  // The STM32 streams IMU at ~100 Hz. Silence means its firmware (or power) hung:
  // the USB-UART bridge stays enumerated, so the port looks fine from the host.
  // 한글: STM32는 IMU를 약 100Hz로 계속 보내므로 침묵하면 펌웨어(또는 전원)가 멈춘 것이다. USB-UART 브리지는 계속 보이기 때문에 포트만 봐서는 모른다. 침묵이 길면 정지 명령을 보낸다.
  // 한글: 50ms마다: STM32 heartbeat 확인 + cmd_vel이 timeout 동안 없으면 바퀴 정지. 판단 로직은 LinkWatchdog(단위시험 있음).
  void watchdog()
  {
    const auto result = watchdog_.check(now().seconds(), serial_.is_open());
    if (result.action == LinkWatchdog::Action::StopStm32Silent) {
      RCLCPP_ERROR(
        get_logger(), "STM32 silent for %.1fs (moving=%d): stopping motors", result.silent_s,
        result.was_moving);
      stop_motors();
    } else if (result.action == LinkWatchdog::Action::StopCmdTimeout) {
      RCLCPP_WARN(
        get_logger(), "cmd_vel timeout (%.2fs), stopping motors", watchdog_.cmd_vel_timeout());
      stop_motors();
    }
  }

  // 한글: 모든 바퀴를 0 rev/s로. 상태/명령 캐시도 초기화한다.
  void stop_motors()
  {
    watchdog_.on_stopped();
    cmd_vx_ = cmd_vy_ = cmd_wz_ = 0.0;
    send_motors({{1, 0.0f}, {2, 0.0f}, {3, 0.0f}, {4, 0.0f}});
    if (motor_stop_frame_on_stop_ && serial_.is_open()) {
      const auto frame = build_motor_stop_packet(0x0F);
      if (!serial_.write(frame.data(), frame.size())) {
        RCLCPP_ERROR(get_logger(), "Motor stop write failed: %s", serial_.last_error().c_str());
      }
    }
  }

  void send_motors(const std::vector<MotorCommand> & motors)
  {
    if (!serial_.is_open()) {
      return;
    }
    const auto frame = build_motor_packet(motors);
    if (!serial_.write(frame.data(), frame.size())) {
      RCLCPP_ERROR(get_logger(), "Motor write failed: %s", serial_.last_error().c_str());
    }
  }

  // 한글: 수신 패킷 분기: 배터리 → IMU → 버스 서보 위치 순서로 시도한다.
  void handle_packet(const RrcPacket & packet)
  {
    uint16_t millivolts = 0;
    if (decode_battery(packet, millivolts)) {
      publish_battery(millivolts);
      return;
    }

    ImuRaw imu;
    if (decode_imu(packet, imu)) {
      publish_imu(imu);
      return;
    }

    WheelFeedback wheels;
    if (decode_wheel_feedback(packet, wheels)) {
      for (int i = 0; i < 4; ++i) {
        wheel_rps_[i] = wheels.rps[i];
      }
      last_wheel_feedback_s_ = now().seconds();
      return;
    }

    BusServoPosition servo_pos;
    if (decode_bus_servo_position(packet, servo_pos)) {
      if (servo_pos.success == 0) {
        arm_servo_ticks_[servo_pos.id] = servo_pos.pulse;
      }
    }
  }

  // Bus servo positions are request/response (the STM32 doesn't stream them on its
  // own), unlike IMU/battery. Cycle through the configured servo IDs one at a time
  // so this stays a low, steady request rate rather than bursting.
  void poll_next_arm_servo()
  {
    if (!serial_.is_open() || arm_servo_ids_.empty()) {
      return;
    }
    const uint8_t servo_id = static_cast<uint8_t>(arm_servo_ids_[arm_poll_index_]);
    arm_poll_index_ = (arm_poll_index_ + 1) % arm_servo_ids_.size();
    const auto frame = build_bus_servo_read_position(servo_id);
    if (!serial_.write(frame.data(), frame.size())) {
      RCLCPP_ERROR_THROTTLE(
        get_logger(), *get_clock(), 5000, "Arm servo poll write failed: %s",
        serial_.last_error().c_str());
    }
  }

  // Torque on = servo holds position (stiff), off = limp. Applied to every configured arm servo.
  // Verified on hardware (2026-10-05): a loaded servo drives toward its OLD stored target
  // instead of holding where it is, so loading must be PRECEDED by a move-to-current-position
  // that overwrites that target (2026-10-05: 0x0B = release, 0x0C = load; the names were swapped before). Frames go through a queue (one per arm_tx_period) because
  // back-to-back bus servo frames are dropped, and so this never blocks the cmd_vel watchdog.
  void set_arm_torque(bool enable)
  {
    // 한글: 토크를 걸 때는 서보가 "저장돼 있던 옛 목표값"으로 튀지 않도록, 먼저 현재 위치로 이동 명령(hold)을
    // 보내 목표를 덮어쓴 뒤 load(0x0C)를 건다. 해제(0x0B)는 그냥 보낸다. 0x0B/0x0C 의미는 rrc_protocol.hpp 참고.
    if (enable) {
      arm_tx_queue_.push_back(
        [this]() {
          std::vector<BusServoTarget> hold;
          for (const auto id : arm_servo_ids_) {
            const auto it = arm_servo_ticks_.find(static_cast<uint8_t>(id));
            if (it != arm_servo_ticks_.end()) {
              // 한글: 읽은 눈금이 음수/범위 밖(예: -34)이면 uint16 변환 시 65502 같은 값이 서보로 가므로
              // 안전 클램프(arm_pulse_min/max)로 제한한 값만 보낸다.
              const int64_t pulse = std::min<int64_t>(
                std::max<int64_t>(static_cast<int64_t>(it->second), arm_pulse_min_),
                arm_pulse_max_);
              hold.push_back({static_cast<uint8_t>(id), static_cast<uint16_t>(pulse)});
            }
          }
          RCLCPP_WARN(get_logger(), "arm hold: target pinned at current position for %zu servos",
            hold.size());
          return build_bus_servo_set_position(1.0, hold);
        });
    }
    for (const auto id : arm_servo_ids_) {
      const uint8_t servo_id = static_cast<uint8_t>(id);
      arm_tx_queue_.push_back(
        [servo_id, enable]() {return build_bus_servo_torque(servo_id, enable);});
    }
    RCLCPP_WARN(get_logger(), "arm torque %s queued", enable ? "ON(+hold)" : "OFF");
  }

  // Startup ramp to the home pose: wait for every servo reading, load + hold, then walk each
  // joint toward its home angle in steps of at most arm_home_step_rad every 2.5 s. Starting
  // pose is whatever the (limp) arm sagged to, so keep the area around the arm clear.
  void arm_home_tick()
  {
    if (arm_home_state_ == 0) {
      for (const auto id : arm_servo_ids_) {
        if (arm_servo_ticks_.find(static_cast<uint8_t>(id)) == arm_servo_ticks_.end()) {
          return;
        }
      }
      set_arm_torque(true);
      arm_home_state_ = 1;
      return;
    }
    if (arm_home_state_ == 1) {
      if (arm_tx_queue_.empty()) {
        arm_home_state_ = 2;
      }
      return;
    }
    std::vector<BusServoTarget> step;
    bool done = true;
    for (std::size_t i = 0; i < arm_joint_names_.size(); ++i) {
      const uint8_t id = static_cast<uint8_t>(arm_servo_ids_[i]);
      const double cur = arm_ticks_to_rad(i, static_cast<double>(arm_servo_ticks_[id]));
      const double delta = arm_home_pose_rad_[i] - cur;
      if (std::abs(delta) > 0.03) {
        done = false;
      }
      const double next = cur + std::min(std::max(delta, -arm_home_step_rad_), arm_home_step_rad_);
      const double raw = std::round(arm_rad_to_ticks(i, next));
      const int64_t pulse = clamp_pulse(raw, arm_pulse_min_, arm_pulse_max_);
      step.push_back({id, static_cast<uint16_t>(pulse)});
    }
    if (done) {
      arm_home_timer_->cancel();
      RCLCPP_WARN(get_logger(), "arm reached home pose");
      return;
    }
    const auto frame = build_bus_servo_set_position(arm_move_duration_s_, step);
    if (!serial_.write(frame.data(), frame.size())) {
      RCLCPP_ERROR(get_logger(), "arm home step write failed: %s", serial_.last_error().c_str());
    }
  }

  void pump_arm_tx_queue()
  {
    if (arm_tx_queue_.empty() || !serial_.is_open()) {
      return;
    }
    const auto frame = arm_tx_queue_.front()();
    arm_tx_queue_.pop_front();
    if (!serial_.write(frame.data(), frame.size())) {
      RCLCPP_ERROR(get_logger(), "arm tx write failed: %s", serial_.last_error().c_str());
    }
  }

  // 한글: 변환 수식은 servo_convert.hpp(단위시험 있음). 여기서는 관절별 보정값만 모아 넘긴다.
  ServoCal arm_cal(std::size_t i) const
  {
    return {
      arm_center_ticks_[i], arm_joint_signs_[i], arm_joint_offsets_rad_[i], arm_rad_per_tick_};
  }

  double arm_ticks_to_rad(std::size_t i, double ticks) const
  {
    return ticks_to_rad(arm_cal(i), ticks);
  }

  double arm_rad_to_ticks(std::size_t i, double rad) const
  {
    return rad_to_ticks(arm_cal(i), rad);
  }

  // sensor_msgs/JointState (name + position in rad) -> one bus servo move frame.
  // The whole command is rejected (nothing sent) if any joint is unknown, has no
  // position reading yet, or would jump more than arm_max_step_rad from where it is.
  // 한글: JointState(이름+라디안)를 버스 서보 이동 프레임으로 변환한다. 알 수 없는 관절, 위치 읽기 전 관절, 한 번에 arm_max_step_rad 넘게 움직이는 관절이 하나라도 있으면 전체를 거부(아무것도 안 보냄)한다.
  void on_arm_command(const sensor_msgs::msg::JointState & msg)
  {
    on_arm_command(msg, arm_move_duration_s_);
  }

  // 한글: JointTrajectory의 첫 점만 쓴다(브리지가 점을 하나씩 보낸다). 이동 시간은 [0.1, 5] 초로 제한 --
  // 너무 짧으면 서보가 급가속, 너무 길면 브리지의 시간 관리가 어긋난다.
  // Only the first point is used (the bridge streams one point at a time). Duration is clamped to
  // [0.1, 5] s: too short = violent servo move, too long = the bridge loses track of time.
  void on_arm_command_timed(const trajectory_msgs::msg::JointTrajectory & traj)
  {
    if (traj.points.empty() || traj.joint_names.size() != traj.points[0].positions.size()) {
      RCLCPP_WARN(get_logger(), "arm/command_timed ignored: empty or name/position mismatch");
      return;
    }
    const auto & pt = traj.points[0];
    const double dur = static_cast<double>(pt.time_from_start.sec) +
      static_cast<double>(pt.time_from_start.nanosec) * 1e-9;
    if (!std::isfinite(dur)) {
      RCLCPP_WARN(get_logger(), "arm/command_timed rejected: non-finite duration");
      return;
    }
    sensor_msgs::msg::JointState js;
    js.name = traj.joint_names;
    js.position = pt.positions;
    on_arm_command(js, std::min(std::max(dur, 0.1), 5.0));
  }

  void on_arm_command(const sensor_msgs::msg::JointState & msg, double duration_s)
  {
    if (!serial_.is_open() || msg.name.size() != msg.position.size() || msg.name.empty()) {
      RCLCPP_WARN(get_logger(), "arm/command ignored: serial closed or name/position mismatch");
      return;
    }
    // 한글: NaN/Inf가 있으면 전체 거부. NaN은 step 비교(`> max`)도 통과하고 정수 변환이 정의되지 않는다.
    // Reject the whole command on NaN/Inf: NaN slips through the `> max` step check and the
    // integer conversion would be undefined.
    if (!all_finite(msg.position)) {
      RCLCPP_WARN(get_logger(), "arm/command rejected: non-finite position (NaN/Inf)");
      return;
    }
    std::vector<BusServoTarget> targets;
    for (std::size_t k = 0; k < msg.name.size(); ++k) {
      const auto joint_it = std::find(
        arm_joint_names_.begin(), arm_joint_names_.end(), msg.name[k]);
      if (joint_it == arm_joint_names_.end()) {
        RCLCPP_WARN(get_logger(), "arm/command rejected: unknown joint '%s'", msg.name[k].c_str());
        return;
      }
      const std::size_t i = static_cast<std::size_t>(joint_it - arm_joint_names_.begin());
      const uint8_t id = static_cast<uint8_t>(arm_servo_ids_[i]);
      const auto cur = arm_servo_ticks_.find(id);
      if (cur == arm_servo_ticks_.end()) {
        RCLCPP_WARN(
          get_logger(), "arm/command rejected: no position reading for '%s' yet",
          msg.name[k].c_str());
        return;
      }
      const double cur_rad = arm_ticks_to_rad(i, static_cast<double>(cur->second));
      if (std::abs(msg.position[k] - cur_rad) > arm_max_step_rad_) {
        RCLCPP_WARN(
          get_logger(),
          "arm/command rejected: '%s' step %.3f rad exceeds arm_max_step_rad %.3f "
          "(current %.3f, target %.3f) -- send smaller steps",
          msg.name[k].c_str(), std::abs(msg.position[k] - cur_rad), arm_max_step_rad_, cur_rad,
          msg.position[k]);
        return;
      }
      const double raw = std::round(arm_rad_to_ticks(i, msg.position[k]));
      const int64_t pulse = clamp_pulse(raw, arm_pulse_min_, arm_pulse_max_);
      targets.push_back({id, static_cast<uint16_t>(pulse)});
    }
    // Logged only once validation passed for every joint -- a mid-loop log here would
    // misleadingly claim a move that a later joint's check could still reject.
    for (std::size_t k = 0; k < msg.name.size(); ++k) {
      RCLCPP_INFO(
        get_logger(), "arm move: %s id=%u -> %u", msg.name[k].c_str(), targets[k].id,
        targets[k].pulse);
    }
    const auto frame = build_bus_servo_set_position(duration_s, targets);
    if (!serial_.write(frame.data(), frame.size())) {
      RCLCPP_ERROR(get_logger(), "arm move write failed: %s", serial_.last_error().c_str());
    }
  }

  // Publishes whatever servo ticks have been read so far (converted to radians).
  // Joints whose servo hasn't reported yet are simply left out of this message
  // (robot_state_publisher keeps their last/default value); mimic joints (gripper
  // fingers) are not listed here -- the URDF's <mimic> tags derive them from r_joint.
  // 한글: 지금까지 읽은 서보 값을 라디안으로 발행. 아직 못 읽은 관절은 빠진다. 그리퍼 손가락은 URDF mimic이 r_joint에서 유도한다.
  void publish_arm_joint_states()
  {
    sensor_msgs::msg::JointState msg;
    msg.header.stamp = now();
    for (std::size_t i = 0; i < arm_joint_names_.size(); ++i) {
      const auto it = arm_servo_ticks_.find(static_cast<uint8_t>(arm_servo_ids_[i]));
      if (it == arm_servo_ticks_.end()) {
        continue;
      }
      const double angle = arm_ticks_to_rad(i, static_cast<double>(it->second));
      msg.name.push_back(arm_joint_names_[i]);
      msg.position.push_back(angle);
    }
    if (!msg.name.empty()) {
      joint_state_pub_->publish(msg);
    }
  }

  // Battery voltage as reported by the STM32 (about once per second). Kept so a hang can be
  // correlated with the voltage at that moment.
  // 한글: 배터리 전압(mV→V) 발행, 하한 미만이면 30초마다 경고.
  void publish_battery(uint16_t millivolts)
  {
    sensor_msgs::msg::BatteryState msg;
    msg.header.stamp = now();
    msg.voltage = static_cast<float>(millivolts) / 1000.0f;
    msg.present = true;
    msg.power_supply_status = sensor_msgs::msg::BatteryState::POWER_SUPPLY_STATUS_UNKNOWN;
    msg.power_supply_technology = sensor_msgs::msg::BatteryState::POWER_SUPPLY_TECHNOLOGY_UNKNOWN;
    battery_pub_->publish(msg);

    if (msg.voltage < low_battery_volts_) {
      RCLCPP_WARN_THROTTLE(
        get_logger(), *get_clock(), 30000, "Battery low: %.2f V (charge below %.1f V)",
        msg.voltage, low_battery_volts_);
    }
  }

  // The STM32 reports acceleration in g and angular rate in deg/s (same
  // conversion as Hiwonder's ros_robot_controller). The board's IMU axes are
  // mounted as X = robot right, Y = robot back, Z = down (found by tilting the
  // robot: flat gives az = -g, left side up gives ax = -g, nose down gives
  // ay = +g), so they are rotated into the base_link convention
  // (x forward, y left, z up) before publishing. gyro_bias is in that frame, rad/s.
  // 한글: IMU 변환 발행: 보드 축(X=오른쪽, Y=뒤, Z=아래)을 base_link(x 앞, y 왼쪽, z 위)로 회전하고 g→m/s², deg/s→rad/s로 바꾼 뒤 gyro_bias를 뺀다. orientation_covariance[0]=-1은 방향 추정 없음(REP-145).
  void publish_imu(const ImuRaw & imu)
  {
    constexpr double kDegToRad = M_PI / 180.0;

    sensor_msgs::msg::Imu msg;
    msg.header.stamp = now();
    msg.header.frame_id = imu_frame_;

    // No orientation estimate (REP-145).
    msg.orientation_covariance[0] = -1.0;

    msg.linear_acceleration.x = -imu.ay * gravity_;
    msg.linear_acceleration.y = -imu.ax * gravity_;
    msg.linear_acceleration.z = -imu.az * gravity_;

    msg.angular_velocity.x = -imu.gy * kDegToRad - gyro_bias_[0];
    msg.angular_velocity.y = -imu.gx * kDegToRad - gyro_bias_[1];
    msg.angular_velocity.z = -imu.gz * kDegToRad - gyro_bias_[2];

    msg.linear_acceleration_covariance[0] = 0.0004;
    msg.linear_acceleration_covariance[4] = 0.0004;
    msg.linear_acceleration_covariance[8] = 0.004;
    msg.angular_velocity_covariance[0] = 0.01;
    msg.angular_velocity_covariance[4] = 0.01;
    msg.angular_velocity_covariance[8] = 0.01;

    imu_pub_->publish(msg);
  }

  void log_stats()
  {
    if (packet_counts_.empty()) {
      return;
    }
    std::string text;
    for (const auto & [func, count] : packet_counts_) {
      char item[48];
      std::snprintf(item, sizeof(item), " 0x%02X:%zu", func, count);
      text += item;
    }
    packet_counts_.clear();
    RCLCPP_DEBUG(get_logger(), "packets/s%s", text.c_str());
  }

  std::string port_name_;
  int baudrate_{1000000};

  double wheelbase_{0.216};
  double track_width_{0.195};
  double wheel_diameter_{0.097};
  double max_linear_{0.2};
  double max_angular_{1.0};
  double cmd_vel_timeout_{0.5};
  double stm32_timeout_{1.0};

  std::string imu_frame_;
  double gravity_{9.80665};
  std::vector<double> gyro_bias_;

  std::string odom_frame_;
  std::string base_frame_;
  double odom_linear_scale_{1.0};
  double odom_lateral_scale_{1.0};
  double odom_angular_scale_{1.0};
  double cmd_vx_{0.0}, cmd_vy_{0.0}, cmd_wz_{0.0};
  TwistSource twist_source_{TwistSource::Command};
  double wheel_feedback_timeout_{0.2};
  double wheel_rps_[4]{0.0, 0.0, 0.0, 0.0};
  double last_wheel_feedback_s_{0.0};
  std::vector<double> wheel_twist_cov_encoder_;
  OnSetParametersCallbackHandle::SharedPtr param_cb_;
  double odom_x_{0.0}, odom_y_{0.0}, odom_yaw_{0.0};
  rclcpp::Time last_odom_time_{0, 0, RCL_ROS_TIME};

  LinkWatchdog watchdog_;

  SerialPort serial_;
  RrcParser parser_;
  std::map<uint8_t, std::size_t> packet_counts_;

  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::TimerBase::SharedPtr stats_timer_;
  rclcpp::TimerBase::SharedPtr watchdog_timer_;
  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_sub_;
  rclcpp::Publisher<sensor_msgs::msg::Imu>::SharedPtr imu_pub_;
  rclcpp::Publisher<sensor_msgs::msg::BatteryState>::SharedPtr battery_pub_;
  double low_battery_volts_{10.0};
  rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
  rclcpp::Publisher<geometry_msgs::msg::TwistWithCovarianceStamped>::SharedPtr twist_pub_;
  rclcpp::TimerBase::SharedPtr odom_timer_;

  bool publish_arm_joint_states_{true};
  std::vector<std::string> arm_joint_names_;
  std::vector<int64_t> arm_servo_ids_;
  std::vector<double> arm_center_ticks_;
  std::vector<double> arm_joint_signs_;
  std::vector<double> arm_joint_offsets_rad_;
  double arm_rad_per_tick_{0.0};
  std::size_t arm_poll_index_{0};
  std::map<uint8_t, int16_t> arm_servo_ticks_;
  rclcpp::Publisher<sensor_msgs::msg::JointState>::SharedPtr joint_state_pub_;
  rclcpp::TimerBase::SharedPtr arm_poll_timer_;
  rclcpp::TimerBase::SharedPtr joint_state_timer_;
  bool arm_command_enabled_{false};
  bool motor_stop_frame_on_stop_{false};
  double arm_move_duration_s_{2.0};
  double arm_max_step_rad_{0.35};
  int64_t arm_pulse_min_{100};
  int64_t arm_pulse_max_{900};
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr arm_cmd_sub_;
  rclcpp::Subscription<trajectory_msgs::msg::JointTrajectory>::SharedPtr arm_timed_sub_;
  rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr arm_torque_sub_;
  rclcpp::TimerBase::SharedPtr arm_tx_timer_;
  rclcpp::TimerBase::SharedPtr arm_home_timer_;
  bool arm_move_home_on_start_{false};
  std::vector<double> arm_home_pose_rad_;
  double arm_home_step_rad_{0.3};
  int arm_home_state_{0};
  std::deque<std::function<std::vector<uint8_t>()>> arm_tx_queue_;
};

}  // namespace jetrover_base

// 한글: 노드 진입점.
int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  // 한글: 파라미터 검증 실패(생성자에서 throw)는 로그를 남기고 비정상 종료한다.
  // A parameter validation failure (thrown in the constructor) logs and exits non-zero.
  try {
    rclcpp::spin(std::make_shared<jetrover_base::BaseNode>());
  } catch (const std::invalid_argument & e) {
    RCLCPP_FATAL(rclcpp::get_logger("base_node"), "%s", e.what());
    rclcpp::shutdown();
    return 1;
  }
  rclcpp::shutdown();
  return 0;
}
