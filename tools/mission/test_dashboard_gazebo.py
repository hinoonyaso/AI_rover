"""Repeat isolated dashboard-to-Gazebo navigation trials.

한글: 대시보드부터 Gazebo까지 격리 주행 시험을 반복한다.
"""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
VENV = Path.home() / '.local/share/jetinspect-ops/venv/bin/python'
BASE = 'http://127.0.0.1:18765'


def request(path, data=None):
    """Call the local test API. / 로컬 테스트 API를 호출한다."""
    headers = {'Host': '127.0.0.1:18765', 'Origin': BASE, 'Content-Type': 'application/json'}
    body = json.dumps(data).encode() if data is not None else None
    with urlopen(Request(BASE + path, data=body, headers=headers), timeout=6) as response:
        return json.load(response)


def webdriver(path, data=None):
    """Call the isolated browser driver. / 격리된 브라우저 드라이버를 호출한다."""
    body = json.dumps(data).encode() if data is not None else None
    with urlopen(Request('http://127.0.0.1:18444' + path, data=body,
                         headers={'Content-Type': 'application/json'}), timeout=20) as response:
        return json.load(response)['value']


def stop(process):
    """Stop the entire process group even if the launch parent already exited.

    한글: launch 부모가 먼저 종료돼도 시험 프로세스 그룹 전체를 정리한다.
    """
    if process is None:
        return
    for sig, timeout in ((signal.SIGINT, 8), (signal.SIGTERM, 3), (signal.SIGKILL, 1)):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            break
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                os.killpg(process.pid, 0)
            except ProcessLookupError:
                break
            time.sleep(.2)
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f'test process {process.pid} did not stop')


def wait_ready(path, phrase, process, timeout):
    """Wait for a launch message with a timeout. / 제한 시간 안에 기동 로그를 확인한다."""
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        if process.poll() is not None:
            raise RuntimeError(f'launch exited early: {path.read_text(errors="replace")[-2000:]}')
        if path.exists() and phrase in path.read_text(errors='replace'):
            return
        time.sleep(1)
    tail = path.read_text(errors='replace')[-2500:] if path.exists() else '(no launch log)'
    raise RuntimeError(f'launch timed out: {phrase}; recent log: {tail}')


def nav_log_ready(text):
    """Check that each lifecycle manager confirmed readiness. / 각 라이프사이클 관리자의 준비 완료를 확인한다."""
    lines = text.splitlines()
    managers = ('[lifecycle_manager_localization]', '[lifecycle_manager_navigation]')
    return all(any(manager in line and 'Managed nodes are active' in line for line in lines) for manager in managers)


def wait_localization_ready(path, process, timeout):
    """Wait until AMCL is active before sending the simulated initial pose.

    한글: 시뮬레이션 초기 자세를 보내기 전에 AMCL 활성화를 기다린다.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError('Nav2 launch exited before localization became active')
        lines = path.read_text(errors='replace').splitlines() if path.exists() else []
        if any('[lifecycle_manager_localization]' in line and 'Managed nodes are active' in line for line in lines):
            return
        time.sleep(1)
    raise RuntimeError('localization lifecycle manager did not become active')


def wait_nav_ready(path, process, timeout):
    """Require both lifecycle managers to report active. / 위치 추정과 주행 관리자의 준비를 모두 확인한다."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError('Nav2 launch exited before both managers became active')
        text = path.read_text(errors='replace') if path.exists() else ''
        if nav_log_ready(text):
            return
        time.sleep(1)
    raise RuntimeError('Nav2 lifecycle managers did not both become active')


def main():
    """Run two independent starts through the API. / API로 독립된 시작점 시험을 두 번 수행한다."""
    if (os.environ.get('ROS_DOMAIN_ID') != '31' or os.environ.get('ROS_AUTOMATIC_DISCOVERY_RANGE') != 'LOCALHOST'
            or os.environ.get('RMW_IMPLEMENTATION') != 'rmw_fastrtps_cpp'):
        raise RuntimeError('requires isolated ROS domain 31 and localhost discovery')
    if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1] not in ('--inspection', '--inspection-browser', '--inspection-cancel', '--inspection-restart', '--inspection-repeat', '--inspection-inverted', '--inspection-bridge-loss')):
        raise ValueError('unsupported option')
    bridge_loss = '--inspection-bridge-loss' in sys.argv
    repeat_inspection = '--inspection-repeat' in sys.argv
    inverted_inspection = '--inspection-inverted' in sys.argv
    restart_inspection = '--inspection-restart' in sys.argv
    cancel_inspection = '--inspection-cancel' in sys.argv
    browser = '--inspection-browser' in sys.argv or cancel_inspection
    inspection = '--inspection' in sys.argv or browser or restart_inspection or repeat_inspection or inverted_inspection or bridge_loss
    with tempfile.TemporaryDirectory(dir='/tmp') as temp:
        directory = Path(temp)
        env = os.environ.copy()
        for key in ('ROS_STATIC_PEERS', 'ROS_DISCOVERY_SERVER', 'FASTRTPS_DEFAULT_PROFILES_FILE', 'FASTDDS_DEFAULT_PROFILES_FILE', 'CYCLONEDDS_URI', 'FASTDDS_BUILTIN_TRANSPORTS', 'ROS_LOCALHOST_ONLY'):
            env.pop(key, None)
        env['GZ_IP'] = '127.0.0.1'
        env['ROS_AUTOMATIC_DISCOVERY_RANGE'] = 'SUBNET'
        env['FASTRTPS_DEFAULT_PROFILES_FILE'] = str(ROOT / 'tools/mission/fastdds-loopback.xml')
        env['GZ_PARTITION'] = 'jetinspect_' + uuid4().hex
        env['ROS_LOG_DIR'] = str(directory / 'ros-logs')
        web_env = env.copy()
        web_env['PYTHONPATH'] = str(ROOT / 'tools/ops/backend') + ':' + str(ROOT / 'tools/ops')
        web_env['MISSION_BROWSER_TEST_DB'] = str(directory / 'missions.sqlite3')
        web_env['MISSION_TEST_CHILD_LOG_DIR'] = str(directory / 'child-logs')
        server_log = (directory / 'server.log').open('w+')
        server = subprocess.Popen([str(VENV), '-m', 'uvicorn', 'browser_test_server:app', '--host', '127.0.0.1', '--port', '18765'], env=web_env, stdout=server_log, stderr=subprocess.STDOUT, start_new_session=True)
        results = []
        driver = None
        session = None
        try:
            deadline = time.monotonic() + 15
            while True:
                try:
                    request('/api/missions')
                    break
                except (URLError, OSError):
                    if time.monotonic() > deadline:
                        raise
                    time.sleep(.5)
            if browser:
                driver = subprocess.Popen(['geckodriver', '--host', '127.0.0.1', '--port', '18444'],
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                deadline = time.monotonic() + 15
                while True:
                    try:
                        if webdriver('/status')['ready']:
                            break
                    except (URLError, OSError):
                        pass
                    if time.monotonic() > deadline:
                        raise RuntimeError('browser driver unavailable')
                    time.sleep(.2)
                session = webdriver('/session', {'capabilities': {'alwaysMatch': {'browserName': 'firefox',
                                    'moz:firefoxOptions': {'args': ['-headless']}}}})['sessionId']
                session_path = '/session/' + session
                webdriver(session_path + '/url', {'url': BASE + '/'})

                def click_xpath(selector):
                    deadline = time.monotonic() + 20
                    while True:
                        try:
                            element = webdriver(session_path + '/element', {'using': 'xpath', 'value': selector})
                            webdriver(session_path + '/element/' + element['element-6066-11e4-a52e-4f735466cecf'] + '/click', {})
                            return
                        except (HTTPError, URLError, OSError):
                            if time.monotonic() > deadline:
                                raise
                            time.sleep(.2)
            trial_count = 3 if repeat_inspection else (1 if inspection else 2)
            for trial in range(1, trial_count + 1):
                print(f'trial {trial}: starting fresh Gazebo and Nav2', flush=True)
                gz_path, nav_path = directory / f'gz{trial}.log', directory / f'nav{trial}.log'
                with gz_path.open('w+') as gz_log, nav_path.open('w+') as nav_log:
                    gz = nav = None
                    try:
                        gz = subprocess.Popen(['ros2', 'launch', 'jetrover_gazebo', 'sim.launch.py', 'gui:=false', 'depth_obstacles:=true'], cwd=ROOT, env=env, stdout=gz_log, stderr=subprocess.STDOUT, start_new_session=True)
                        wait_ready(gz_path, 'Configured and activated mecanum_drive_controller', gz, 90)
                        if inspection and not cancel_inspection and not restart_inspection:
                            fixture_path = ROOT / 'tools/mission/stack_light_robot_view.sdf'
                            if inverted_inspection:
                                tree = ET.parse(fixture_path)
                                for name, color in (('red', '0.025 0 0 1'), ('yellow', '1 1 0 1'), ('green', '0 0.025 0 1')):
                                    material = tree.find(f".//visual[@name='{name}']/material")
                                    if material is None:
                                        raise RuntimeError('fixture visual missing')
                                    for tag in ('ambient', 'diffuse', 'emissive'):
                                        material.find(tag).text = color
                                fixture_path = directory / 'inverted_robot_view.sdf'
                                tree.write(fixture_path, encoding='unicode', xml_declaration=True)
                            subprocess.run(['ros2', 'run', 'ros_gz_sim', 'create', '-world', 'jetrover_room',
                                            '-file', str(fixture_path),
                                            '-name', 'robot_view_stack_light'], env=env, check=True, timeout=30)
                            fixture_y = '10.0' if bridge_loss else '1.770'
                            pose = (f'name: "robot_view_stack_light", position: {{x: 1.001, y: {fixture_y}, z: 0.158}}, '
                                    'orientation: {x: -0.301, y: 0.301, z: 0.640, w: 0.640}')
                            response = subprocess.run(['gz', 'service', '-s', '/world/jetrover_room/set_pose',
                                                       '--reqtype', 'gz.msgs.Pose', '--reptype', 'gz.msgs.Boolean',
                                                       '--timeout', '5000', '--req', pose], env=env, check=True,
                                                      capture_output=True, text=True, timeout=10)
                            if 'data: true' not in response.stdout:
                                raise RuntimeError('fixture pose not confirmed')
                        nav = subprocess.Popen(['ros2', 'launch', 'jetrover_navigation', 'nav2.launch.py', 'use_sim_time:=true', f'params_file:={ROOT}/tools/nav/ab_params/nav2_params_mppi.yaml', 'precise_approach:=false'], cwd=ROOT, env=env, stdout=nav_log, stderr=subprocess.STDOUT, start_new_session=True)
                        wait_localization_ready(nav_path, nav, 90)
                        payload = {'request_id': str(uuid4()), 'mode': 'gazebo',
                                   'kind': 'inspect_stack_light' if inspection else 'navigate_demo', 'parameters': {}}
                        if browser:
                            click_xpath("//button[contains(normalize-space(.), '임무 관리')]")
                            click_xpath("//option[@value='gazebo_inspection']")
                            click_xpath("//button[contains(normalize-space(.), '임무 생성')]")
                            deadline = time.monotonic() + 20
                            while True:
                                matches = [m for m in request('/api/missions')['missions'] if m['kind'] == 'inspect_stack_light']
                                if matches:
                                    mission = matches[0]
                                    break
                                if time.monotonic() > deadline:
                                    raise RuntimeError('browser did not create inspection')
                                time.sleep(.2)
                            click_xpath("//button[contains(normalize-space(.), 'Gazebo 실행')]")
                        else:
                            mission = request('/api/missions', payload)
                        mission_id = mission['id']
                        if not browser:
                            request(f'/api/missions/{mission_id}/start', {})
                        print(f'trial {trial}: mission {mission_id} submitted', flush=True)
                        # The mission sets AMCL's initial pose; the planner can need that transform to activate.
                        # 한글: 임무가 AMCL 초기 자세를 설정하며 플래너 활성화에는 그 TF가 필요할 수 있다.
                        wait_nav_ready(nav_path, nav, 90)
                        until = time.monotonic() + 260
                        last_state = None
                        cancel_submitted = False
                        restart_done = False
                        bridge_stopped = False
                        while time.monotonic() < until:
                            mission = request(f'/api/missions/{mission_id}')
                            if bridge_loss and mission['stage'] == 'gazebo_inspection' and not bridge_stopped:
                                # Stop only the bridge belonging to this test's launch process group.
                                # 한글: 이 시험의 launch 프로세스 그룹에 속한 브리지만 중지한다.
                                probe = subprocess.run(['ros2', 'topic', 'echo', '--once', '--field', 'header',
                                                        '--qos-reliability', 'best_effort', '/depth_cam/color/image_raw',
                                                        'sensor_msgs/msg/Image'],
                                                       env=env, capture_output=True, text=True, timeout=10)
                                if probe.returncode != 0 or 'stamp:' not in probe.stdout:
                                    raise RuntimeError(f'camera probe failed (code {probe.returncode}): '
                                                       f'{probe.stdout[-500:]} {probe.stderr[-500:]}')
                                processes = subprocess.run(['ps', '-eo', 'pid=,pgid=,args='], capture_output=True,
                                                           text=True, check=True).stdout.splitlines()
                                matches = []
                                for entry in processes:
                                    fields = entry.strip().split(None, 2)
                                    if (len(fields) == 3 and int(fields[1]) == gz.pid and
                                            'ros_gz_bridge/parameter_bridge' in fields[2]):
                                        matches.append(int(fields[0]))
                                if len(matches) != 1:
                                    raise RuntimeError(f'expected one test bridge, found {matches}')
                                os.kill(matches[0], signal.SIGTERM)
                                deadline = time.monotonic() + 5
                                while time.monotonic() < deadline:
                                    try:
                                        status = Path(f'/proc/{matches[0]}/status').read_text()
                                    except FileNotFoundError:
                                        break
                                    if '\nState:\tZ' in status:
                                        break
                                    time.sleep(.1)
                                else:
                                    raise RuntimeError('test bridge did not terminate')
                                # Bring the fixture into view only after the camera bridge stops.
                                # 한글: 카메라 브리지가 중지된 뒤에만 시험판을 관측 위치로 이동한다.
                                pose = ('name: "robot_view_stack_light", position: {x: 1.001, y: 1.770, z: 0.158}, '
                                        'orientation: {x: -0.301, y: 0.301, z: 0.640, w: 0.640}')
                                moved = subprocess.run(['gz', 'service', '-s', '/world/jetrover_room/set_pose',
                                                        '--reqtype', 'gz.msgs.Pose', '--reptype', 'gz.msgs.Boolean',
                                                        '--timeout', '5000', '--req', pose], env=env, check=True,
                                                       capture_output=True, text=True, timeout=10)
                                if 'data: true' not in moved.stdout:
                                    raise RuntimeError('fixture was not placed after bridge loss')
                                bridge_stopped = True
                                print('verified camera stream, stopped test bridge during inspection', flush=True)
                            if restart_inspection and mission['stage'] == 'gazebo_inspection' and not restart_done:
                                print('restarting isolated manager during inspection', flush=True)
                                stop(server)
                                server = subprocess.Popen([str(VENV), '-m', 'uvicorn', 'browser_test_server:app', '--host', '127.0.0.1', '--port', '18765'], env=web_env, stdout=server_log, stderr=subprocess.STDOUT, start_new_session=True)
                                deadline = time.monotonic() + 20
                                while True:
                                    try:
                                        mission = request(f'/api/missions/{mission_id}')
                                        break
                                    except (URLError, OSError):
                                        if time.monotonic() > deadline:
                                            raise
                                        time.sleep(.2)
                                restart_done = True
                            if cancel_inspection and mission['stage'] == 'gazebo_inspection' and not cancel_submitted:
                                click_xpath("//button[contains(normalize-space(.), 'Gazebo 취소')]")
                                cancel_submitted = True
                                print('browser requested cancellation during inspection', flush=True)
                            if mission['state'] != last_state:
                                last_state = mission['state']
                                print(f'trial {trial}: {last_state}', flush=True)
                            if mission['state'] in ('succeeded', 'failed', 'canceled', 'interrupted'):
                                events = request(f'/api/missions/{mission_id}/events')['events']
                                results.append({'trial': trial, 'state': mission['state'], 'reason': mission['reason'],
                                                'result': mission['result'], 'events': [entry['state'] for entry in events],
                                                'stages': [entry['stage'] for entry in events]})
                                print('TRIAL_RESULT ' + json.dumps(results[-1]), flush=True)
                                if mission['state'] in ('failed', 'interrupted') and not (bridge_loss or restart_inspection):
                                    child_log = directory / 'child-logs' / f'{mission_id}.log'
                                    if child_log.exists():
                                        print('CHILD_LOG ' + child_log.read_text(errors='replace')[-5000:], flush=True)
                                    else:
                                        print('CHILD_LOG unavailable', flush=True)
                                if bridge_loss and mission['state'] == 'failed':
                                    diagnostic = (mission.get('result') or {}).get('diagnostics')
                                    if not isinstance(diagnostic, dict) or not isinstance(diagnostic.get('received'), int):
                                        raise RuntimeError('inspection failure diagnostics were not persisted')
                                    print('INSPECTION_FAILURE_EVIDENCE ' + json.dumps(diagnostic), flush=True)
                                if inspection and mission['state'] == 'succeeded':
                                    colors = mission['result']['colors']
                                    expected_colors = ['off', 'on', 'off'] if inverted_inspection else ['on', 'off', 'on']
                                    if [colors[name]['state'] for name in ('red', 'yellow', 'green')] != expected_colors:
                                        raise RuntimeError('fixture colors mismatch')
                                if browser and mission['state'] == 'succeeded':
                                    deadline = time.monotonic() + 15
                                    while True:
                                        body = webdriver(session_path + '/execute/sync', {'script': 'return document.body.innerText', 'args': []})
                                        if all(text in body for text in ('가상 경광등 관측 결과', '빨강', '노랑', '초록', '켜짐', '꺼짐')):
                                            break
                                        if time.monotonic() > deadline:
                                            raise RuntimeError('browser did not display inspection colors')
                                        time.sleep(.5)
                                    print('BROWSER_RESULT inspection colors displayed', flush=True)
                                if inspection and mission['state'] not in ('succeeded', 'canceled') and not restart_inspection and not bridge_loss:
                                    pose_result = subprocess.run(['gz', 'topic', '-e', '-t', '/world/jetrover_room/dynamic_pose/info',
                                                                  '--json-output', '-n', '1'], env=env, capture_output=True,
                                                                 text=True, timeout=15)
                                    if pose_result.returncode == 0:
                                        pose_data = json.loads(pose_result.stdout)
                                        print('ROBOT_POSE ' + json.dumps(next((p for p in pose_data['pose'] if p.get('name') == 'jetrover'), None)), flush=True)
                                    diagnostic = subprocess.run(['/usr/bin/python3', str(ROOT / 'tools/mission/check_stack_robot_view.py')],
                                                                env=env, capture_output=True, text=True, timeout=55)
                                    print('CAMERA_DIAGNOSTIC ' + diagnostic.stdout + diagnostic.stderr, flush=True)
                                if mission['state'] in ('failed', 'interrupted') and not restart_inspection and not bridge_loss:
                                    raise RuntimeError(f'Gazebo mission failed: {mission["reason"]}')
                                break
                            time.sleep(2)
                        else:
                            request(f'/api/missions/{mission_id}/cancel', {})
                            raise RuntimeError('dashboard trial timed out; cancellation requested')
                    except Exception as exc:
                        # Retain state before teardown; intermittent lifecycle faults otherwise lose their logs.
                        # 한글: 간헐적인 라이프사이클 오류 증거가 지워지지 않도록 종료 전에 보존한다.
                        evidence = Path(tempfile.mkdtemp(prefix='jetinspect-mission-failure-', dir='/tmp'))
                        gz_log.flush()
                        nav_log.flush()
                        for path in (gz_path, nav_path):
                            if path.exists():
                                shutil.copy2(path, evidence / path.name)
                        child_logs = directory / 'child-logs'
                        if child_logs.exists():
                            shutil.copytree(child_logs, evidence / 'child-logs')
                        server_log.flush()
                        shutil.copy2(directory / 'server.log', evidence / 'server.log')
                        (evidence / 'error.txt').write_text(repr(exc))
                        commands = {
                            'nodes': ['ros2', 'node', 'list', '--no-daemon', '--spin-time', '2'],
                            'amcl': ['ros2', 'lifecycle', 'get', '/amcl'],
                            'map_server': ['ros2', 'lifecycle', 'get', '/map_server'],
                            'smoother': ['ros2', 'lifecycle', 'get', '/smoother_server'],
                            'processes': ['ps', '-eo', 'pid,ppid,pgid,args'],
                        }
                        for name, command in commands.items():
                            try:
                                output = subprocess.run(command, env=env, capture_output=True, text=True, timeout=8)
                                (evidence / f'{name}.txt').write_text(output.stdout + '\nSTDERR:\n' + output.stderr)
                            except (OSError, subprocess.SubprocessError) as error:
                                (evidence / f'{name}.txt').write_text(repr(error))
                        print(f'failure evidence: {evidence}', flush=True)
                        raise
                    finally:
                        stop(nav)
                        stop(gz)
            print('ALL_RESULTS ' + json.dumps(results), flush=True)
            expected_count = trial_count
            expected_reason = 'inspection_unconfirmed' if bridge_loss else ('manager_restarted' if restart_inspection else ('inspection_canceled' if cancel_inspection else ('inspection_observed' if inspection else 'nav2_succeeded')))
            expected_state = 'failed' if bridge_loss else ('interrupted' if restart_inspection else ('canceled' if cancel_inspection else 'succeeded'))
            expected_events = (['created', 'queued', 'running', 'running', 'cancel_requested', 'canceled'] if cancel_inspection else
                               ['created', 'queued', 'running', 'running', 'interrupted'] if restart_inspection else
                               ['created', 'queued', 'running', 'running', 'failed'] if bridge_loss else
                               ['created', 'queued', 'running', 'running', 'succeeded'] if inspection else
                               ['created', 'queued', 'running', 'succeeded'])
            if len(results) != expected_count or (bridge_loss and not bridge_stopped) or any(item['state'] != expected_state or item['reason'] != expected_reason or item['events'] != expected_events or (inspection and 'gazebo_inspection' not in item['stages']) for item in results):
                raise RuntimeError('one or more dashboard-to-Gazebo trials failed')
        finally:
            if session:
                try:
                    req = Request('http://127.0.0.1:18444/session/' + session, method='DELETE')
                    urlopen(req, timeout=5).close()
                except (OSError, URLError):
                    pass
            if driver:
                driver.terminate()
                try:
                    driver.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    driver.kill()
                    driver.wait()
            stop(server)
            server_log.close()


if __name__ == '__main__':
    main()
