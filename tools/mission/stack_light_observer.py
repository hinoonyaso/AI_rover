"""Collect fresh simulation camera samples for a stack-light inspection.

한글: 시뮬레이션 경광등 점검에 사용할 최신 카메라 표본을 수집한다.
"""
from pathlib import Path
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src/jetrover_perception/scripts'))
from stack_light import HUE_RANGES, classify  # noqa: E402

def fixture_regions(image):
    """Locate the simulated three-color fixture in one frame. / 가상 시험판 세 색상의 영상 위치를 찾는다."""
    if not isinstance(image, np.ndarray) or image.dtype != np.uint8 or image.shape != (360, 640, 3):
        return None
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    hue, saturation, value = (hsv[:, :, i] for i in range(3))
    found = {}
    for name, ranges in HUE_RANGES.items():
        mask = np.zeros(hue.shape, dtype=np.uint8)
        for low, high in ranges:
            mask |= ((hue >= low) & (hue <= high)).astype(np.uint8)
        mask &= ((saturation >= 100) & (value >= 15)).astype(np.uint8)
        count, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        if count < 2:
            return None
        x, y, w, h, area = (int(v) for v in stats[1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])])
        if w < 12 or h < 12 or area < 100:
            return None
        found[name] = (x + w // 2, y + h // 2, w, h)
    red, yellow, green = (found[name] for name in ('red', 'yellow', 'green'))
    gap1, gap2 = yellow[1] - red[1], green[1] - yellow[1]
    if (min(gap1, gap2) < 12 or max(gap1, gap2) > 2 * min(gap1, gap2) or
            max(red[0], yellow[0], green[0]) - min(red[0], yellow[0], green[0]) > 80):
        return None
    return {name: (x - 6, y - 6, 12, 12) for name, (x, y, _, _) in found.items()}


class ObservationWindow:
    """Accept only fresh, ordered RGB frames. / 최신 순서의 RGB 영상만 수집한다."""

    def __init__(self):
        self.frames = []
        self.last_stamp = None
        self.received = 0
        self.invalid_time = 0
        self.gap_resets = 0
        self.invalid_format = 0

    def add(self, image, stamp, sim_now, received_at):
        """Add a valid sample and discard stale windows. / 유효 표본을 추가하고 오래된 관측 창을 버린다."""
        self.received += 1
        if (not all(np.isfinite(v) for v in (stamp, sim_now, received_at)) or
                not 0 <= sim_now - stamp <= .6 or
                (self.last_stamp is not None and stamp <= self.last_stamp)):
            self.invalid_time += 1
            self.frames.clear()
            return
        self.last_stamp = stamp
        if self.frames and received_at - self.frames[-1][0] < .3:
            return
        if self.frames and (received_at <= self.frames[-1][0] or received_at - self.frames[-1][0] > .6):
            self.gap_resets += 1
            self.frames.clear()
        self.frames.append((received_at, image))

    def result(self, now):
        """Return color observations without claiming mission success. / 임무 성공으로 추정하지 않고 색상 관측만 반환한다."""
        regions = fixture_regions(self.frames[-1][1]) if self.frames else None
        return classify(self.frames, regions or {}, now)


def observe(node, stop_requested, timeout=20):
    """Observe the robot camera; return an explicit status and color evidence.

    한글: 로봇 카메라를 관측하고 명시적인 결과와 색상별 근거를 반환한다.
    """
    import rclpy
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import Image

    window = ObservationWindow()
    last_reasons = {}
    # Limit OpenCV worker threads so the simulated camera keeps receiving CPU time.
    # 한글: 시뮬레이션 카메라가 CPU 시간을 확보하도록 OpenCV 스레드를 제한한다.
    cv2.setNumThreads(1)

    def receive(msg):
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
        now = node.get_clock().now().nanoseconds / 1e9
        if msg.encoding != 'rgb8' or msg.step != msg.width * 3 or len(msg.data) != msg.height * msg.step:
            window.invalid_format += 1
            window.frames.clear()
            return
        image = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width, 3).copy()
        window.add(image, stamp, now, time.monotonic())

    subscription = node.create_subscription(Image, '/depth_cam/color/image_raw', receive, qos_profile_sensor_data)
    try:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if stop_requested():
                return {'status': 'canceled', 'reason': 'inspection_canceled'}
            rclpy.spin_once(node, timeout_sec=.1)
            if len(window.frames) >= 5 and window.frames[-1][0] - window.frames[0][0] >= 2:
                colors = window.result(time.monotonic())
                last_reasons = {name: item['reason'] for name, item in colors.items()}
                if all(item['state'] != 'unknown' for item in colors.values()):
                    return {'status': 'observed', 'colors': colors}
        print(f'INSPECTION_DIAGNOSTIC received={window.received} invalid_time={window.invalid_time} '
              f'gap_resets={window.gap_resets} invalid_format={window.invalid_format} '
              f'window_frames={len(window.frames)} color_reasons={last_reasons}', flush=True)
        return {'status': 'unavailable', 'reason': 'inspection_unconfirmed'}
    finally:
        node.destroy_subscription(subscription)
