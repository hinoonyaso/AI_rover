# 한글: micro-ROS 펌웨어의 /rrc/* 토픽을 기존 스택이 쓰는 토픽(/imu/data_raw, /wheel_twist, /battery_state)으로 연결하는 브리지 노드.
"""Bridge between the micro-ROS firmware topics (/rrc/*) and the topics the rest of the stack uses.

  /rrc/imu_raw   -> /imu/data_raw      subtracts the configured gyro bias (firmware has none)
  /rrc/wheel_rps -> /wheel_twist       mecanum forward kinematics of the MEASURED wheel speeds
  /rrc/battery   -> /battery_state     republished + low battery warning
  /rrc/status    -> log               e-stop / motor fault / low battery transitions
"""
import math

from geometry_msgs.msg import TwistWithCovarianceStamped
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import BatteryState, Imu
from std_msgs.msg import Float32MultiArray, Int32MultiArray

STATUS_FLAGS = {0x01: 'ESTOP', 0x02: 'MOVING', 0x04: 'LOW_BATTERY', 0x08: 'MOTOR_ENABLED', 0x10: 'MOTOR_FAULT'}
STOP_REASONS = {0: 'none', 1: 'cmd timeout', 2: 'estop', 3: 'low battery', 4: 'motor fault', 5: 'stop command'}
FAULTS = {0: 'ok', 1: 'driver fault pin', 2: 'runaway/stall (check encoder polarity)'}


# 한글: 측정된 바퀴 rev/s에서 몸체 속도(vx, vy, wz)를 구한다. base_node.mecanum_rps와 firmware core/mecanum.c의 역변환이다.
def mecanum_forward(rps, wheelbase, track_width, wheel_diameter):
    """Inverse of base_node.mecanum_rps (and of core/mecanum.c): wheel rev/s -> (vx, vy, wz)."""
    q = math.pi * wheel_diameter / 4.0
    k = -(rps[0] + rps[1] + rps[2] + rps[3]) * q
    vx = (rps[0] + rps[1] - rps[2] - rps[3]) * q
    vy = (rps[1] - rps[0] + rps[3] - rps[2]) * q
    wz = 2.0 * k / (wheelbase + track_width)
    return vx, vy, wz


class RrcBridge(Node):

    def __init__(self):
        super().__init__('rrc_bridge')
        self.wheelbase = self.declare_parameter('wheelbase', 0.216).value
        self.track_width = self.declare_parameter('track_width', 0.195).value
        self.wheel_diameter = self.declare_parameter('wheel_diameter', 0.097).value
        self.imu_frame = self.declare_parameter('imu_frame', 'imu_link').value
        self.base_frame = self.declare_parameter('base_frame', 'base_footprint').value
        self.gyro_bias = list(self.declare_parameter('gyro_bias', [0.0, 0.0, 0.0]).value)
        self.low_battery = self.declare_parameter('low_battery_volts', 10.0).value
        self.cov = list(self.declare_parameter('wheel_twist_cov', [0.02, 0.02, 0.05]).value)

        self.imu_pub = self.create_publisher(Imu, 'imu/data_raw', qos_profile_sensor_data)
        self.twist_pub = self.create_publisher(TwistWithCovarianceStamped, 'wheel_twist', 10)
        self.batt_pub = self.create_publisher(BatteryState, 'battery_state', 10)
        self.create_subscription(Imu, 'rrc/imu_raw', self.on_imu, qos_profile_sensor_data)
        self.create_subscription(Float32MultiArray, 'rrc/wheel_rps', self.on_wheel, qos_profile_sensor_data)
        self.create_subscription(BatteryState, 'rrc/battery', self.on_battery, 10)
        self.create_subscription(Int32MultiArray, 'rrc/status', self.on_status, 10)
        self.last_status = None
        self.imu_count = 0
        self.create_timer(10.0, self.log_rates)
        self.get_logger().info('rrc_bridge up: gyro_bias=%s' % self.gyro_bias)

# 한글: MCU IMU(base_link 축, bias 미보정)에서 설정된 자이로 bias를 빼서 /imu/data_raw로 재발행한다. MCU 시각이 아직 동기화 전이면(0) 호스트 시각을 쓴다.
    def on_imu(self, msg):
        out = Imu()
        out.header = msg.header
        if out.header.stamp.sec == 0 and out.header.stamp.nanosec == 0:
            out.header.stamp = self.get_clock().now().to_msg()  # MCU time not synced yet
        out.header.frame_id = self.imu_frame
        out.orientation_covariance = msg.orientation_covariance
        out.linear_acceleration = msg.linear_acceleration
        out.linear_acceleration_covariance = msg.linear_acceleration_covariance
        out.angular_velocity.x = msg.angular_velocity.x - self.gyro_bias[0]
        out.angular_velocity.y = msg.angular_velocity.y - self.gyro_bias[1]
        out.angular_velocity.z = msg.angular_velocity.z - self.gyro_bias[2]
        out.angular_velocity_covariance = msg.angular_velocity_covariance
        self.imu_pub.publish(out)
        self.imu_count += 1

# 한글: 엔코더 기반 실측 바퀴 속도 → /wheel_twist(EKF 입력). 공분산은 설정값(실주행 비교 전까지 미검증).
    def on_wheel(self, msg):
        if len(msg.data) < 4:
            return
        vx, vy, wz = mecanum_forward(msg.data[:4], self.wheelbase, self.track_width, self.wheel_diameter)
        out = TwistWithCovarianceStamped()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = self.base_frame
        out.twist.twist.linear.x = vx
        out.twist.twist.linear.y = vy
        out.twist.twist.angular.z = wz
        out.twist.covariance[0] = self.cov[0]
        out.twist.covariance[7] = self.cov[1]
        out.twist.covariance[35] = self.cov[2]
        self.twist_pub.publish(out)

# 한글: 배터리 상태 재발행 + 저전압 경고(30초 제한).
    def on_battery(self, msg):
        if msg.header.stamp.sec == 0 and msg.header.stamp.nanosec == 0:
            msg.header.stamp = self.get_clock().now().to_msg()
        self.batt_pub.publish(msg)
        if msg.voltage < self.low_battery:
            self.get_logger().warn('Battery low: %.2f V (charge below %.1f V)' % (msg.voltage, self.low_battery),
                                   throttle_duration_sec=30.0)

# 한글: MCU 상태(e-stop, 모터 fault, 정지 사유)가 바뀔 때만 로그를 남긴다. fault/e-stop이면 경고 수준.
    def on_status(self, msg):
        d = list(msg.data)
        if len(d) < 10:
            return
        if self.last_status is not None and d[:8] == self.last_status[:8]:
            return
        self.last_status = d
        flags = [name for bit, name in STATUS_FLAGS.items() if d[0] & bit]
        faults = ['M%d: %s' % (i, FAULTS.get(d[4 + i], str(d[4 + i]))) for i in range(4) if d[4 + i]]
        text = 'MCU status: flags=%s stop_reason=%s imu_kind=%d comm=%d uptime=%.1fs reset_cause=0x%02X' % (
            ','.join(flags) or '-', STOP_REASONS.get(d[1], d[1]), d[2], d[3], d[8] / 1000.0, d[9] & 0xFF)
        if faults or (d[0] & (0x01 | 0x10)):
            self.get_logger().warn(text + (' faults: ' + '; '.join(faults) if faults else ''))
        else:
            self.get_logger().info(text)

    def log_rates(self):
        self.get_logger().info('imu %.1f Hz' % (self.imu_count / 10.0))
        self.imu_count = 0


def main(args=None):
    rclpy.init(args=args)
    node = RrcBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
