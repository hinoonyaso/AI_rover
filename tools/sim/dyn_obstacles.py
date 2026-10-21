#!/usr/bin/env python3
# 한글: Gazebo 동적 장애물(사람, 낮은 상자)을 정해진 경로·속도로 움직이는 구동기와 시나리오 D1~D4 (체크리스트 8.16, host).
#       움직임 계산은 순수 함수(단위시험 test_dyn_obstacles.py), 실제 이동은 ros_gz_bridge로 연결한 /world/<w>/set_pose 서비스.
#       모델은 room_lap2_objects.sdf의 person_0, dyn_box(중력 끔, 평소 방 밖 (8, 8)에 세워 둠).
"""Kinematic driver for the dynamic-obstacle test models and the D1-D6 scenarios (checklist 8.16, host).

Models (room_lap2_objects.sdf): person_0 (two legs r 6 cm that cross the LiDAR plane + torso) and dyn_box (33 x 22 x 11 cm,
below the LiDAR, seen only by the depth camera). Both have gravity off and are parked outside the room at (8, 8).
The driver calls /world/<world>/set_pose (bridged by `ros_gz_bridge parameter_bridge
/world/<world>/set_pose@ros_gz_interfaces/srv/SetEntityPose`) at RATE_HZ of simulated time.
A motion starts when its trigger fires: `after_s` seconds after the goal was sent, or when the robot has advanced
`robot_progress_m` along the start->goal line.
"""
from dataclasses import dataclass, field
import math  # noqa: I100

RATE_HZ = 20.0           # set_pose rate in simulated time / 시뮬레이션 시간 기준 갱신 주기
Z = 0.002                # model origin height (just above the floor) / 바닥 바로 위
PARK = {'person_0': (8.0, 8.0), 'dyn_box': (8.0, 8.6)}
PERSON_LEGS = ((0.0, 0.10), (0.0, -0.10))   # leg centres in the model frame / 모델 기준 다리 중심
PERSON_LEG_R = 0.06
DYN_BOX_SIZE = (0.33, 0.22)
OBJECT_0_PARK = (8.0, 9.2)                  # the static-avoidance box is moved away in D scenarios / D 시나리오에선 치움

# A↔B line of the static-avoidance scenarios (avoid_trials.py), longest straight run in the scan room.
# 정지 상자 시나리오의 A↔B 직선(방에서 가장 긴 직선)을 쓴다.
A = (1.02, 0.30)
B = (1.00, 1.25)


@dataclass
class Motion:
    """One model moving along a polyline at constant speed once triggered (speed 0 = appear at path[0] and stay)."""

    model: str
    path: list
    speed: float
    yaw_deg: float = 0.0
    after_s: float = None           # trigger: seconds after the goal was sent / 목표 보낸 뒤 초
    robot_progress_m: float = None  # trigger: robot advanced this far along start->goal / 로봇 진행 거리
    park_at_end: bool = True        # park outside the room when the path ends / 끝나면 방 밖으로
    pause_at: int = None            # waypoint index to stand still at / 멈춰 설 경유점 번호
    pause_s: float = 0.0            # seconds standing there / 서 있는 시간
    started_at: float = field(default=None, repr=False)


def path_length(path):
    return sum(math.dist(path[i], path[i + 1]) for i in range(len(path) - 1))


def point_along(path, d):
    """Point at arc length d along the polyline and whether the end was reached. 한글: 경로 위 거리 d 지점."""
    if d <= 0.0:
        return path[0], False
    for i in range(len(path) - 1):
        seg = math.dist(path[i], path[i + 1])
        if d <= seg and seg > 0.0:
            f = d / seg
            return (path[i][0] + f * (path[i + 1][0] - path[i][0]), path[i][1] + f * (path[i + 1][1] - path[i][1])), False
        d -= seg
    return path[-1], True


def motion_pose(m, t):
    """(x, y) of motion m at time t (same clock as m.started_at), or None when the model should be parked."""
    if m.started_at is None or t < m.started_at:
        return None
    if m.speed <= 0.0:
        return m.path[0]
    d = m.speed * (t - m.started_at)
    if m.pause_at is not None and m.pause_s > 0.0:
        # 경유점 pause_at에서 pause_s초 서 있다가 계속 / stand at waypoint pause_at for pause_s, then go on
        d_pause = path_length(m.path[:m.pause_at + 1])
        if d > d_pause:
            d = max(d_pause, d - m.speed * m.pause_s)
    p, done = point_along(m.path, d)
    if done and m.park_at_end:
        return None
    return p


def progress(robot_xy, start, goal):
    """Distance travelled along the start->goal line (m). 한글: 출발→목표 직선 방향 진행 거리."""
    ux, uy = goal[0] - start[0], goal[1] - start[1]
    n = math.hypot(ux, uy)
    return ((robot_xy[0] - start[0]) * ux + (robot_xy[1] - start[1]) * uy) / n


def triggered(m, t_since_goal, robot_progress):
    if m.after_s is not None and t_since_goal >= m.after_s:
        return True
    return m.robot_progress_m is not None and robot_progress is not None and robot_progress >= m.robot_progress_m


def scenarios():
    """D1-D6 (prd/sim-dynamic-avoidance-test-plan.md; D5/D6 added 2026-10-22). Fresh Motion objects each call.

    Robot A (1.02, 0.30, 83 deg) -> B (1.00, 1.25). Crossing line y 1.00: the obstacle reaches the robot path while the
    robot centre is about 0.55-0.65 m before it (the scan room is too short for the planned 0.6-0.8 m everywhere).
    한글: 로봇 경로를 지날 때 로봇 중심과 0.55~0.65 m(방이 짧아 계획의 0.6~0.8 m를 다 맞추진 못함).
    """
    leg = {'AB': ((*A, 83.0), B)}
    return {
        # D1 사람이 오른쪽에서 왼쪽으로 0.5 m/s로 가로지름 / person crosses right to left at 0.5 m/s
        'D1': {'legs': leg, 'motions': [Motion('person_0', [(1.55, 1.00), (0.25, 1.00)], 0.5, yaw_deg=180.0, after_s=0.0)]},
        # D2 사람이 정면에서 0.3 m/s로 다가오다 왼쪽으로 비켜 지나감 / person walks toward the robot, then steps aside
        'D2': {'legs': leg, 'motions': [Motion('person_0', [(1.00, 1.30), (1.00, 1.00), (0.30, 1.00)], 0.3,
                                               yaw_deg=-90.0, after_s=0.0)]},
        # D3 낮은 상자가 0.3 m/s로 가로지름(LiDAR에 안 보임) / low box crosses at 0.3 m/s (depth camera only)
        'D3': {'legs': leg, 'motions': [Motion('dyn_box', [(1.55, 0.95), (0.25, 0.95)], 0.3, after_s=0.0)]},
        # D4 로봇이 5 cm 나아가면 앞 경로에 상자가 나타나 그대로 있음 / a box appears on the path and stays
        'D4': {'legs': leg, 'motions': [Motion('dyn_box', [(1.00, 0.85)], 0.0, robot_progress_m=0.05, park_at_end=False)]},
        # D5 (2026-10-22 추가) 사람이 로봇 바로 앞을 0.3 m/s로 천천히 가로지름: 로봇이 5 cm 나아가면 출발, 로봇 중심에서 약 0.4 m 앞을 지남.
        #    D1~D3은 장애물이 0.6 m 넘게 앞에서 먼저 지나가 '멈추고 기다리기'가 시험되지 않았다(baseline).
        # person crosses slowly right in front (~0.4 m from the robot centre); D1-D3 never made the robot stop
        'D5': {'legs': leg, 'motions': [Motion('person_0', [(1.55, 0.95), (0.25, 0.95)], 0.3, yaw_deg=180.0,
                                               robot_progress_m=0.05)]},
        # D6 (2026-10-22 추가) 사람이 경로 위로 들어와 4 s 서 있다가 왔던 쪽(오른쪽)으로 물러남. 처음엔 왼쪽으로 나가게 했는데, 로봇이 왼쪽으로
        #    돌아가는 중이라 위치만 옮기는 사람 모델이 거의 멈춘 로봇 쪽으로 걸어 들어갔다(시나리오 결함, 6/6 '접촉').
        # person stands on the path 4 s, then steps back to the right (leaving to the left walked it into the detouring robot)
        'D6': {'legs': leg, 'motions': [Motion('person_0', [(1.55, 0.95), (1.00, 0.95), (1.55, 0.95)], 0.4, yaw_deg=180.0,
                                               robot_progress_m=0.05, pause_at=1, pause_s=4.0)]},
    }


class ObstacleDriver:
    """Moves the scenario models through set_pose on a simulated-time timer of `node`.

    node      rclpy node with use_sim_time (its clock drives the timer)
    robot_xy  callable returning the robot (x, y) in the map frame or None
    """

    def __init__(self, node, world, robot_xy):
        from ros_gz_interfaces.srv import SetEntityPose  # noqa: F401 - imported here so the pure part needs no ROS
        self._srv_type = SetEntityPose
        self.node, self.robot_xy = node, robot_xy
        self.cli = node.create_client(SetEntityPose, f'/world/{world}/set_pose')
        self.motions, self.start, self.goal, self.t_goal = [], None, None, None
        self.log = []          # (t, model, x, y) commanded poses / 명령한 자세 기록
        self.timer = node.create_timer(1.0 / RATE_HZ, self._tick)
        self.active = False

    def ready(self, timeout=10.0):
        return self.cli.wait_for_service(timeout_sec=timeout)

    def set_pose(self, model, x, y, yaw_deg=0.0):
        req = self._srv_type.Request()
        req.entity.name, req.entity.type = model, 2      # 2 = MODEL
        req.pose.position.x, req.pose.position.y, req.pose.position.z = float(x), float(y), Z
        yaw = math.radians(yaw_deg)
        req.pose.orientation.z, req.pose.orientation.w = math.sin(yaw / 2), math.cos(yaw / 2)
        return self.cli.call_async(req)                 # fire and forget; the next tick sends a newer pose

    def park_all(self):
        for name, (x, y) in PARK.items():
            self.set_pose(name, x, y)

    def begin(self, motions, start, goal, t_goal):
        """Arm the motions for one trial; t_goal = simulated time the goal was sent."""
        for m in motions:
            m.started_at = None
        self.motions, self.start, self.goal, self.t_goal = motions, start, goal, t_goal
        self.log = []
        self.active = True

    def end(self):
        self.active = False
        self.park_all()

    def _tick(self):
        if not self.active:
            return
        t = self.node.get_clock().now().nanoseconds * 1e-9
        r = self.robot_xy()
        prog = progress(r, self.start, self.goal) if r is not None else None
        for m in self.motions:
            if m.started_at is None and triggered(m, t - self.t_goal, prog):
                m.started_at = t
            p = motion_pose(m, t)
            if p is None:
                if m.started_at is not None:
                    x, y = PARK[m.model]
                    self.set_pose(m.model, x, y)
                continue
            self.set_pose(m.model, p[0], p[1], m.yaw_deg)
            self.log.append((t, m.model, p[0], p[1]))
