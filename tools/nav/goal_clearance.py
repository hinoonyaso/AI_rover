#!/usr/bin/env python3
"""Distance from a pose to the nearest LiDAR-visible obstacle (saved map or live LiDAR; no ROS needed).

Near-wall start points and goals deadlock against collision_monitor DirStop (stop -> no progress
-> wait -> retry, troubleshooting/065): keep them at least MIN_CLEARANCE_M from obstacles. Use this
before saving a start point or accepting a goal (voice V2, prd/voice-mission-control.md).

  python3 tools/nav/goal_clearance.py maps/lap2_20261005.yaml 1.30 0.40 1.02 0.37
  python3 tools/nav/goal_clearance.py --live 1.30 0.40      # live /global_costmap/costmap (Nav2 running)

한글: 저장된 지도에서 자세까지 가장 가까운 점유 칸 거리(ROS 불필요). 벽 가까운 시작점·목표는 DirStop과
교착하므로(065) 장애물에서 MIN_CLEARANCE_M 이상이어야 한다. 출발점 저장·목표 수락 전에 쓴다.
"""
import math
from pathlib import Path
import sys

import numpy as np
import yaml

# DirStop uses the LiDAR only, so clearance is measured to LiDAR-visible obstacles. Sim 2026-11-25:
# deadlocked points were <= 0.33 m from such walls, working points >= 0.46 m (a low 11 cm box nearer
# than that did not matter). 한글: DirStop은 LiDAR만 쓰므로 LiDAR에 보이는 장애물 기준. 교착 지점 <= 0.33 m,
# 정상 지점 >= 0.46 m(더 가까운 11 cm 낮은 상자는 영향 없음).
MIN_CLEARANCE_M = 0.40


def read_pgm(path):
    """Read a binary (P5) PGM into a uint8 array, top row first. / 이진 PGM을 읽는다."""
    data = Path(path).read_bytes()
    fields, pos = [], 0
    while len(fields) < 4:
        while data[pos:pos + 1].isspace():
            pos += 1
        if data[pos:pos + 1] == b'#':
            pos = data.index(b'\n', pos) + 1
            continue
        end = pos
        while not data[end:end + 1].isspace():
            end += 1
        fields.append(data[pos:end])
        pos = end
    if fields[0] != b'P5' or int(fields[3]) > 255:
        raise ValueError('only 8-bit binary PGM (P5) is supported')
    width, height = int(fields[1]), int(fields[2])
    pixels = np.frombuffer(data[pos + 1:pos + 1 + width * height], dtype=np.uint8)
    return pixels.reshape(height, width)


class MapClearance:
    """Occupied cells of a map_server map and clearance queries. / 지도의 점유 칸과 여유 거리 질의."""

    def __init__(self, yaml_path):
        meta = yaml.safe_load(Path(yaml_path).read_text())
        image = read_pgm(Path(yaml_path).parent / meta['image'])
        occupancy = (255 - image.astype(float)) / 255.0 if not meta.get('negate', 0) else image / 255.0
        self.resolution = float(meta['resolution'])
        self.origin = meta['origin'][:2]
        self.height = image.shape[0]
        rows, cols = np.nonzero(occupancy > float(meta['occupied_thresh']))
        # Cell centres in the map frame; the image's top row is the largest y.
        # 한글: 칸 중심의 지도 좌표. 이미지 맨 위 행이 가장 큰 y다.
        self.occupied = np.column_stack((self.origin[0] + (cols + 0.5) * self.resolution,
                                         self.origin[1] + (self.height - rows - 0.5) * self.resolution))

    @classmethod
    def from_grid(cls, width, height, resolution, origin_xy, data, lethal=100):
        """Use a live nav_msgs/OccupancyGrid (e.g. /global_costmap/costmap): cells >= lethal are obstacles.

        The saved map can miss obstacles the costmap sees (sim 2026-11-25: static map 0.47 m vs
        live costmap ~0.3 m at the deadlocked points), so decisions should use the live costmap.
        한글: 실시간 코스트맵(lethal 이상 = 장애물)을 쓴다. 저장 지도는 실제 장애물을 놓칠 수 있다.
        """
        self = cls.__new__(cls)
        self.resolution = float(resolution)
        self.origin = list(origin_xy)
        self.height = int(height)
        grid = np.asarray(data, dtype=np.int16).reshape(int(height), int(width))
        rows, cols = np.nonzero(grid >= lethal)   # OccupancyGrid row 0 is the smallest y
        self.occupied = np.column_stack((self.origin[0] + (cols + 0.5) * self.resolution,
                                         self.origin[1] + (rows + 0.5) * self.resolution))
        return self

    def clearance(self, x, y):
        """Metres from (x, y) to the nearest occupied cell centre. / 가장 가까운 점유 칸까지 거리(m)."""
        if not len(self.occupied):
            return math.inf
        return float(np.min(np.hypot(self.occupied[:, 0] - x, self.occupied[:, 1] - y)))

    def nearest(self, x, y):
        """Map coordinates of the nearest occupied cell centre, or None. / 가장 가까운 점유 칸 좌표."""
        if not len(self.occupied):
            return None
        i = int(np.argmin(np.hypot(self.occupied[:, 0] - x, self.occupied[:, 1] - y)))
        return float(self.occupied[i, 0]), float(self.occupied[i, 1])

    def check(self, x, y, minimum=MIN_CLEARANCE_M):
        """(ok, clearance) for a candidate start point or goal. / 후보 지점의 통과 여부와 여유 거리."""
        value = self.clearance(x, y)
        return value >= minimum, value


def scan_clearance(ranges, angle_min, angle_increment, blind_half_angle=1.4, range_min=0.12):
    """Nearest LiDAR return around the robot, ignoring the rear sector the arm blocks.

    For "save the current position as the start point": the LiDAR sees exactly what DirStop sees.
    The A1 has no returns over ~160 deg behind the robot (arm occlusion), so +-blind_half_angle around
    the rear is ignored. Ranges are from the LiDAR, which sits near the robot centre (approximation).
    한글: 현재 위치를 출발점으로 저장할 때 쓴다. LiDAR가 DirStop과 같은 것을 본다. 팔에 가린 뒤쪽 약 160°는 제외.
    """
    best = math.inf
    for i, r in enumerate(ranges):
        if not math.isfinite(r) or r < range_min:
            continue
        a = angle_min + i * angle_increment
        rear = abs(math.atan2(math.sin(a - math.pi), math.cos(a - math.pi)))
        if rear <= blind_half_angle:
            continue
        best = min(best, r)
    return best


def live_costmap(topic='/global_costmap/costmap', wait=15.0):
    """Read one live costmap message (ROS). / 실시간 코스트맵 한 장을 읽는다."""
    import time
    import rclpy
    from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
    from nav_msgs.msg import OccupancyGrid
    rclpy.init()
    node = rclpy.create_node('goal_clearance')
    grids = []
    qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL)
    node.create_subscription(OccupancyGrid, topic, grids.append, qos)
    end = time.time() + wait
    while not grids and time.time() < end:
        rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_node()
    rclpy.try_shutdown()
    if not grids:
        raise SystemExit(f'no costmap on {topic}')
    g = grids[-1]
    return MapClearance.from_grid(g.info.width, g.info.height, g.info.resolution,
                                  (g.info.origin.position.x, g.info.origin.position.y), g.data)


def main(argv):
    if len(argv) < 4 or (len(argv) - 2) % 2:
        print(__doc__)
        return 2
    # "--live" instead of a map file reads /global_costmap/costmap. / 지도 대신 --live면 실시간 코스트맵.
    clearance = live_costmap() if argv[1] == '--live' else MapClearance(argv[1])
    worst = True
    for i in range(2, len(argv), 2):
        x, y = float(argv[i]), float(argv[i + 1])
        ok, value = clearance.check(x, y)
        worst &= ok
        near = clearance.nearest(x, y)
        where = f' (nearest obstacle cell {near[0]:.2f}, {near[1]:.2f})' if near else ''
        print(f'({x:.2f}, {y:.2f}) clearance {value:.2f} m{where} -> {"OK" if ok else f"TOO CLOSE (< {MIN_CLEARANCE_M} m)"}')
    return 0 if worst else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
