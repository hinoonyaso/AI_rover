#!/usr/bin/env python3
# 한글: 주행 중 특정 시점의 local/global 코스트맵, 전역 경로(/plan), 로봇·상자 정답 자세를 그림 한 장으로 저장한다(host).
#       회피가 왜 멈추는지 보려는 진단용. 목표를 보내고 --at 초 뒤(시뮬레이션 시간)에 찍는다.
"""Save a picture of the costmaps, the plan and the ground-truth robot/box (host, ROS_DOMAIN_ID=31, Nav2 running).

  python3 tools/sim/costmap_snapshot.py --scenario S2 --leg BA --at 12 20 [--out Log/sim_avoid/snap]
Teleports like avoid_trials.py, sends the goal, then writes <out>_<scenario><leg>_t<at>.png at each --at second.
Colours: local costmap lethal red / inscribed orange / inflated yellow, global costmap grey outline, plan blue,
footprint green, box magenta, goal cyan cross.
"""
import argparse
import math
import os
import sys

import cv2
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import OccupancyGrid
import numpy as np
import rclpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import avoid_trials as T  # noqa: E402

PPM = 160            # pixels per metre
SPAN = 1.2           # half size of the picture (m) around the robot/box midpoint


def grid_to_img(info, data, x0, y0, tf=None):
    """Occupancy values sampled onto the picture grid (nearest). tf = (c, s, tx, ty): picture(map) -> grid frame."""
    n = int(2 * SPAN * PPM)
    g = np.array(data).reshape(info.height, info.width)
    cols = x0 - SPAN + (np.arange(n) + 0.5) / PPM
    rows = y0 + SPAN - (np.arange(n) + 0.5) / PPM
    X, Y = np.meshgrid(cols, rows)
    if tf is not None:
        c, s, tx, ty = tf
        X, Y = c * X - s * Y + tx, s * X + c * Y + ty
    ix = ((X - info.origin.position.x) / info.resolution).astype(int)
    iy = ((Y - info.origin.position.y) / info.resolution).astype(int)
    ok = (ix >= 0) & (ix < info.width) & (iy >= 0) & (iy < info.height)
    out = np.full((n, n), -1, np.int16)
    out[ok] = g[iy[ok], ix[ok]]
    return out


def map_to_frame(node, frame):
    """(c, s, tx, ty) taking map-frame points into `frame` (the costmap's frame), or None."""
    if frame == 'map':
        return None
    try:
        tr = node.buf.lookup_transform(frame, 'map', rclpy.time.Time())
    except Exception:  # noqa: BLE001
        return None
    q = tr.transform.rotation
    yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
    return math.cos(yaw), math.sin(yaw), tr.transform.translation.x, tr.transform.translation.y


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--scenario', default='S2', choices=sorted(T.SCENARIOS))
    ap.add_argument('--leg', default='BA')
    ap.add_argument('--at', type=float, nargs='+', default=[15.0])
    ap.add_argument('--out', default=os.path.join(T.JSON_DIR, 'snap'))
    args = ap.parse_args()
    rclpy.init()
    node, gt = T.Runner(), T.GroundTruth()
    cost = {}
    node.create_subscription(OccupancyGrid, '/local_costmap/costmap', lambda m: cost.__setitem__('local', m), 1)
    node.create_subscription(OccupancyGrid, '/global_costmap/costmap', lambda m: cost.__setitem__('global', m), 1)
    try:
        node.spin(3.0)
        start, goal_xy = T.SCENARIOS[args.scenario]['legs'][args.leg]
        box = T.SCENARIOS[args.scenario]['box']
        T.setup_leg(node, gt, args.scenario, start, box)
        node.plans.clear()
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.pose.position.x, goal.pose.pose.position.y = goal_xy
        yaw = math.atan2(goal_xy[1] - start[1], goal_xy[0] - start[0])
        goal.pose.pose.orientation.z, goal.pose.pose.orientation.w = math.sin(yaw / 2), math.cos(yaw / 2)
        node.client.wait_for_server(timeout_sec=10.0)
        handle_f = node.client.send_goal_async(goal)
        rclpy.spin_until_future_complete(node, handle_f)
        t0 = node.now()
        for at in sorted(args.at):
            while node.now() - t0 < at:
                node.spin(0.1)
            g = gt.latest
            cx, cy = (g[1] + g[4]) / 2, (g[2] + g[5]) / 2
            n = int(2 * SPAN * PPM)

            def px(x, y):
                return int((x - (cx - SPAN)) * PPM), int((cy + SPAN - y) * PPM)

            def panel(kind):
                img = np.full((n, n, 3), 255, np.uint8)
                if kind in cost:
                    v = grid_to_img(cost[kind].info, cost[kind].data, cx, cy,
                                    map_to_frame(node, cost[kind].header.frame_id))
                    img[v == -1] = (235, 235, 235)
                    img[(v > 0) & (v < 99)] = (150, 230, 255)        # inflated, low cost
                    img[(v >= 99) & (v < 253)] = (60, 160, 255)      # inflated, high cost
                    img[v >= 253] = (40, 40, 230)                    # inscribed / lethal
                for k in range(-int(SPAN), int(SPAN) + 1):
                    gx, gy = px(round(cx) + k, 0)[0], px(0, round(cy) + k)[1]
                    cv2.line(img, (gx, 0), (gx, n), (200, 200, 200), 1)
                    cv2.line(img, (0, gy), (n, gy), (200, 200, 200), 1)
                    cv2.putText(img, f'x{round(cx) + k}', (gx + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (90, 90, 90), 1)
                    cv2.putText(img, f'y{round(cy) + k}', (2, gy - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (90, 90, 90), 1)
                if node.plans:
                    pts = [px(*p) for p in node.plans[-1][1]]
                    cv2.polylines(img, [np.array(pts, np.int32)], False, (200, 90, 0), 2)
                for poly, col in ((T.M.rect_corners(g[4], g[5], g[6], T.BOX_SIZE[0] / 2, T.BOX_SIZE[1] / 2), (200, 0, 200)),
                                  (T.M.rect_corners(g[1], g[2], g[3], *T.FOOTPRINT_HALF), (0, 150, 0))):
                    cv2.polylines(img, [np.array([px(*p) for p in poly], np.int32)], True, col, 2)
                cv2.circle(img, px(g[1] + 0.19 * math.cos(g[3]), g[2] + 0.19 * math.sin(g[3])), 4, (0, 150, 0), -1)
                cv2.drawMarker(img, px(*goal_xy), (255, 200, 0), cv2.MARKER_CROSS, 14, 2)
                cv2.putText(img, kind, (6, n - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
                return img
            img = np.hstack([panel('global'), panel('local')])
            for kind in ('global', 'local'):
                if kind in cost:
                    d = np.array(cost[kind].data)
                    print(f'  {kind} costmap frame {cost[kind].header.frame_id}: cells >=253 {np.mean(d >= 253) * 100:.1f} %, '
                          f'99..252 {np.mean((d >= 99) & (d < 253)) * 100:.1f} %, 1..98 {np.mean((d > 0) & (d < 99)) * 100:.1f} %, '
                          f'unknown {np.mean(d < 0) * 100:.1f} %', flush=True)
            cmd = node.cmd[-1] if node.cmd else (0, 0, 0, 0)
            cv2.putText(img, f'{args.scenario}{args.leg} t={at:.0f}s robot ({g[1]:.2f},{g[2]:.2f}) yaw {math.degrees(g[3]):.0f}  '
                        f'cmd {cmd[1]:.2f} {cmd[2]:.2f} {cmd[3]:.2f}', (6, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
            path = f'{args.out}_{args.scenario}{args.leg}_t{int(at)}.png'
            os.makedirs(os.path.dirname(path), exist_ok=True)
            cv2.imwrite(path, img)
            print('wrote', path, flush=True)
        handle_f.result().cancel_goal_async()
        node.spin(1.0)
    finally:
        gt.stop()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
