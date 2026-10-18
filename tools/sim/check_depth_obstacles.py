#!/usr/bin/env python3
# 한글: Gazebo에서 깊이 장애물(sparse_point_cloud)이 상자를 잡고 local costmap에 찍히는지 로봇 기준 좌표로 확인한다.
#       상자 위치는 Gazebo 정답(로봇·상자 월드 자세)으로 계산하므로 AMCL 위치와 무관하다. 읽기만 한다.
#       사용: python3 tools/sim/check_depth_obstacles.py ROBOT_X ROBOT_Y ROBOT_YAW_DEG BOX_X BOX_Y BOX_SX BOX_SY
#       (sim.launch.py depth_obstacles:=true + nav2.launch.py use_sim_time:=true가 떠 있어야 함, ROS_DOMAIN_ID=31)
# Box relative to the robot comes from the Gazebo ground truth (argv: robot x y yaw_deg, box x y, box sx sy).
import math, sys, time, rclpy, numpy as np
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from nav_msgs.msg import OccupancyGrid
from sensor_msgs_py import point_cloud2
from tf2_ros import Buffer, TransformListener
from rclpy.time import Time
from scipy.spatial.transform import Rotation as R
rx, ry, ryaw, bx, by, sx, sy = map(float, sys.argv[1:8]); ryaw = math.radians(ryaw)
dx, dy = bx - rx, by - ry
bfx, bfy = math.cos(ryaw)*dx + math.sin(ryaw)*dy, -math.sin(ryaw)*dx + math.cos(ryaw)*dy
print("box centre in base_footprint (ground truth): (%.3f, %.3f)" % (bfx, bfy))
def box_corners_robot():   # box rectangle (world axes) in the robot frame
    out = []
    for cx, cy in ((-sx/2, -sy/2), (sx/2, -sy/2), (sx/2, sy/2), (-sx/2, sy/2)):
        X, Y = bx + cx - rx, by + cy - ry
        out.append((math.cos(ryaw)*X + math.sin(ryaw)*Y, -math.sin(ryaw)*X + math.cos(ryaw)*Y))
    return np.array(out)
def in_poly(p, poly):
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > p[1]) != (y2 > p[1]) and p[0] < x1 + (p[1] - y1) * (x2 - x1) / (y2 - y1): inside = not inside
    return inside
rclpy.init(); n = Node("check_depth_obs", parameter_overrides=[rclpy.parameter.Parameter("use_sim_time", value=True)])
buf = Buffer(); TransformListener(buf, n)
st = {}
n.create_subscription(PointCloud2, "/depth_cam/depth/points_sparse", lambda m: st.__setitem__("pc", m), 10)
n.create_subscription(OccupancyGrid, "/local_costmap/costmap", lambda m: st.__setitem__("lc", m), 10)
t0 = time.time()
while time.time() - t0 < 30: rclpy.spin_once(n, timeout_sec=0.1)
poly = box_corners_robot()
def to_robot(frame):
    tr = buf.lookup_transform("base_footprint", frame, Time()); q = tr.transform.rotation; t = tr.transform.translation
    return R.from_quat([q.x, q.y, q.z, q.w]).as_matrix(), np.array([t.x, t.y, t.z])
pc = st.get("pc")
if pc is not None:
    pts = np.array([[p[0], p[1], p[2]] for p in point_cloud2.read_points(pc, field_names=("x", "y", "z"), skip_nans=True)])
    rot, t = to_robot(pc.header.frame_id); w = pts @ rot.T + t
    inbox = np.array([in_poly(p[:2], poly * 1.0) for p in w])
    near = np.array([min(np.hypot(*(p[:2] - poly.mean(0))), 9) < 0.30 for p in w])
    print("points n %d: in box %d, within 30 cm of the box centre %d, elsewhere %d" % (len(w), inbox.sum(), near.sum(), (~near).sum()))
    print("  robot-frame x %.2f..%.2f y %.2f..%.2f z %.3f..%.3f" % (w[:,0].min(), w[:,0].max(), w[:,1].min(), w[:,1].max(), w[:,2].min(), w[:,2].max()))
    far = w[~near]
    if len(far): print("  elsewhere points: x %.2f..%.2f y %.2f..%.2f z %.3f..%.3f" % (far[:,0].min(), far[:,0].max(), far[:,1].min(), far[:,1].max(), far[:,2].min(), far[:,2].max()))
else: print("NO points")
lc = st.get("lc")
if lc is not None:
    info = lc.info; g = np.array(lc.data).reshape(info.height, info.width)
    rot, t = to_robot(lc.header.frame_id)   # costmap frame (odom) -> robot
    inv_rot, inv_t = rot.T, -rot.T @ t      # robot -> costmap frame
    hits = tot = 0
    for fx in np.linspace(0, 1, 7):
        for fy in np.linspace(0, 1, 5):
            p = poly[0] + fx * (poly[1] - poly[0]) + fy * (poly[3] - poly[0])
            q = inv_rot @ np.array([p[0], p[1], 0.0]) + inv_t
            i, j = int((q[1] - info.origin.position.y) / info.resolution), int((q[0] - info.origin.position.x) / info.resolution)
            if 0 <= i < info.height and 0 <= j < info.width:
                tot += 1; hits += g[i, j] >= 99
    print("local costmap: box cells lethal/inscribed %d of %d" % (hits, tot))
else: print("NO costmap")
