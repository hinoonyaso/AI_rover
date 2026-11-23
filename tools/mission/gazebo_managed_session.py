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
    # Pause/resume before driving starts mean nothing; only cancel (or EOF) stops preparation.
    # 한글: 주행 전 일시정지·재개는 의미가 없어 무시하고, 취소(또는 입력 종료)만 준비를 멈춘다.
    if select.select([sys.stdin], [], [], 0)[0]:
        line = sys.stdin.readline()
        if not line or line.strip() not in ('pause', 'resume'):
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


SIM_NAV_PARAMS = 'tools/nav/ab_params/nav2_params_sim_tol05.yaml'
INSPECT_NAV_PARAMS = 'tools/nav/ab_params/nav2_params_sim_inspect.yaml'
# Clear spawn for return missions; must match gazebo_nav_trial.py RETURN_START (troubleshooting/065).
# 한글: 복귀 임무용 여유 있는 시작점. gazebo_nav_trial.py RETURN_START와 같아야 한다.
RETURN_SPAWN = (1.30, 0.40, 1.45)


def workspace_paths(config):
    """Point absolute ``.../jetrover_ws/install/...`` paths at this checkout's install.

    Tracked variants hard-code ``/home/sang/jetrover_ws/install`` (BT XML); a clone elsewhere
    (host ``~/AI_rover``) would otherwise load another checkout's files.
    한글: 추적 변형의 절대 경로(BT XML)를 현재 체크아웃의 install로 바꾼다. 다른 위치의 복제본이
    다른 체크아웃의 파일을 읽지 않게 한다.
    """
    if isinstance(config, dict):
        return {key: workspace_paths(value) for key, value in config.items()}
    if isinstance(config, list):
        return [workspace_paths(value) for value in config]
    if isinstance(config, str) and '/jetrover_ws/install/' in config:
        return str(ROOT / 'install') + '/' + config.split('/jetrover_ws/install/', 1)[1]
    return config


def navigation_nav_params(directory):
    """Sim-validated Nav2 variant for navigation missions (2026-11-22, troubleshooting/065).

    The dashboard used ``nav2_params_mppi.yaml`` generated on 2026-10-11, before the official
    parameters changed; ``nav2_params_sim_tol05.yaml`` is the latest variant validated in Gazebo.
    한글: 주행 임무용 시뮬 검증 변형. 예전 10-11 생성 MPPI 파일 대신 Gazebo에서 검증한 최신 변형을 쓴다.
    """
    config = workspace_paths(yaml.safe_load((ROOT / SIM_NAV_PARAMS).read_text()))
    target = directory / 'navigation_nav.yaml'
    target.write_text(yaml.safe_dump(config, sort_keys=False))
    return target


def inspection_nav_params(directory):
    """Limit simulated inspection pose error for camera visibility.

    한글: 카메라 시야 확보를 위해 시뮬레이션 점검의 도착 오차를 제한한다.
    """
    # Inspection keeps the MPPI variant it was validated with (now tracked as nav2_params_sim_inspect.yaml):
    # the DWB sim variant with a 3 cm tolerance found no valid trajectory in front of the fixture
    # (troubleshooting/065, 2026-11-23). 한글: 점검은 검증된 MPPI 설정을 쓴다(이제 git 추적). DWB 시뮬 변형 + 3 cm로는
    # 픽스처 앞에서 유효 궤적이 없어 진행하지 못했다.
    config = workspace_paths(yaml.safe_load((ROOT / INSPECT_NAV_PARAMS).read_text()))
    goal = config['controller_server']['ros__parameters']['general_goal_checker']
    goal['xy_goal_tolerance'] = 0.03
    goal['yaw_goal_tolerance'] = 0.08
    target = directory / 'inspection_nav.yaml'
    target.write_text(yaml.safe_dump(config, sort_keys=False))
    return target


def main():
    """Prepare, run, and clean up an isolated Gazebo mission. / 격리 Gazebo 임무를 준비·실행·정리한다."""
    require_simulation()
    if len(sys.argv) != 2 or sys.argv[1] not in ('navigate_demo', 'inspect_stack_light', 'return_to_start'):
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
                # Every dashboard mission starts at the clear spawn; the wall-side default made
                # planning from the start fail intermittently (troubleshooting/065).
                # 한글: 모든 대시보드 임무는 여유 있는 시작점에서 출발한다(벽 옆 기본값은 간헐적으로 경로 실패).
                spawn = [f'x:={RETURN_SPAWN[0]}', f'y:={RETURN_SPAWN[1]}', f'yaw:={RETURN_SPAWN[2]}']
                gazebo = subprocess.Popen(['ros2', 'launch', 'jetrover_gazebo', 'sim.launch.py', 'gui:=false', 'depth_obstacles:=true', *spawn],
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
                              else navigation_nav_params(directory))
                nav = subprocess.Popen(['ros2', 'launch', 'jetrover_navigation', 'nav2.launch.py', 'use_sim_time:=true',
                                        f'params_file:={nav_params}', 'precise_approach:=false'],
                                       cwd=ROOT, env=env, stdout=navlog, stderr=subprocess.STDOUT, start_new_session=True)
                wait_log(directory / 'nav.log', 'localization_ready', nav, 100)
                print('MISSION_STAGE gazebo_navigation', flush=True)
                args = ['/usr/bin/python3', str(ROOT / 'tools/mission/gazebo_nav_trial.py'), '--managed']
                if sys.argv[1] == 'inspect_stack_light':
                    args.append('--inspect')
                if sys.argv[1] == 'return_to_start':
                    args.append('--return')
                else:
                    args.append('--clear-start')
                trial = subprocess.Popen(args, cwd=ROOT, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT, start_new_session=True)
                cancel_sent = False
                buffer = b''
                while trial.poll() is None or select.select([trial.stdout], [], [], 0)[0]:
                    ready, _, _ = select.select([trial.stdout, sys.stdin], [], [], .2)
                    if sys.stdin in ready and not cancel_sent:
                        # Forward pause/resume; anything else (or EOF) is a single cancel.
                        # 한글: 일시정지·재개는 그대로 전달하고, 그 밖의 입력(또는 종료)은 취소 한 번으로 보낸다.
                        line = sys.stdin.readline()
                        command = line.strip() if line and line.strip() in ('pause', 'resume') else 'cancel'
                        cancel_sent = command == 'cancel'
                        try:
                            trial.stdin.write(command.encode() + b'\n')
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
            # Optional diagnostics: keep the session logs before the temporary folder is removed.
            # 한글: 진단용 선택 기능. 임시 폴더가 지워지기 전에 세션 로그를 지정 폴더로 복사한다.
            keep = os.environ.get('JETINSPECT_SESSION_LOG_DIR')
            if keep:
                target = Path(keep) / time.strftime('%Y%m%d_%H%M%S')
                target.mkdir(parents=True, exist_ok=True)
                for log in directory.glob('*.log'):
                    (target / log.name).write_bytes(log.read_bytes())
        print('MISSION_RESULT ' + json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
