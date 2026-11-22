#!/usr/bin/python3
"""Observe ROS sensors only; never publish or send actions.

한글: ROS 센서만 관찰하며 발행이나 액션 전송은 하지 않는다.
"""
import base64
import json
import math
import os
from pathlib import Path
import time

import cv2
from cv_bridge import CvBridge, CvBridgeError

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.parameter_client import AsyncParameterClient
from diagnostic_msgs.msg import DiagnosticArray
from sensor_msgs.msg import BatteryState, CameraInfo, Image, Imu, JointState, LaserScan, PointCloud2
from nav_msgs.msg import Odometry
from camera_info_status import camera_info_snapshot
from arm_observation import arm_observation, valid_mapping
from wheel_observation import wheel_feedback_snapshot
from odom_observation import OdomTracker


class SensorMonitor(Node):
    """Track recent topic counts and battery voltage. / 최근 토픽 수신율과 배터리 전압을 추적한다."""
    def __init__(self):
        super().__init__('jetinspect_ops_monitor')
        self.samples = {name: [] for name in ('imu', 'scan', 'camera', 'depth_obstacles')}
        self.battery = None
        self.battery_time = 0.0
        self.camera_info = {'color': None, 'depth': None}
        self.wheel_feedback = None
        self.odom = {'raw': OdomTracker(), 'ekf': OdomTracker()}
        self.arm_mapping, self.arm_mapping_at = {}, 0.0
        self.arm_offsets = {}
        self.arm_joints, self.arm_joint_at = {}, 0.0
        self.arm_diagnostics, self.arm_diagnostics_at = {}, 0.0
        self.arm_parameters = AsyncParameterClient(self, '/base_node')
        self.arm_parameter_future = None
        self.arm_parameter_started = 0.0
        self.bridge = CvBridge()
        self.last_preview = 0.0
        self.pair_color = None
        self.pair_saved_stamp = None
        for name, topic, message_type in (('imu', '/imu/data_raw', Imu), ('scan', '/scan', LaserScan)):
            self.create_subscription(message_type, topic, lambda message, name=name: self.received(name), qos_profile_sensor_data)
        self.create_subscription(PointCloud2, '/depth_cam/depth/points_sparse', lambda msg: self.received('depth_obstacles'), qos_profile_sensor_data)
        self.create_subscription(Image, '/depth_cam/color/image_raw', self.camera_received, qos_profile_sensor_data)
        self.create_subscription(Image, '/depth_cam/depth/image_raw', self.depth_received, qos_profile_sensor_data)
        self.create_subscription(BatteryState, '/battery_state', self.battery_received, qos_profile_sensor_data)
        for name in ('color', 'depth'):
            self.create_subscription(CameraInfo, f'/depth_cam/{name}/camera_info',
                                     lambda msg, name=name: self.camera_info_received(name, msg), qos_profile_sensor_data)
        self.create_subscription(JointState, '/joint_states', self.arm_joint_received, 10)
        self.create_subscription(DiagnosticArray, '/arm/servo_stats', self.arm_stats_received, 10)
        self.create_subscription(DiagnosticArray, '/wheel/feedback', self.wheel_feedback_received, qos_profile_sensor_data)
        for key, topic in (('raw','/odom_raw'), ('ekf','/odom')):
            self.create_subscription(Odometry, topic, lambda msg, key=key: self.odom[key].update(msg, time.time()), 10)
        self.create_timer(5.0, self.request_arm_mapping)
        # Keep snapshot intervals below the 1.5 s servo freshness limit.
        # 한글: 스냅샷 간격을 서보 신선도 제한 1.5초보다 짧게 유지한다.
        self.create_timer(0.5, self.write_status)

    def received(self, name):
        """Record a timestamp, discarding samples older than ten seconds. / 10초 이내 수신 시각만 보관한다."""
        now = time.time()
        self.samples[name] = [stamp for stamp in self.samples[name] if 0 <= now - stamp < 10] + [now]

    def camera_received(self, msg):
        """Track frames and save a bounded preview. / 프레임을 추적하고 저빈도 미리보기를 저장한다."""
        self.received('camera')
        now = time.monotonic()
        if now - self.last_preview < 1.0:
            return
        self.last_preview = now
        try:
            image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            ok, encoded = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if not ok:
                return
            directory = Path.home() / '.local/share/jetinspect-ops/run'
            directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            temporary = directory / 'camera-preview.tmp'
            temporary.write_bytes(encoded.tobytes())
            os.replace(temporary, directory / 'camera-preview.jpg')
            stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            if stamp > 0 and msg.header.frame_id and len(encoded) <= 2_000_000:
                self.pair_color = {'stamp': stamp, 'frame_id': msg.header.frame_id, 'width': msg.width,
                                   'height': msg.height, 'jpeg': base64.b64encode(encoded.tobytes()).decode('ascii')}
            # Preserve the BGR-converted camera frame losslessly for calibration.
            # 한글: 보정에는 BGR 변환된 카메라 프레임을 무손실로 보관한다.
            ok, lossless = cv2.imencode('.png', image, [cv2.IMWRITE_PNG_COMPRESSION, 1])
            if ok and len(lossless) <= 4_000_000:
                temporary = directory / 'camera-calibration.tmp'
                temporary.write_bytes(lossless.tobytes())
                os.replace(temporary, directory / 'camera-calibration.png')
        except (CvBridgeError, cv2.error, OSError) as exc:
            self.get_logger().warning(f'camera preview unavailable: {exc}', throttle_duration_sec=30.0)

    def depth_received(self, msg):
        """Save a bounded time-matched color/depth pair for visual inspection.

        한글: 시각이 일치하는 제한된 컬러·깊이 영상 쌍을 시각 검사용으로 저장한다.
        """
        color = self.pair_color
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        if (not color or self.pair_saved_stamp == color['stamp'] or msg.encoding != '16UC1' or
                msg.header.frame_id != color['frame_id'] or (msg.width, msg.height) != (color['width'], color['height']) or
                not math.isfinite(stamp) or stamp <= 0 or abs(stamp-color['stamp']) > .15):
            return
        try:
            depth = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
            gray = cv2.convertScaleAbs(depth, alpha=255.0/4000.0)
            colored = cv2.applyColorMap(gray, cv2.COLORMAP_TURBO)
            colored[depth == 0] = 0
            ok, encoded = cv2.imencode('.jpg', colored, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if not ok or len(encoded) > 2_000_000:
                return
            pair = {'color_jpeg':color['jpeg'], 'depth_jpeg':base64.b64encode(encoded.tobytes()).decode('ascii'),
                    'width':msg.width, 'height':msg.height, 'frame_id':msg.header.frame_id,
                    'color_stamp':color['stamp'], 'depth_stamp':stamp, 'created_at':time.time()}
            directory = Path.home() / '.local/share/jetinspect-ops/run'
            directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            temporary = directory / 'rgb-depth-pair.tmp'
            temporary.write_text(json.dumps(pair))
            os.replace(temporary, directory / 'rgb-depth-pair.json')
            self.pair_saved_stamp = color['stamp']
        except (CvBridgeError, cv2.error, OSError, TypeError, ValueError) as exc:
            self.get_logger().warning(f'rgb-depth pair unavailable: {exc}', throttle_duration_sec=30.0)

    def camera_info_received(self, name, msg):
        """Record observed intrinsics separately for color and depth.

        한글: 컬러와 깊이 내부 파라미터를 별도로 관찰해 기록한다.
        """
        self.camera_info[name] = camera_info_snapshot(msg, time.time())

    def wheel_feedback_received(self, msg):
        """Keep only a valid full four-port feedback message.

        한글: 유효한 네 포트 전체 피드백 메시지만 보관한다.
        """
        self.wheel_feedback = wheel_feedback_snapshot(msg.status, time.time())

    def request_arm_mapping(self):
        """Read mapping from the running base node; do not change parameters.

        한글: 실행 중인 base 노드의 대응표만 읽으며 파라미터를 변경하지 않는다.
        """
        if self.arm_parameter_future is not None and not self.arm_parameter_future.done():
            if time.monotonic() - self.arm_parameter_started < 5.0:
                return
            # A restarted service may never answer an in-flight request; drop it before retrying.
            # 한글: 서비스 재시작으로 응답 없는 요청을 폐기하고 다음 조회를 허용한다.
            expired = self.arm_parameter_future
            self.arm_parameter_future = None
            self.arm_mapping, self.arm_mapping_at, self.arm_offsets = {}, 0.0, {}
            expired.cancel()
        if not self.arm_parameters.services_are_ready():
            return
        self.arm_parameter_future = self.arm_parameters.get_parameters(['arm_joint_names', 'arm_servo_ids', 'arm_joint_offsets_rad'])
        self.arm_parameter_started = time.monotonic()
        self.arm_parameter_future.add_done_callback(self.arm_mapping_received)

    def arm_mapping_received(self, future):
        """Accept only a complete one-to-one mapping. / 일대일 대응표만 수락한다."""
        if future is not self.arm_parameter_future:
            return
        try:
            values = future.result().values
            names = list(values[0].string_array_value)
            mapping = valid_mapping(names, list(values[1].integer_array_value))
            offsets = list(values[2].double_array_value)
            if not mapping or len(offsets) != len(names) or any(not math.isfinite(value) or abs(value) > 6.3 for value in offsets):
                raise ValueError('invalid_arm_parameters')
            self.arm_offsets = dict(zip(names, offsets))
            self.arm_mapping, self.arm_mapping_at = mapping, time.time()
        except Exception as exc:
            self.arm_mapping, self.arm_mapping_at = {}, 0.0
            self.arm_offsets = {}
            self.get_logger().warning(f'arm mapping unavailable: {exc}', throttle_duration_sec=30.0)

    def arm_joint_received(self, msg):
        """Keep only finite current joint messages. / 유한한 관절 메시지만 유지한다."""
        if len(msg.name) != len(msg.position) or len(set(msg.name)) != len(msg.name):
            self.arm_joints, self.arm_joint_at = {}, 0.0
            return
        self.arm_joints = {name: value for name, value in zip(msg.name, msg.position) if math.isfinite(value)}
        self.arm_joint_at = time.time()

    def arm_stats_received(self, msg):
        """Record diagnostic ages, not message timestamps as servo freshness.

        한글: 메시지 시각이 아닌 실제 서보 응답 경과 시간을 기록한다.
        """
        ages = {}
        for status in msg.status:
            try:
                servo = int(status.hardware_id)
                values = {v.key: v.value for v in status.values}
                age = float(values['age_s'])
                if servo in ages or not math.isfinite(age):
                    self.arm_diagnostics, self.arm_diagnostics_at = {}, 0.0
                    return
                ages[servo] = age
            except (KeyError, ValueError, TypeError):
                continue
        self.arm_diagnostics, self.arm_diagnostics_at = ages, time.time()

    def battery_received(self, msg):
        """Record valid voltage with its observation time. / 유효 전압과 수신 시각을 기록한다."""
        self.battery = msg.voltage if math.isfinite(msg.voltage) and msg.voltage > 0 else None
        self.battery_time = time.time()

    def write_status(self):
        """Atomically publish a status snapshot in the private runtime directory.

        한글: 사용자 전용 디렉터리에 상태 스냅샷을 원자적으로 기록한다.
        """
        now = time.time()
        streams = {}
        for name, stamps in self.samples.items():
            current = [stamp for stamp in stamps if 0 <= now - stamp < 10]
            self.samples[name] = current
            streams[name] = {'hz': round((len(current) - 1) / (current[-1] - current[0]), 1) if len(current) > 1 and current[-1] > current[0] else None,
                             'age_seconds': round(now - current[-1], 1) if current else None,
                             'received_at': current[-1] if current else None}
        sources = [self.get_publishers_info_by_topic(topic) for topic in ('/joint_states', '/arm/servo_stats')]
        confirmed = all(len(items) == 1 and items[0].node_name == 'base_node' and items[0].node_namespace == '/' for items in sources)
        output = {'timestamp': now, 'streams': streams, 'camera_info': self.camera_info, 'wheel_feedback': self.wheel_feedback, 'odometry': {key: tracker.value for key, tracker in self.odom.items()},
                  'arm': arm_observation(self.arm_mapping, self.arm_mapping_at, self.arm_joints, self.arm_joint_at,
                                         self.arm_diagnostics, self.arm_diagnostics_at, now, self.arm_offsets, confirmed),
                  'battery_voltage': self.battery if 0 <= now - self.battery_time < 10 else None,
                  'battery_received_at': self.battery_time if self.battery is not None and 0 <= now - self.battery_time < 10 else None}
        directory = Path.home() / '.local/share/jetinspect-ops/run'
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        temp = directory / 'ros-status.tmp'
        temp.write_text(json.dumps(output))
        os.replace(temp, directory / 'ros-status.json')


def main():
    """Run until stopped without starting any robot nodes. / 로봇 노드를 기동하지 않고 종료까지 관찰한다."""
    rclpy.init()
    node = SensorMonitor()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
