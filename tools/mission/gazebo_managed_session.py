"""Own one isolated Gazebo environment and its dashboard mission.

한글: 대시보드 임무 한 건의 격리 Gazebo 환경을 생성하고 정리한다.
"""
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import tempfile
import time

import yaml

from gazebo_nav_trial import require_simulation

ROOT = Path(__file__).resolve().parents[2]


class Canceled(Exception):
    pass


def stop_group(process):
    """Stop only a process group started by this session. / 이 세션이 시작한 프로세스 그룹만 종료한다."""
    if process is None:
        return
    for sig, delay in ((signal.SIGINT, 2), (signal.SIGTERM, 1), (signal.SIGKILL, 1)):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            break
        end = time.monotonic() + delay
        while time.monotonic() < end:
            process.poll()
            try:
                os.killpg(process.pid, 0)
            except ProcessLookupError:
                break
            time.sleep(.1)
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        raise RuntimeError('gazebo_cleanup_unconfirmed') from None


def check_cancel():
    """Treat an explicit cancel or closed parent pipe as cancellation. / 취소 또는 부모 연결 종료를 처리한다."""
    if select.select([sys.stdin], [], [], 0)[0]:
        sys.stdin.readline()
        raise Canceled()


def wait_log(path, text, process, timeout):
    """Wait for a bounded startup signal while accepting cancellation.

    한글: 취소를 처리하면서 제한 시간 내 기동 신호를 기다린다.
    """
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        check_cancel()
        if process.poll() is not None:
            raise RuntimeError('gazebo_start_failed')
        if path.exists():
            content = path.read_text(errors='replace')
            if text == 'localization_ready':
                if any('[lifecycle_manager_localization]' in line and 'Managed nodes are active' in line for line in content.splitlines()):
                    return
            elif text in content:
                return
        time.sleep(.5)
    raise RuntimeError('gazebo_start_timeout')


def run_checked(command, env, log, timeout):
    """Run one owned setup command with timeout and cancellation. / 소유한 준비 명령을 시간 제한과 취소 처리로 실행한다."""
    process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        end = time.monotonic() + timeout
        while process.poll() is None and time.monotonic() < end:
            check_cancel()
            time.sleep(.2)
        if process.poll() is None or process.returncode != 0:
            raise RuntimeError('gazebo_fixture_unavailable')
    finally:
        stop_group(process)


def inspection_nav_params(directory):
    """Limit simulated inspection pose error for camera visibility.

    한글: 카메라 시야 확보를 위해 시뮬레이션 점검의 도착 오차를 제한한다.
    """
    source = ROOT / 'tools/nav/ab_params/nav2_params_mppi.yaml'
    config = yaml.safe_load(source.read_text())
    goal = config['controller_server']['ros__parameters']['general_goal_checker']
    goal['xy_goal_tolerance'] = 0.03
    goal['yaw_goal_tolerance'] = 0.08
    target = directory / 'inspection_nav.yaml'
    target.write_text(yaml.safe_dump(config, sort_keys=False))
    return target


def main():
    """Prepare, run, and clean up an isolated Gazebo mission. / 격리 Gazebo 임무를 준비·실행·정리한다."""
    require_simulation()
    if len(sys.argv) != 2 or sys.argv[1] not in ('navigate_demo', 'inspect_stack_light'):
        raise ValueError('unsupported simulated mission')
    env = os.environ.copy()
    if not env.get('GZ_PARTITION', '').startswith('jetinspect_dashboard_'):
        raise RuntimeError('dedicated Gazebo partition required')
    # Termination also unwinds the owned child groups instead of orphaning them.
    # 한글: 종료 신호에도 소유한 하위 프로세스 그룹을 정리한다.
    def terminate(_sig, _frame):
        raise Canceled()
    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    gazebo = nav = trial = None
    result = None
    with tempfile.TemporaryDirectory(prefix='jetinspect-session-', dir='/tmp') as folder:
        directory = Path(folder)
        try:
            nodes = subprocess.run(['ros2', 'node', 'list', '--no-daemon', '--spin-time', '2'],
                                   env=env, capture_output=True, text=True, timeout=12, check=True)
            conflicts = {'/base_node', '/controller_manager', '/amcl', '/map_server', '/bt_navigator', '/ros_gz_bridge'}
            if conflicts.intersection(nodes.stdout.splitlines()):
                raise RuntimeError('gazebo_environment_busy')
            check_cancel()
            with (directory / 'gazebo.log').open('w+') as gzlog, (directory / 'nav.log').open('w+') as navlog, (directory / 'setup.log').open('w+') as setup:
                gazebo = subprocess.Popen(['ros2', 'launch', 'jetrover_gazebo', 'sim.launch.py', 'gui:=false', 'depth_obstacles:=true'],
                                          cwd=ROOT, env=env, stdout=gzlog, stderr=subprocess.STDOUT, start_new_session=True)
                wait_log(directory / 'gazebo.log', 'Configured and activated mecanum_drive_controller', gazebo, 100)
                if sys.argv[1] == 'inspect_stack_light':
                    fixture = ROOT / 'tools/mission/stack_light_robot_view.sdf'
                    run_checked(['ros2', 'run', 'ros_gz_sim', 'create', '-world', 'jetrover_room', '-file', str(fixture),
                                 '-name', 'robot_view_stack_light'], env, setup, 30)
                    pose = ('name: "robot_view_stack_light", position: {x: 1.001, y: 1.770, z: 0.158}, '
                            'orientation: {x: -0.301, y: 0.301, z: 0.640, w: 0.640}')
                    run_checked(['gz', 'service', '-s', '/world/jetrover_room/set_pose', '--reqtype', 'gz.msgs.Pose',
                                 '--reptype', 'gz.msgs.Boolean', '--timeout', '5000', '--req', pose], env, setup, 10)
                    setup.flush()
                    if 'data: true' not in (directory / 'setup.log').read_text(errors='replace'):
                        raise RuntimeError('gazebo_fixture_unavailable')
                nav_params = (inspection_nav_params(directory) if sys.argv[1] == 'inspect_stack_light'
                              else ROOT / 'tools/nav/ab_params/nav2_params_mppi.yaml')
                nav = subprocess.Popen(['ros2', 'launch', 'jetrover_navigation', 'nav2.launch.py', 'use_sim_time:=true',
                                        f'params_file:={nav_params}', 'precise_approach:=false'],
                                       cwd=ROOT, env=env, stdout=navlog, stderr=subprocess.STDOUT, start_new_session=True)
                wait_log(directory / 'nav.log', 'localization_ready', nav, 100)
                print('MISSION_STAGE gazebo_navigation', flush=True)
                args = ['/usr/bin/python3', str(ROOT / 'tools/mission/gazebo_nav_trial.py'), '--managed']
                if sys.argv[1] == 'inspect_stack_light':
                    args.append('--inspect')
                trial = subprocess.Popen(args, cwd=ROOT, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT, start_new_session=True)
                cancel_sent = False
                buffer = b''
                while trial.poll() is None or select.select([trial.stdout], [], [], 0)[0]:
                    ready, _, _ = select.select([trial.stdout, sys.stdin], [], [], .2)
                    if sys.stdin in ready and not cancel_sent:
                        sys.stdin.readline()
                        cancel_sent = True
                        try:
                            trial.stdin.write(b'cancel\n')
                            trial.stdin.flush()
                        except (BrokenPipeError, OSError):
                            pass
                    if trial.stdout in ready:
                        chunk = os.read(trial.stdout.fileno(), 65536)
                        if not chunk:
                            break
                        buffer += chunk
                        while b'\n' in buffer:
                            line, buffer = buffer.split(b'\n', 1)
                            if line.startswith(b'MISSION_RESULT '):
                                try:
                                    result = json.loads(line[len(b'MISSION_RESULT '):])
                                except ValueError:
                                    pass
                            else:
                                print(line.decode(errors='replace'), flush=True)
                if not isinstance(result, dict):
                    raise RuntimeError('gazebo_result_unconfirmed')
        except Canceled:
            result = {'state': 'canceled', 'reason': 'gazebo_preparation_canceled'}
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            reason = str(error) if str(error) in ('gazebo_environment_busy', 'gazebo_start_failed', 'gazebo_start_timeout',
                                                  'gazebo_fixture_unavailable', 'gazebo_result_unconfirmed') else 'gazebo_start_failed'
            result = {'state': 'interrupted', 'reason': reason}
        finally:
            try:
                for process in (trial, nav, gazebo):
                    stop_group(process)
            except RuntimeError:
                result = {'state': 'interrupted', 'reason': 'gazebo_cleanup_unconfirmed'}
        print('MISSION_RESULT ' + json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
