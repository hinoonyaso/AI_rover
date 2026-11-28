#!/usr/bin/env python3
# 한글: 간격을 둔 depth 영상으로 만드는 가벼운 PointCloud2 + 기준 depth 대비 새 물체만 남기는 self-filter.
"""Lightweight PointCloud2 from a strided (downsampled) depth image.

The camera driver's own enable_point_cloud computes a full-resolution cloud
(up to ~230k points for 640x360) internally and was the direct cause of
troubleshooting/019's silent hangs under the full Nav2 stack -- the heavy
work happens before anything is even published, so downsampling downstream
(e.g. on the host, or with a voxel filter after the fact) doesn't help.

This instead samples every `stride`-th pixel from the already-working
depth/image_raw BEFORE projecting to 3D, so the expensive part (per-pixel
XYZ math) only ever runs on a small fraction of the points. stride=8 on
640x360 depth gives at most 80x45 = 3600 points, vs ~230k for the full
cloud -- close to what a Nav2 voxel/obstacle layer would keep anyway after
its own internal downsampling, so there is little practical loss for that
use case (see PRD 3D XYZ / Safety Manager pipelines, neither of which needs
a dense cloud).

Self-filtering (2026-10-05, checklist 8.12, troubleshooting/023): with the arm in its home pose
the camera sees the robot's own wheel (that is the point -- it closes the near-field blind
zone, see base.yaml's arm_home_pose_rad comment). Feeding those self-points into Nav2's
obstacle_layer would mark the robot's own footprint as occupied and reintroduce
troubleshooting/020's "Start occupied" problem.

The first attempt at this (transform each point into base_footprint and drop anything inside
the robot's footprint rectangle) was wrong: a real external obstacle placed ~35cm in front of
the robot projects into that same rectangle too (the camera is forward-mounted and tilted
down, so near-field obstacles and the robot's own wheel land in overlapping XY once
transformed), and the robot's wheel height (~9.7cm) overlaps the height range of a real low
obstacle -- so neither XY nor height alone can tell them apart (troubleshooting/023: this
let the robot push an obstacle it never even published as a point).

Instead this compares each pixel's depth against a one-time reference depth image captured
with the arm in its home pose and nothing in front of the robot (`depth_background_ref.npy` --
recapture if the home pose changes). The robot's own wheel/chassis always measures ~the same
depth as that reference (nothing moved). Anything that now measures *closer* than the
reference by more than a margin is something new between the camera and that known
background -- a real obstacle, regardless of where it lands in XY. This has no failure mode
tied to the obstacle's position or height matching the wheel's.

Home-pose gate (2026-10-07, troubleshooting/031): that reference is only valid while the arm
(and therefore the camera) is at the pose it was captured in. If the arm is elsewhere, the
floor itself differs from the reference and shows up as obstacles (or real obstacles are
missed), so this node stops publishing until /joint_states is back within tolerance of the
home pose. Withholding the cloud is deliberate: collision_monitor treats the depth source as
stale after its source_timeout and stops the robot, i.e. no navigation on an invalid reference.
한글: 기준 depth는 그걸 찍은 팔 자세에서만 유효하다. 팔이 홈 자세에서 벗어나면 발행을 멈추고,
collision_monitor가 source_timeout 후 로봇을 세운다(잘못된 기준으로 주행하지 않게 하는 의도된 동작).
"""
import os
import time
import hashlib
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import TransformStamped
from sensor_msgs.msg import CameraInfo, Image, JointState, PointCloud2, PointField
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Header
from tf2_ros import Buffer, StaticTransformBroadcaster, TransformException, TransformListener

# Static frame at the camera position with base_footprint's axes (floor-aware mode). The voxel layer
# raytraces from the cloud frame's origin, so it must stay at the camera (rays to the floor behind a
# low box pass above it, S4); a static frame also means the costmap needs no arm TF at the image stamp.
# 한글: 카메라 위치에 base_footprint 축 방향의 정적 프레임. voxel 층은 점군 프레임 원점에서 광선을 쏘므로
# 원점이 카메라에 있어야 하고(S4), 정적이라 코스트맵이 영상 시각의 팔 TF를 기다리지 않는다.
FLOOR_ORIGIN_FRAME = 'depth_floor_origin'


def quat_to_matrix(q):
    """Rotation matrix of a geometry_msgs Quaternion. / 쿼터니언 -> 회전 행렬."""
    x, y, z, w = q.x, q.y, q.z, q.w
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def fit_floor_plane(points, min_samples=30, inlier_m=0.01, min_inlier_fraction=0.5):
    """Least-squares plane z = a*x + b*y + c, refit once on the inliers (drops a low object's top).

    한글: 최소제곱 평면 z = ax + by + c. 한 번 맞춘 뒤 잔차 inlier_m 안의 점으로 다시 맞춘다(낮은 물체 윗면 제거).
    """
    if len(points) < min_samples:
        return None
    a = np.column_stack((points[:, 0], points[:, 1], np.ones(len(points))))
    coef = np.linalg.lstsq(a, points[:, 2], rcond=None)[0]
    keep = np.abs(a @ coef - points[:, 2]) <= inlier_m
    # Most candidates must lie on the plane, otherwise it is not the floor. / 대부분이 평면 위여야 바닥이다.
    if keep.sum() < max(min_samples, min_inlier_fraction * len(points)):
        return None
    return np.linalg.lstsq(a[keep], points[keep, 2], rcond=None)[0]


def floor_plane_points(depth, background, us, vs, intrinsics, rotation, translation, margin_mm,
                       raised_m=0.02, max_tilt_rad=0.21, max_offset_m=0.10, window_m=0.08):
    """Obstacle/free masks and base_footprint points whose z is the height above the floor seen now.

    2026-11-25 (troubleshooting/061): the camera is on the arm, so a small error between the joint
    readings and the real arm pose (servo backlash) tilts the camera TF and a 5 cm box read 2..9 cm
    high. The floor visible in the same frame (pixels that still match the background and lie near
    the nominal floor) is fitted with a plane and heights are measured from it, which cancels that
    tilt. Real robot 2026-11-28: the fitted floor was 6.8 deg tilted and 5.0 cm low at the robot
    centre in the TF's base_footprint, so the limits (12 deg, 10 cm, +-8 cm candidate window) leave
    room for that. Returns None when the floor is not visible enough or the plane is implausible.
    한글: 카메라가 팔에 달려 관절 읽기값과 실제 자세의 작은 차이(백래시)로 카메라 TF가 기울어 5 cm 상자가
    2~9 cm로 읽혔다. 같은 프레임에 보이는 바닥(기준과 같고 명목 바닥 근처인 픽셀)으로 평면을 맞추고
    높이를 그 평면에서 잰다. 실기(11-28): TF 기준 바닥이 6.8° 기울고 로봇 중심에서 5.0 cm 낮아
    한계를 12°/10 cm/±8 cm로 둔다. 바닥이 충분히 안 보이거나 평면이 비정상이면 None.
    """
    fx, fy, cx, cy = intrinsics
    present = (depth > 0) & (background > 0)
    delta = background.astype(np.int32) - depth.astype(np.int32)

    def to_base(depth_mm):
        z = depth_mm.astype(np.float32) / 1000.0
        cam = np.stack(((us - cx) * z / fx, (vs - cy) * z / fy, z), axis=-1)
        return cam @ rotation.T + translation

    now = to_base(depth)
    ref = to_base(background)
    candidates = present & (np.abs(delta) <= margin_mm) & (np.abs(ref[..., 2]) <= window_m) & (
        np.abs(now[..., 2]) <= window_m)
    plane = fit_floor_plane(now[candidates])
    if plane is None:
        return None
    if np.arctan(np.hypot(plane[0], plane[1])) > max_tilt_rad or abs(plane[2]) > max_offset_m:
        return None

    def above(points):
        return points[..., 2] - (plane[0] * points[..., 0] + plane[1] * points[..., 1] + plane[2])

    height = above(now)
    reference_floor = present & (np.abs(above(ref)) <= 0.025)
    raised = height >= raised_m
    # A raised pixel is an obstacle if it is closer than the background by the margin, or (where the
    # background is floor) by only 10 mm: a low object barely changes the depth at a grazing angle.
    # 한글: 기준보다 margin 이상 가깝거나, 기준이 바닥인 곳에선 10 mm만 가까워도 높이가 있으면 장애물.
    obstacle = present & raised & ((delta > margin_mm) | (reference_floor & (delta > 10)))
    free = present & (np.abs(delta) <= margin_mm) & ~obstacle & ~(reference_floor & raised)
    now[..., 2] = height
    return obstacle, free, now, plane


class SparsePointCloud(Node):
    def __init__(self):
        super().__init__('sparse_point_cloud')
        # 한글: stride=8이면 640x360 depth에서 최대 약 3600점(전체는 약 23만점). 3D 투영 연산을 점 수가 적은 단계에서만 한다.
        self.declare_parameter('stride', 8)
        self.declare_parameter('floor_aware', False)
        self.floor_aware = self.get_parameter('floor_aware').value
        # floor_aware (2026-11-25): uses the LATEST camera TF instead of waiting for the image stamp.
        # The arm is static whenever the home-pose gate is open, and joint_states (5 Hz) left the TF
        # at the image stamp missing for 30..65% of frames. 한글: 영상 시각 대신 최신 카메라 TF를 쓴다.
        # 게이트가 열려 있으면 팔은 정지 상태이고, 5 Hz joint_states 때문에 영상 시각 TF가 30~65% 없었다.
        self.declare_parameter('floor_raised_m', 0.02)
        self.floor_raised = float(self.get_parameter('floor_raised_m').value)
        if self.floor_aware:
            self.tf_buffer = Buffer()
            self.tf_listener = TransformListener(self.tf_buffer, self)
            self.static_tf = StaticTransformBroadcaster(self)
            self.origin_xyz = None
        # 한글: 발행 속도를 4프레임에 1번으로 낮춘다(원격 RViz에서 TF 타이밍 경쟁 방지).
        # Publishing at the full depth rate (~25-30Hz) meant a remote viewer
        # (RViz over WiFi) sometimes couldn't resolve the full TF chain in
        # time for a given message's exact stamp -- same class of cross-
        # machine timing race as troubleshooting/018, just for this topic.
        # Harmless (the viewer keeps showing the last good cloud) but noisy.
        # A live view doesn't need more than a few Hz.
        self.declare_parameter('process_every_nth', 4)
        default_ref = os.path.join(
            get_package_share_directory('jetrover_perception'),
            'config', 'depth_background_ref.npy')
        self.declare_parameter('background_depth_path', default_ref)
        self.declare_parameter('background_calibration_path', '')
        self.declare_parameter('background_calibration_sha256', '')
        self.declare_parameter('expected_depth_frame', '')
        self.expected_depth_frame = self.get_parameter('expected_depth_frame').value
        self.intrinsics_frame = None
        self.background_calibration_path = self.get_parameter('background_calibration_path').value
        self.background_calibration_sha256 = self.get_parameter('background_calibration_sha256').value
        # mm, margin above typical depth-sensor noise at this range (troubleshooting/023).
        # 30 -> 60 (2026-10-05): with the wrist-raised home pose the camera sees the far floor, where
        # the noise exceeds 30 mm (~12 false points/frame, 0.9 at 60). A real box is >100 mm closer.
        # 한글: 손목을 든 새 홈 자세는 먼 바닥까지 보여서 노이즈가 커짐 → 거짓 점이 30mm에서 프레임당 약 12개, 60mm에서 약 1개.
        self.declare_parameter('background_margin_mm', 60)
        # 2026-10-05 (회피 시험): the camera only sees an obstacle's FRONT face, so the space behind it
        # stays "free" in the costmap and the robot (and line waypoints) drove into the box body.
        # Every obstacle point is therefore extended along its viewing ray by `extrude_depth_m`.
        # 한글: 카메라는 장애물 앞면만 보므로 시선 방향으로 뒤쪽 extrude_depth_m(기본 0.3m)까지 점을 복제해
        # 몸통도 점유로 취급한다(상자를 치고 지나가던 문제). 현재 기본값은 아래 0.15m.
        self.declare_parameter('extrude_depth_m', 0.15)  # 0.3 -> 0.15 (2026-10-06): 좁은 방에서 붉은 영역이 너무 커서 통로가 막혔다
        self.declare_parameter('extrude_step_m', 0.1)
        self.extrude_depth = self.get_parameter('extrude_depth_m').value
        self.extrude_step = self.get_parameter('extrude_step_m').value
        # Clearing cloud (2026-10-22, checklist 8.16, troubleshooting/053): the obstacle cloud
        # holds ONLY obstacle points, so when an obstacle leaves there is no ray to clear its
        # cells and the mark stays in the costmap. With publish_clearing, pixels that match the
        # background (free floor) go to depth/points_clear for a Nav2 observation source with
        # marking false / clearing true. Off by default (real robot unchanged until validated).
        # 한글: 장애물 점만 보내면 장애물이 떠난 뒤 지울 광선이 없어 흔적이 남는다.
        # 기준과 같은 바닥 점을 지우기 전용 토픽으로 보낸다(기본 끔).
        self.declare_parameter('publish_clearing', False)
        # clearing points every stride*factor pixels / 지우기 점 간격 배수
        self.declare_parameter('clearing_stride_factor', 2)
        self.publish_clearing = bool(self.get_parameter('publish_clearing').value)
        self.clear_step = max(1, int(self.get_parameter('clearing_stride_factor').value))
        self.stride = self.get_parameter('stride').value
        self.every_nth = self.get_parameter('process_every_nth').value
        self.background_margin_mm = self.get_parameter('background_margin_mm').value
        ref_path = self.get_parameter('background_depth_path').value
        # 한글: 기준 depth 이미지(로봇 홈 자세, 앞에 아무것도 없는 상태)를 불러온다. 홈 자세를 바꾸면 다시 찍어야 한다.
        self.background = np.load(ref_path)
        self.background_sparse = self.background[::self.stride, ::self.stride]
        self.get_logger().info(
            f'loaded background depth reference from {ref_path}, '
            f'valid fraction={float((self.background > 0).mean()):.3f}')
        # Home-pose gate (module docstring). Empty home_pose_rad disables it (camera bench tests).
        # 한글: 팔 홈 자세 확인. home_pose_rad가 비어 있으면 끔(카메라 단독 시험용). camera.launch.py가 base.yaml 값을 넘긴다.
        self.declare_parameter(
            'home_pose_joint_names', ['joint1', 'joint2', 'joint3', 'joint4', 'joint5'])
        self.declare_parameter('home_pose_rad', [0.0])
        # 0.04 -> 0.08 rad + 1 s debounce (2026-10-07, first floor test): at the home pose joint3
        # read 0.025..0.042 rad off while driving (servo backlash/vibration), so 0.04 flapped the
        # gate and collision_monitor stopped the robot 3 times. The gate is meant to catch gross
        # pose changes (arm folded / used for manipulation: 0.3..0.6 rad); small backlash is the
        # background_margin_mm's job (0 false points measured at joint3 0.029 rad off).
        # 한글: 0.04는 주행 중 백래시(0.025~0.042)로 열림/닫힘을 반복해 로봇이 3번 섰다. 게이트는 큰 자세 변화
        # (팔 접힘/조작, 0.3~0.6 rad)만 잡고, 작은 백래시는 margin(60mm)이 처리한다. 1초 이상 계속 벗어나야 닫힘.
        self.declare_parameter('home_pose_tolerance_rad', 0.08)
        self.declare_parameter('home_pose_debounce_s', 1.0)
        self.declare_parameter('joint_state_timeout_s', 2.0)
        self.home_names = list(self.get_parameter('home_pose_joint_names').value)
        home = [float(v) for v in self.get_parameter('home_pose_rad').value]
        self.home_pose = home if len(home) == len(self.home_names) else None
        self.home_tol = self.get_parameter('home_pose_tolerance_rad').value
        self.js_timeout = self.get_parameter('joint_state_timeout_s').value
        self.debounce = self.get_parameter('home_pose_debounce_s').value
        self._bad_since = None  # first time the pose check failed in the current streak
        self._joints = {}
        self._joints_stamp = None
        self._gate_ok = None  # last logged gate state / 마지막으로 로그한 상태
        if self.home_pose is None:
            self.get_logger().warn(
                'home_pose_rad not set (or length mismatch): home-pose gate DISABLED -- '
                'cloud is published regardless of arm pose')
        else:
            self.create_subscription(JointState, '/joint_states', self._joint_cb, 10)
            self.get_logger().info(
                f'home-pose gate on: {dict(zip(self.home_names, self.home_pose))}, '
                f'tol={self.home_tol} rad')
        self._count = 0
        self.intrinsics = None

        self.pub = self.create_publisher(PointCloud2, 'depth/points_sparse', 10)
        self.pub_clear = (self.create_publisher(PointCloud2, 'depth/points_clear', 10)
                          if self.publish_clearing else None)
        self.create_subscription(
            CameraInfo, 'depth/camera_info', self._info_cb, qos_profile_sensor_data)
        self.create_subscription(
            Image, 'depth/image_raw', self._depth_cb, qos_profile_sensor_data)

    def _joint_cb(self, msg):
        for name, pos in zip(msg.name, msg.position):
            self._joints[name] = pos
        self._joints_stamp = time.monotonic()

    # 한글: 팔이 홈 자세(허용오차 내)이고 joint_states가 최신이면 (True, ''), 아니면 (False, 이유).
    def _home_pose_ok(self):
        if self.home_pose is None:
            return True, ''
        if self._joints_stamp is None or time.monotonic() - self._joints_stamp > self.js_timeout:
            return False, 'no recent /joint_states'
        worst_name, worst_err = None, 0.0
        for name, target in zip(self.home_names, self.home_pose):
            if name not in self._joints:
                return False, f'{name} missing in /joint_states'
            err = abs(self._joints[name] - target)
            if err > worst_err:
                worst_name, worst_err = name, err
        if worst_err > self.home_tol:
            return False, f'arm off home pose: {worst_name} off by {worst_err:.3f} rad'
        return True, f'max error {worst_name}={worst_err:.3f} rad'

    # 한글: 카메라 내부 파라미터(fx, fy, cx, cy) 저장.
    def _info_cb(self, msg):
        if self.expected_depth_frame and msg.header.frame_id != self.expected_depth_frame:
            self.intrinsics = None
            self.intrinsics_frame = None
            return
        self.intrinsics = (msg.k[0], msg.k[4], msg.k[2], msg.k[5])  # fx, fy, cx, cy
        self.intrinsics_frame = msg.header.frame_id

    # 한글: 기준 depth보다 margin 이상 '가까운' 픽셀만 장애물로 본다. 로봇 자신의 바퀴/섀시나 바닥은 기준과 같아서 제거되고, XY/높이 필터가 실제 장애물까지 지우던 문제(troubleshooting/023)를 피한다.
    def _depth_cb(self, msg):
        self._count += 1
        if self._count % self.every_nth != 0:
            return
        self._process_depth(msg)

    def _publish_origin(self, translation):
        # Re-broadcast the static origin only when the camera moved (>1 cm). Point heights are
        # computed relative to the published origin, so its exact value does not change them.
        # 한글: 카메라가 1 cm 넘게 움직였을 때만 다시 알린다. 점 높이는 알린 원점 기준이라 영향 없다.
        if self.origin_xyz is not None and np.max(np.abs(self.origin_xyz - translation)) <= 0.01:
            return
        self.origin_xyz = translation.copy()
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'base_footprint'
        t.child_frame_id = FLOOR_ORIGIN_FRAME
        t.transform.translation.x, t.transform.translation.y, t.transform.translation.z = (
            float(v) for v in translation)
        t.transform.rotation.w = 1.0
        self.static_tf.sendTransform(t)
        self.get_logger().info(f'{FLOOR_ORIGIN_FRAME} at {np.round(translation, 3).tolist()} in base_footprint')

    def _process_floor_aware(self, msg, depth_sparse, us, vs):
        try:
            tf = self.tf_buffer.lookup_transform(
                'base_footprint', msg.header.frame_id, rclpy.time.Time()).transform
        except TransformException as exc:
            self.get_logger().warn(f'floor filter: no camera TF: {exc}', throttle_duration_sec=5.0)
            return
        rotation = quat_to_matrix(tf.rotation)
        cam = np.array([tf.translation.x, tf.translation.y, tf.translation.z])
        result = floor_plane_points(
            depth_sparse, self.background_sparse, us, vs, self.intrinsics, rotation, cam,
            self.background_margin_mm, self.floor_raised)
        if result is None:
            self.get_logger().warn('floor plane unavailable; cloud withheld', throttle_duration_sec=5.0)
            return
        obstacle, free, points_base, plane = result
        self._publish_origin(cam)
        origin = self.origin_xyz
        header = Header(stamp=msg.header.stamp, frame_id=FLOOR_ORIGIN_FRAME)
        if self.pub_clear is not None:
            k = self.clear_step
            sub = np.zeros_like(free)
            sub[::k, ::k] = True
            self.pub_clear.publish(point_cloud2.create_cloud(
                header, self._fields(), points_base[free & sub] - origin))
        points = points_base[obstacle]
        if self.extrude_depth > 0.0 and len(points) > 0:
            # Extrude horizontally away from the camera at the face height (the box body is behind
            # the face at the same height). 한글: 앞면 높이 그대로 카메라에서 먼 쪽 수평으로 늘린다.
            away = points[:, :2] - origin[:2]
            away /= np.maximum(np.linalg.norm(away, axis=1, keepdims=True), 1e-6)
            layers = [points]
            d = self.extrude_step
            while d <= self.extrude_depth + 1e-6:
                extended = points.copy()
                extended[:, :2] += away * d
                layers.append(extended)
                d += self.extrude_step
            points = np.concatenate(layers, axis=0)
        self.pub.publish(point_cloud2.create_cloud(header, self._fields(), points - origin))

    def _process_depth(self, msg):
        # A raw depth frame must not be compared with a color-aligned background.
        # 한글: 미정합 깊이를 컬러 정합 기준 영상과 비교하지 않는다.
        if self.expected_depth_frame and (msg.header.frame_id != self.expected_depth_frame or self.intrinsics_frame != self.expected_depth_frame):
            self.get_logger().warn('depth frame is not color aligned; cloud withheld', throttle_duration_sec=5.0)
            return
        if self.background_calibration_path:
            # Withhold obstacle and clearing clouds if the calibration changes at runtime.
            # 한글: 실행 중 보정값이 바뀌면 장애물과 지우기 점 모두 발행하지 않는다.
            try:
                calibration = Path(self.background_calibration_path)
                if calibration.is_symlink() or calibration.stat().st_size > 65536 or hashlib.sha256(calibration.read_bytes()).hexdigest() != self.background_calibration_sha256:
                    raise ValueError('calibration changed')
            except (OSError, ValueError):
                self.get_logger().warn('corrected background calibration mismatch; cloud withheld', throttle_duration_sec=5.0)
                return
        if self.intrinsics is None:
            return
        fx, fy, cx, cy = self.intrinsics

        ok, why = self._home_pose_ok()
        # Debounce: only close after the check has failed continuously for debounce seconds.
        # 한글: 연속으로 debounce초 이상 실패해야 닫는다(순간적인 서보 읽기 흔들림 무시).
        now = time.monotonic()
        if ok:
            self._bad_since = None
        else:
            if self._bad_since is None:
                self._bad_since = now
            if self._gate_ok is not False and now - self._bad_since < self.debounce:
                ok = True
        if ok != self._gate_ok:
            # Log only on state changes (plus a throttled reminder while blocked).
            # 한글: 상태가 바뀔 때만 로그(막혀 있는 동안은 아래 throttle 경고).
            if ok:
                self.get_logger().info(f'home-pose gate OPEN, publishing ({why})')
            else:
                self.get_logger().warn(f'home-pose gate CLOSED, not publishing: {why}')
            self._gate_ok = ok
        if not ok:
            self.get_logger().warn(
                f'depth cloud withheld: {why}', throttle_duration_sec=5.0)
            return

        depth = np.frombuffer(msg.data, dtype=np.uint16).reshape(msg.height, msg.width)
        depth_sparse = depth[::self.stride, ::self.stride]

        vs, us = np.indices(depth_sparse.shape)
        us = us * self.stride
        vs = vs * self.stride
        if self.floor_aware:
            self._process_floor_aware(msg, depth_sparse, us, vs)
            return
        # 한글: mm → m
        z = depth_sparse.astype(np.float32) / 1000.0  # mm -> m

        # Closer than the known background (wheel/floor with nothing in front) by more than
        # the margin -> something new is there now, real obstacle. Equal to or farther than
        # the background -> the robot's own wheel/chassis or ordinary floor, drop it.
        bg = self.background_sparse
        valid = (
            (depth_sparse > 0) & (bg > 0) &
            (depth_sparse.astype(np.int32) < bg.astype(np.int32) - self.background_margin_mm))
        free = (depth_sparse > 0) & (bg > 0) & (
            np.abs(depth_sparse.astype(np.int32) - bg.astype(np.int32)) <= self.background_margin_mm)
        if self.pub_clear is not None:
            # Free floor = within the margin of the background. Sub-sampled: the rays only
            # need to cover the area. 한글: 기준과 margin 안으로 같은 픽셀 = 빈 바닥, 더 성기게.
            k = self.clear_step
            sub = np.zeros_like(free)
            sub[::k, ::k] = True
            free &= sub
            zf = z[free]
            clear_pts = np.stack(
                [(us[free] - cx) * zf / fx, (vs[free] - cy) * zf / fy, zf], axis=-1)
            self.pub_clear.publish(
                point_cloud2.create_cloud(msg.header, self._fields(), clear_pts))
        x = (us[valid] - cx) * z[valid] / fx
        y = (vs[valid] - cy) * z[valid] / fy
        z = z[valid]
        points = np.stack([x, y, z], axis=-1)
        if self.extrude_depth > 0.0 and len(points) > 0:
            norm = np.linalg.norm(points, axis=1, keepdims=True)
            rays = points / np.maximum(norm, 1e-6)
            layers = [points]
            d = self.extrude_step
            while d <= self.extrude_depth + 1e-6:
                extended = points + rays * d
                layers.append(extended)
                d += self.extrude_step
            points = np.concatenate(layers, axis=0)

        cloud = point_cloud2.create_cloud(msg.header, self._fields(), points)
        self.pub.publish(cloud)

    @staticmethod
    def _fields():
        return [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
        ]


def main():
    rclpy.init()
    node = SparsePointCloud()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
