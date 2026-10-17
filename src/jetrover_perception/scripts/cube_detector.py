#!/usr/bin/env python3
# 한글: 색 큐브 찾기 — RGB 영상에서 HSV 범위로 빨강/초록/파랑 영역을 찾고, 그 영역 depth 중앙값과
#       카메라 내부 파라미터로 3D 점을 만들어 TF로 target_frame(기본 base_footprint) 좌표로 바꿔
#       cubes/<색>(PointStamped)으로 낸다. 실기·Gazebo 토픽과 형식이 같다(color rgb8, depth 16UC1 mm,
#       depth가 color에 정렬됨 — 2026-10-14 bag에서 확인). 점은 카메라가 본 표면(보통 윗면) 위치다.
"""
Colour-cube detector: HSV blobs + aligned depth -> 3D points in target_frame.

Topics in: depth_cam/color/image_raw (rgb8), depth_cam/depth/image_raw (16UC1 mm, aligned
to colour), depth_cam/color/camera_info. Out: cubes/red|green|blue (geometry_msgs/PointStamped
in target_frame, the observed surface point) and cubes/debug (rgb8 with the blobs drawn).
The same topics exist on the robot and in Gazebo. The pure helpers (colour_masks,
largest_blob, blob_depth_m, pixel_to_point) are unit-tested without ROS.
"""
import math

import numpy as np

# HSV(OpenCV: H 0..179) 범위 — Gazebo 큐브는 순색이라 넉넉히 맞는다. 실기 큐브는 확인 후 조정.
# HSV ranges (OpenCV H is 0..179). Red wraps around 0, hence two ranges.
DEFAULT_RANGES = {
    'red': [((0, 120, 70), (10, 255, 255)), ((170, 120, 70), (179, 255, 255))],
    'green': [((40, 100, 50), (85, 255, 255))],
    'blue': [((100, 120, 50), (130, 255, 255))],
}


def colour_masks(rgb, ranges=DEFAULT_RANGES):
    """Return {colour: uint8 mask 0/255} for an RGB uint8 image. 한글: 색별 마스크."""
    import cv2
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    out = {}
    for name, rs in ranges.items():
        m = np.zeros(rgb.shape[:2], np.uint8)
        for lo, hi in rs:
            m |= cv2.inRange(hsv, np.array(lo, np.uint8), np.array(hi, np.uint8))
        # 작은 점 잡음 제거 / remove speckles
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        out[name] = m
    return out


def largest_blob(mask, min_area):
    """Largest connected blob: (u, v, area, blob_mask) or None if none reaches min_area pixels."""
    import cv2
    n, labels, stats, cents = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if n <= 1:
        return None
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    area = int(stats[k, cv2.CC_STAT_AREA])
    if area < min_area:
        return None
    return float(cents[k][0]), float(cents[k][1]), area, (labels == k)


def blob_depth_m(depth_mm, blob, max_depth_m):
    """Median depth (m) of the blob's valid pixels, or None. 한글: 영역 안 유효 depth의 중앙값."""
    d = depth_mm[blob]
    d = d[(d > 0) & (d < max_depth_m * 1000.0)]
    if d.size < 5:
        return None
    return float(np.median(d)) / 1000.0


def pixel_to_point(u, v, z, k):
    """Back-project a pixel into the optical frame (x right, y down, z fwd); k: 3x3 row-major."""
    fx, cx, fy, cy = k[0], k[2], k[4], k[5]
    return ((u - cx) * z / fx, (v - cy) * z / fy, z)


def correct_pitch(y, z, pitch):
    """Rotate an optical-frame point (y down, z forward) so a camera pitched `pitch` rad further down
    than modelled maps into the model's optical frame. 한글: 모델보다 더 숙인 카메라의 점을 모델 좌표로."""
    c, s = math.cos(pitch), math.sin(pitch)
    return y * c + z * s, -y * s + z * c


def main():
    import cv2
    import rclpy
    import tf2_geometry_msgs  # noqa: F401  (registers PointStamped with tf2)
    from cv_bridge import CvBridge
    from geometry_msgs.msg import PointStamped
    from rclpy.duration import Duration
    from rclpy.node import Node
    from rclpy.qos import qos_profile_sensor_data
    from rclpy.time import Time
    from sensor_msgs.msg import CameraInfo, Image
    from tf2_ros import Buffer, TransformListener

    class CubeDetector(Node):
        def __init__(self):
            super().__init__('cube_detector')
            self.target = self.declare_parameter('target_frame', 'base_footprint').value
            self.min_area = int(self.declare_parameter('min_area_px', 60).value)
            self.max_depth = float(self.declare_parameter('max_depth_m', 1.2).value)
            self.max_dt = float(self.declare_parameter('max_color_depth_dt_s', 0.15).value)
            self.colours = list(self.declare_parameter('colours', ['red', 'green', 'blue']).value)
            self.bridge = CvBridge()
            self.k = None
            self.depth = None
            self.tf = Buffer()
            # 리스너를 별도 스레드로: 콜백 안에서 TF를 기다리는 동안 갱신이 멈추면
            # "미래 시각"으로 거부됐다(Gazebo, 2026-10-17)
            # node=None으로 리스너 전용 노드를 만든다: 이 노드(self)를 넘기면 뒤의 rclpy.spin()이
            # 노드를 메인 executor로 가져가 TF가 영상 콜백과 한 스레드에서 처리되고, 실기 30 Hz
            # 영상에 밀려 TF가 3~7 s 늦었다(2026-10-18, 시뮬레이션은 영상이 느려 드러나지 않음).
            # Own thread: waiting for TF inside the callback otherwise blocks the updates
            # it is waiting for. node=None gives the listener its own node: with self, the
            # later rclpy.spin() took the node back into the main executor and the TF fell
            # 3-7 s behind the 30 Hz camera on the robot.
            self.tf_listener = TransformListener(self.tf, None, spin_thread=True)
            self.tf_timeout = float(self.declare_parameter('tf_timeout_s', 0.3).value)
            self.max_tf_lag = float(self.declare_parameter('max_tf_lag_s', 3.0).value)
            # 카메라가 URDF 모델보다 아래로 더 숙인 각도(deg). 실기 바닥 평면 측정 7개 자세에서 +4.9°
            # (오차 rms 1°, docs/benchmarks/arm_floor_calib_20261018.md). 시뮬레이션은 0.
            # Extra downward pitch of the real camera vs the URDF (floor-plane fit, 7 poses). 0 in sim.
            self.pitch_off = math.radians(
                float(self.declare_parameter('pitch_offset_deg', 0.0).value))
            self.latest_tf_uses = 0
            self.pubs = {c: self.create_publisher(PointStamped, f'cubes/{c}', 10)
                         for c in self.colours}
            self.debug = self.create_publisher(Image, 'cubes/debug', 2)
            self.create_subscription(CameraInfo, 'depth_cam/color/camera_info',
                                     lambda m: setattr(self, 'k', list(m.k)),
                                     qos_profile_sensor_data)
            self.create_subscription(Image, 'depth_cam/depth/image_raw', self.on_depth,
                                     qos_profile_sensor_data)
            self.create_subscription(Image, 'depth_cam/color/image_raw', self.on_color,
                                     qos_profile_sensor_data)
            self.get_logger().info(
                f'cube detector: {self.colours} -> cubes/<colour> in {self.target}')

        def to_target(self, p, t_img):
            """Point into target_frame at the image time, else with the latest TF if lag <= max."""
            # 영상 시각의 TF가 없으면(시뮬레이션에서 TF가 영상보다 약 1.8 s 늦게 오기도 함, 2026-10-17)
            # 가장 최근 TF를 쓴다 —
            # 관찰 자세에 멈춰 있을 때 인식하므로 오차가 작다. max_tf_lag_s보다 오래된 TF는 쓰지 않는다.
            # Fall back to the latest TF (the arm is still at the viewing pose) unless it is
            # older than max_tf_lag_s.
            try:
                return self.tf.transform(p, self.target, timeout=Duration(seconds=self.tf_timeout))
            except Exception as e:   # noqa: BLE001  (tf2 raises several exception types)
                first_error = e
            try:
                tr = self.tf.lookup_transform(self.target, p.header.frame_id, Time())
            except Exception as e:   # noqa: BLE001
                self.get_logger().warn(f'TF {p.header.frame_id} -> {self.target}: '
                                       f'{first_error}; {e}',
                                       throttle_duration_sec=5.0)
                return None
            lag = t_img - (tr.header.stamp.sec + tr.header.stamp.nanosec * 1e-9)
            if lag > self.max_tf_lag:
                self.get_logger().warn(f'latest TF is {lag:.2f} s older than the image: skipped',
                                       throttle_duration_sec=5.0)
                return None
            self.latest_tf_uses += 1
            if self.latest_tf_uses % 100 == 1:
                self.get_logger().info(f'using the latest TF ({lag:.2f} s older than the image); '
                                       f'{self.latest_tf_uses} times so far')
            return tf2_geometry_msgs.do_transform_point(p, tr)

        def on_depth(self, m):
            self.depth = m

        def on_color(self, m):
            if self.k is None or self.depth is None:
                return
            t_c = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
            t_d = self.depth.header.stamp.sec + self.depth.header.stamp.nanosec * 1e-9
            if abs(t_c - t_d) > self.max_dt:
                return
            rgb = self.bridge.imgmsg_to_cv2(m, 'rgb8')
            depth = self.bridge.imgmsg_to_cv2(self.depth, 'passthrough')
            if depth.shape[:2] != rgb.shape[:2]:
                self.get_logger().warn('depth and colour sizes differ: not aligned',
                                       throttle_duration_sec=5.0)
                return
            dbg = rgb.copy()
            masks = colour_masks(rgb, {c: DEFAULT_RANGES[c] for c in self.colours})
            for c, mask in masks.items():
                blob = largest_blob(mask, self.min_area)
                if blob is None:
                    continue
                u, v, area, bm = blob
                z = blob_depth_m(depth, bm, self.max_depth)
                if z is None:
                    continue
                x, y, z = pixel_to_point(u, v, z, self.k)
                y, z = correct_pitch(y, z, self.pitch_off)
                p = PointStamped()
                p.header = m.header
                p.point.x, p.point.y, p.point.z = x, y, z
                q = self.to_target(p, t_c)
                if q is None:
                    continue
                self.pubs[c].publish(q)
                cv2.circle(dbg, (int(u), int(v)), 6, (255, 255, 255), 2)
                cv2.putText(dbg, f'{c} {q.point.x:.3f},{q.point.y:.3f}', (int(u) + 8, int(v)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            out = self.bridge.cv2_to_imgmsg(dbg, 'rgb8')
            out.header = m.header
            self.debug.publish(out)

    rclpy.init()
    rclpy.spin(CubeDetector())


if __name__ == '__main__':
    main()
