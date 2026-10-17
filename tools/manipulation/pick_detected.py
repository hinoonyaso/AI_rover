#!/usr/bin/env python3
# 한글: 카메라로 찾은 큐브를 집는다(2단계: 보고 집기). 관찰 자세(look_floor) → cubes/<색> 중앙값 → URDF IK(arm_ik.py)로
#       큐브 위 15 cm·큐브 높이 관절 목표 → MoveIt으로 이동(충돌 검사) → 닫기 → 들기. 큐브 위치를 미리 알 필요가 없다.
#       닫기: --gripper sim이면 MoveIt gripper 그룹(r_joint 0.3), real이면 접촉 파지 Action arm/grasp(실기 T6).
#       팔이 움직인다. cube_detector.py와 move_group(mode:=real)이 떠 있어야 한다.
"""Pick a cube found by the camera (no known position). THE ARM MOVES.

Needs move_group (mode:=real) and jetrover_perception cube_detector.py running.
Usage: python3 tools/manipulation/pick_detected.py red|green|blue [--gripper sim|real] [--place]
Steps: look_floor -> median of cubes/<colour> (base_footprint) -> IK (tools/sim/arm_ik.py, gripper
down) above the cube (0.15 m) and at --grasp-z -> MoveIt moves -> close -> lift -> look_floor again:
still seen on the floor = FAIL. --place puts it back down and opens. Exit 1 on a failure.
"""
import argparse
import os
import subprocess
import sys
import tempfile
import time
import types

import numpy as np
from geometry_msgs.msg import PointStamped

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'sim'))
import moveit_t7 as T  # noqa: E402
from arm_ik import load_chain, solve  # noqa: E402


def urdf_path():
    """Real-robot URDF (same arm kinematics as the simulation URDF)."""
    from ament_index_python.packages import get_package_share_directory
    xacro = os.path.join(get_package_share_directory('jetrover_description'), 'urdf', 'jetrover.xacro')
    out = tempfile.NamedTemporaryFile(suffix='.urdf', delete=False).name
    with open(out, 'w') as f:
        f.write(subprocess.run(['xacro', xacro], capture_output=True, text=True, check=True).stdout)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('colour', choices=('red', 'green', 'blue'))
    ap.add_argument('--gripper', choices=('sim', 'real'), default='sim')
    ap.add_argument('--close', type=float, default=0.3, help='sim: r_joint close target')
    ap.add_argument('--samples', type=int, default=10)
    # end_effector_link는 손끝이 아니다: 손끝은 그보다 약 3.5 cm 아래(URDF 손가락 메쉬 FK, 2026-10-17).
    # 0.025로 두면 손끝이 바닥 1 cm 아래로 계획돼 Gazebo에서 바닥에 막혀 큐브를 놓쳤다 → 0.045(손끝 바닥 위 약 1 cm).
    # end_effector_link is ~3.5 cm above the fingertips; 0.025 planned the tips 1 cm into the floor.
    ap.add_argument('--grasp-z', type=float, default=0.045,
                    help='end_effector_link height at the grasp (m); fingertips are ~0.035 lower')
    ap.add_argument('--place', action='store_true')
    ap.add_argument('--scale', type=float, default=0.3)
    args = ap.parse_args()

    rig = T.Rig(types.SimpleNamespace(scale=args.scale, tol=0.05, settle=1.5, temp_stop=None))
    ns = T.named_states()
    if not rig.move.wait_for_server(timeout_sec=15):
        sys.exit('move_action not available')
    pts = []
    rig.n.create_subscription(PointStamped, f'cubes/{args.colour}',
                              lambda m: pts.append((m.point.x, m.point.y, m.point.z)), 10)
    rig.spin(2.0)

    def step(ok, what):
        if not ok:
            last = rig.rows[-1] if rig.rows else {}
            print(f'FAIL at: {what}; last move errors {last.get("err")}', flush=True)
            now = {j: round(rig.js.get(j, float('nan')), 3) for j in T.ARM + ['r_joint']}
            print(f'  joints now {now}', flush=True)
            sys.exit(1)

    step(rig.go('look_floor', 'arm', ns['look_floor']), 'look_floor')
    pts.clear()
    t0 = time.monotonic()
    while len(pts) < args.samples and time.monotonic() - t0 < 10.0:
        rig.spin(0.1)
    step(len(pts) >= 3, f'detect {args.colour} ({len(pts)} detections)')
    x, y, z = np.median(np.array(pts), axis=0)
    print(f'  {args.colour} cube at ({x:.3f}, {y:.3f}) m in base_footprint, top z {z:.3f} '
          f'({len(pts)} detections)', flush=True)

    chain = load_chain(urdf_path())
    q = np.array([ns['home'][j] for j in T.ARM])     # IK 시작값 = 홈 자세 / IK seed: the home pose
    poses = {}
    for key, zz in (('above', 0.15), ('grasp', args.grasp_z)):
        q, err, tilt = solve(chain, np.array([x, y, zz]), q)
        # 위에서 잡으려면 그리퍼가 거의 아래를 봐야 한다 — 15° 넘게 기울면 닿지 않는 자리로 본다(약 0.30 m 너머).
        # From above the gripper must point nearly down: > 15 deg tilt = out of reach (beyond ~0.30 m).
        step(err < 0.005 and tilt < 15.0, f'IK {key} (err {err * 1000:.1f} mm, tilt {tilt:.1f} deg)')
        poses[key] = dict(zip(T.ARM, q.tolist()))
        print(f'  IK {key} z {zz}: {np.round(q, 3).tolist()}', flush=True)

    step(rig.go('open gripper', 'gripper', ns['gripper_open']), 'open')
    step(rig.go('above cube', 'arm', poses['above']), 'above')
    step(rig.go('down to cube', 'arm', poses['grasp']), 'down')
    if args.gripper == 'sim':
        rig.go('close gripper', 'gripper', {'r_joint': args.close})
        rig.spin(1.0)
        # 참고용 값일 뿐: 큐브를 쥐어도(0.303) 빈손이어도(0.309) 명령 근처까지 간다(2026-10-18) —
        # 성공 여부는 아래 '다시 보기' 확인으로 판단한다.
        # Informative only: ~0.30 with the cube held (0.303) and with nothing (0.309); the pick is
        # judged by looking at the floor again below.
        print(f'  gripper r_joint {rig.js.get("r_joint", float("nan")):.3f} (cmd {args.close})', flush=True)
    else:
        from jetrover_interfaces.action import Grasp
        g = Grasp.Goal()
        g.profile = 'cube3cm'
        fut = rig.grasp.send_goal_async(g)
        rig.wait(fut, 5)
        gh = fut.result()
        step(gh is not None and gh.accepted, 'grasp accepted')
        rf = gh.get_result_async()
        rig.wait(rf, 40)
        res = rf.result().result if rf.done() else None
        step(res is not None and res.success, f'grasp ({res.reason if res else None})')
    step(rig.go('lift', 'arm', poses['above']), 'lift')
    # 들었는지 확인: 다시 바닥을 보고 바닥 높이(z < 0.06)에 큐브가 보이면 실패 — 자리와 무관하게(밀려나
    # 6 cm 옆에 떨어진 경우를 놓쳤다). 닫힘 각도로는 판단이 안 된다(빈손도 0.309, 2026-10-17).
    # 그리퍼에 든 큐브는 높이가 높아 걸리지 않는다.
    # Check the pick by looking again: the cube seen at floor height anywhere = FAIL (a pushed-away
    # cube 6 cm off was missed by a 3 cm radius); the gripper angle cannot tell (0.309 when empty).
    step(rig.go('look again', 'arm', ns['look_floor']), 'look again')
    # 5 s 동안 본다: 시뮬레이션이 느리면 2 s에 2건만 와서 기준(3건)을 못 넘고 거짓 성공이 났다(2026-10-18).
    # Watch for 5 s: a slow simulation gave only 2 detections in 2 s and a false PICKED.
    pts.clear()
    t0 = time.monotonic()
    while time.monotonic() - t0 < 5.0:
        rig.spin(0.1)
    left = [p for p in pts if p[2] < 0.06]
    where = np.round(np.median(np.array(left), axis=0)[:2], 3).tolist() if left else None
    step(len(left) < 2, f'lift check: cube still on the floor at {where} ({len(left)}/{len(pts)})')
    print(f'PICKED {args.colour} (not on the floor in 5 s; {len(pts)} detections in total)', flush=True)
    if args.place:
        step(rig.go('place', 'arm', poses['grasp']), 'place')
        if args.gripper == 'real':
            from jetrover_interfaces.srv import Release
            rr = rig.release.call_async(Release.Request())
            rig.wait(rr, 5)
            rig.spin(2.5)
        rig.go('open gripper', 'gripper', ns['gripper_open'])
        rig.go('retreat', 'arm', poses['above'])
        print(f'PLACED {args.colour}', flush=True)


if __name__ == '__main__':
    main()
