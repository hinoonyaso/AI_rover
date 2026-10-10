/* 한글: micro-ROS 노드(COMM_MODE=MICROROS일 때 주 통신). 토픽/서비스 목록과 에이전트 실행 방법이 아래에 있다. 이 파일은 주변장치를 직접 만지지 않고 robot_ctrl/robot_services API만 쓴다. */
/* micro-ROS (XRCE-DDS over serial) node: the PRIMARY host link when built with COMM_MODE=MICROROS.
 * Agent side:  ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyACM0 -b 1000000
 *
 *   publishes   /rrc/imu_raw      sensor_msgs/Imu          ROS frame (x fwd, y left, z up), no gyro bias
 *               /rrc/battery      sensor_msgs/BatteryState voltage [V]
 *               /rrc/wheel_rps    std_msgs/Float32MultiArray   4 x wheel rev/s (measured)
 *               /rrc/status       std_msgs/Int32MultiArray     see STATUS_FIELDS below
 *   subscribes  /cmd_vel          geometry_msgs/Twist      clamped by CMD_VEL_MAX_* then robot_set_velocity()
 *               /rrc/pid_cmd      std_msgs/Float32MultiArray   [motor(255=all), kp, ki, kd]
 *               /rrc/buzzer_cmd   std_msgs/UInt16MultiArray    [freq, on_ms, off_ms, cycles]
 *               /rrc/led_cmd      std_msgs/UInt16MultiArray    [on_ms, off_ms, cycles]
 *   service     /rrc/estop        std_srvs/SetBool         data=true: latch e-stop, false: clear
 * STATUS_FIELDS: [flags, stop_reason, imu_kind, comm_mode, fault0..3, uptime_ms, reset_cause]
 *
 * All hardware access goes through the robot_services/robot_ctrl API; this file never touches a peripheral. */
#ifndef COMM_MICROROS_H
#define COMM_MICROROS_H

#include "rrc_ext.h"

/* 2026-10-10: 0.5 m/s / 2.0 rad/s -> the RRC-verified base_node limits (0.2 / 1.0). 한글: RRC 검증값과 통일. */
#define CMD_VEL_MAX_LINEAR_MPS 0.2f
#define CMD_VEL_MAX_ANGULAR_RPS 1.0f

void comm_microros_task(void *arg);
void comm_microros_publish_imu(const float accel_g[3], const float gyro_dps[3]);
void comm_microros_publish_battery(uint16_t mv);
void comm_microros_publish_status(const rrc_ext_status_t *s);
void comm_microros_publish_wheel(const rrc_ext_wheel_t *w);

#endif
