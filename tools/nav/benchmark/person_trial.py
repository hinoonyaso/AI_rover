# 사람 시험 bag: 시간별 로봇 속도, LiDAR로 본 사람(정면 통로 안 점)과 몸 사이 최소 간격, collision_monitor 상태
# Person trial bag: robot speed over time, min gap between body hull and LiDAR returns in the corridor ahead, collision_monitor state.
# Usage: python3 tools/nav/benchmark/person_trial.py bags/<tag>/trial_D06
import sys, math, numpy as np, rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
bag = sys.argv[1]
def tfstatic(bag):
    r = rosbag2_py.SequentialReader(); r.open(rosbag2_py.StorageOptions(uri=bag), rosbag2_py.ConverterOptions('', ''))
    T = get_message('tf2_msgs/msg/TFMessage'); e = {}
    while r.has_next():
        tp, d, _ = r.read_next()
        if tp == '/tf_static':
            for t in deserialize_message(d, T).transforms: e[t.child_frame_id] = (t.header.frame_id, t.transform)
    return e
E = tfstatic(bag)
def chain(f):
    x = y = yaw = 0.0
    while f != 'base_footprint':
        p, tr = E[f]; q = tr.rotation; ty = math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z)); c, s = math.cos(ty), math.sin(ty)
        x, y = c*x - s*y + tr.translation.x, s*x + c*y + tr.translation.y; yaw += ty; f = p
    return x, y, yaw
HX, HY = 0.166, 0.13
r = rosbag2_py.SequentialReader(); r.open(rosbag2_py.StorageOptions(uri=bag), rosbag2_py.ConverterOptions('', ''))
S = get_message('sensor_msgs/msg/LaserScan'); O = get_message('nav_msgs/msg/Odometry'); CM = get_message('nav2_msgs/msg/CollisionMonitorState')
t0 = None; v = 0.0; rows = []; cms = []
while r.has_next():
    tp, d, t = r.read_next(); t0 = t0 or t; ts = (t - t0) * 1e-9
    if tp == '/odom':
        tw = deserialize_message(d, O).twist.twist; v = math.hypot(tw.linear.x, tw.linear.y)
    elif tp == '/collision_monitor_state':
        m = deserialize_message(d, CM); cms.append((round(ts, 1), m.action_type, m.polygon_name))
    elif tp == '/scan':
        m = deserialize_message(d, S); lx, ly, lyaw = chain(m.header.frame_id)
        a = m.angle_min + np.arange(len(m.ranges)) * m.angle_increment + lyaw; rr = np.array(m.ranges); ok = np.isfinite(rr) & (rr > m.range_min)
        px = lx + rr[ok]*np.cos(a[ok]); py = ly + rr[ok]*np.sin(a[ok])
        sel = (px > 0) & (px < 1.2) & (np.abs(py) < 0.7)          # 앞쪽 통로(벽은 1.4 m 이상 앞) / corridor ahead
        if sel.any():
            dx = np.maximum(px[sel] - HX, 0) ; dy = np.maximum(np.abs(py[sel]) - HY, 0)
            gap = np.hypot(dx, dy).min()
            i = np.argmin(np.hypot(dx, dy)); rows.append((ts, gap, px[sel][i], py[sel][i], v))
        else:
            rows.append((ts, float('nan'), 0, 0, v))
g = np.array([x[1] for x in rows]); k = int(np.nanargmin(g)) if np.isfinite(g).any() else None
print('min LiDAR gap (body hull to nearest return in the corridor ahead): %.1f cm at t %.1f (point x %.2f y %.2f, robot speed %.3f m/s)' % (rows[k][1]*100, rows[k][0], rows[k][2], rows[k][3], rows[k][4]) if k is not None else 'no returns in corridor')
stopped = [x for x in rows if x[4] < 0.01 and x[0] > 3]
print('time with robot speed < 0.01 m/s (after 3 s): %.1f s' % (len(stopped) * np.median(np.diff([x[0] for x in rows]))))
print('collision_monitor events:', cms[:10])
for x in rows[::7]: print('  t %4.1f  gap %5s cm  v %.3f' % (x[0], '%.1f' % (x[1]*100) if np.isfinite(x[1]) else '-', x[4]))
