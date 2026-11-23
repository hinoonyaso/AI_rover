#!/usr/bin/env python3
"""Run one isolated Gazebo return_to_start mission with a pause and resume, like the dashboard.

Starts ``gazebo_managed_session.py return_to_start`` with the dashboard's isolation settings
(domain 31, loopback Fast DDS, unique Gazebo partition), sends ``pause`` a few seconds into the
first leg, ``resume`` after a hold, and prints stage changes and the final result. Simulation
only; it refuses nothing itself, the session/trial scripts enforce the simulation checks.

한글: 대시보드와 같은 격리 설정으로 Gazebo 출발점 복귀 임무를 한 번 실행하며, 첫 구간 도중
일시정지·재개를 보내고 단계와 결과를 출력한다. 시뮬레이션 전용.
"""
import argparse
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pause-after', type=float, default=6.0, help='seconds into leg 1 (0 = no pause)')
    parser.add_argument('--hold', type=float, default=8.0, help='seconds paused before resume')
    parser.add_argument('--timeout', type=float, default=900.0)
    parser.add_argument('--kind', choices=('return_to_start', 'navigate_demo', 'inspect_stack_light'), default='return_to_start')
    args = parser.parse_args()
    env = os.environ.copy()
    for key in ('ROS_STATIC_PEERS', 'ROS_DISCOVERY_SERVER', 'FASTRTPS_DEFAULT_PROFILES_FILE',
                'FASTDDS_DEFAULT_PROFILES_FILE', 'CYCLONEDDS_URI', 'PYTHONPATH',
                'FASTDDS_BUILTIN_TRANSPORTS', 'ROS_LOCALHOST_ONLY'):
        env.pop(key, None)
    env.update({'ROS_DOMAIN_ID': '31', 'ROS_AUTOMATIC_DISCOVERY_RANGE': 'SUBNET',
                'RMW_IMPLEMENTATION': 'rmw_fastrtps_cpp', 'GZ_IP': '127.0.0.1',
                'FASTRTPS_DEFAULT_PROFILES_FILE': str(ROOT / 'tools/mission/fastdds-loopback.xml'),
                'GZ_PARTITION': 'jetinspect_dashboard_' + uuid.uuid4().hex})
    command = ('set -e; source /opt/ros/jazzy/setup.bash; source "$1/install/setup.bash"; '
               'exec /usr/bin/python3 "$1/tools/mission/gazebo_managed_session.py" "$2"')
    child = subprocess.Popen(['/bin/bash', '-c', command, 'trial', str(ROOT), args.kind], env=env, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    start = time.monotonic()
    leg_started = paused_at = None
    navigation_marks = 0
    resumed = sent_pause = False
    result = None

    def stamp(text):
        print(f'{time.monotonic() - start:6.1f}s {text}', flush=True)

    def send(word):
        child.stdin.write(word + '\n')
        child.stdin.flush()
        stamp('>>> ' + word)

    while time.monotonic() - start < args.timeout:
        if select.select([child.stdout], [], [], 0.5)[0]:
            line = child.stdout.readline()
            if not line:
                break
            line = line.rstrip()
            if line.startswith(('MISSION_', 'simulation goal', 'action status', 'start reported')):
                stamp(line[:200])
            if line == 'MISSION_STAGE gazebo_navigation':
                navigation_marks += 1
                if navigation_marks == 2:  # the session prints one before the trial starts
                    leg_started = time.monotonic()
            elif line == 'MISSION_STAGE gazebo_paused':
                paused_at = time.monotonic()
            elif line.startswith('MISSION_RESULT '):
                result = json.loads(line[len('MISSION_RESULT '):])
        now = time.monotonic()
        if args.pause_after > 0 and leg_started and not sent_pause and now - leg_started > args.pause_after:
            send('pause')
            sent_pause = True
        if paused_at and not resumed and now - paused_at > args.hold:
            send('resume')
            resumed = True
    if child.poll() is None:
        send('cancel')
    child.wait(60)
    stamp(f'result {result}')
    return 0 if result and result.get('state') == 'succeeded' else 1


if __name__ == '__main__':
    sys.exit(main())
