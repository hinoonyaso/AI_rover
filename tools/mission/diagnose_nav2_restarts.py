"""Reproduce isolated Gazebo/Nav2 startup and retain evidence; sends no goals.

한글: 격리 Gazebo/Nav2 기동을 반복해 증거를 보존하며 주행 목표는 보내지 않는다.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

from test_dashboard_gazebo import ROOT, stop, wait_localization_ready, wait_nav_ready, wait_ready


def snapshot(env, path):
    """Save the discovered ROS graph without using the ROS daemon. / ROS 데몬 없이 발견된 노드 목록을 저장한다."""
    result = subprocess.run(['ros2', 'node', 'list', '--no-daemon', '--spin-time', '2'],
                            env=env, capture_output=True, text=True, timeout=15)
    path.write_text(result.stdout + '\nSTDERR:\n' + result.stderr)
    return result.returncode


def main():
    """Run six starts and initialize Gazebo localization without motion. / 주행 없이 위치를 초기화하고 여섯 번 기동한다."""
    if (os.environ.get('ROS_DOMAIN_ID') != '31' or
            os.environ.get('ROS_AUTOMATIC_DISCOVERY_RANGE') != 'LOCALHOST' or
            os.environ.get('RMW_IMPLEMENTATION') != 'rmw_fastrtps_cpp'):
        raise RuntimeError('isolated ROS domain 31 required')
    if sys.argv[1:] not in ([], ['--udp']):
        raise ValueError('expected optional --udp')
    evidence = Path(tempfile.mkdtemp(prefix='jetinspect-nav2-startup-', dir='/tmp'))
    env = os.environ.copy()
    for key in ('ROS_STATIC_PEERS', 'ROS_DISCOVERY_SERVER', 'FASTRTPS_DEFAULT_PROFILES_FILE',
                'FASTDDS_DEFAULT_PROFILES_FILE', 'CYCLONEDDS_URI'):
        env.pop(key, None)
    env['GZ_IP'] = '127.0.0.1'
    env.pop('FASTDDS_BUILTIN_TRANSPORTS', None)
    if '--udp' in sys.argv:
        # This affects the isolated diagnostic processes only, not the robot or dashboard.
        # 한글: 로봇이나 대시보드가 아닌 격리 진단 프로세스에만 적용한다.
        env['FASTDDS_BUILTIN_TRANSPORTS'] = 'UDPv4'
    env['GZ_PARTITION'] = 'jetinspect_debug_' + uuid4().hex
    env['ROS_LOG_DIR'] = str(evidence / 'ros-logs')
    print(f'evidence: {evidence}; transport: {"UDPv4" if "--udp" in sys.argv else "default"}', flush=True)
    outcomes = []
    for number in range(1, 7):
        snapshot(env, evidence / f'nodes-before-{number}.txt')
        gz = nav = None
        gz_path, nav_path = evidence / f'gazebo-{number}.log', evidence / f'nav2-{number}.log'
        started = time.monotonic()
        with gz_path.open('w+') as gz_log, nav_path.open('w+') as nav_log:
            try:
                gz = subprocess.Popen(['ros2', 'launch', 'jetrover_gazebo', 'sim.launch.py', 'gui:=false',
                                       'depth_obstacles:=true'], cwd=ROOT, env=env, stdout=gz_log,
                                      stderr=subprocess.STDOUT, start_new_session=True)
                wait_ready(gz_path, 'Configured and activated mecanum_drive_controller', gz, 90)
                nav = subprocess.Popen(['ros2', 'launch', 'jetrover_navigation', 'nav2.launch.py',
                                        'use_sim_time:=true', f'params_file:={ROOT}/tools/nav/ab_params/nav2_params_mppi.yaml',
                                        'precise_approach:=false'], cwd=ROOT, env=env, stdout=nav_log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
                wait_localization_ready(nav_path, nav, 90)
                pose = subprocess.run(['/usr/bin/python3', str(ROOT / 'tools/mission/gazebo_nav_trial.py'), '--prepare-only'],
                                      env=env, capture_output=True, text=True, timeout=85)
                (evidence / f'pose-{number}.log').write_text(pose.stdout + '\nSTDERR:\n' + pose.stderr)
                if pose.returncode != 0:
                    raise RuntimeError('simulated initial pose setup failed')
                wait_nav_ready(nav_path, nav, 90)
                outcome = 'nav_ready'
            except (RuntimeError, subprocess.SubprocessError) as exc:
                outcome = 'failed'
                (evidence / f'error-{number}.txt').write_text(str(exc))
                for name, command in {
                    'amcl': ['ros2', 'lifecycle', 'get', '/amcl'],
                    'map': ['ros2', 'lifecycle', 'get', '/map_server'],
                    'smoother': ['ros2', 'lifecycle', 'get', '/smoother_server'],
                    'processes': ['ps', '-eo', 'pid,ppid,pgid,state,comm,args'],
                    'memory': ['free', '-m'],
                }.items():
                    try:
                        observed = subprocess.run(command, env=env, capture_output=True, text=True, timeout=8)
                        (evidence / f'{name}-{number}.txt').write_text(observed.stdout + '\nSTDERR:\n' + observed.stderr)
                    except (OSError, subprocess.SubprocessError) as error:
                        (evidence / f'{name}-{number}.txt').write_text(repr(error))
            finally:
                snapshot(env, evidence / f'nodes-during-{number}.txt')
                stop(nav)
                stop(gz)
                snapshot(env, evidence / f'nodes-after-{number}.txt')
        outcome_data = {'trial': number, 'outcome': outcome, 'elapsed_s': round(time.monotonic() - started, 1)}
        outcomes.append(outcome_data)
        print(json.dumps(outcome_data), flush=True)
    (evidence / 'results.json').write_text(json.dumps(outcomes, indent=2))
    if any(item['outcome'] != 'nav_ready' for item in outcomes):
        raise SystemExit('one or more Nav2 starts failed; inspect retained evidence')


if __name__ == '__main__':
    main()
