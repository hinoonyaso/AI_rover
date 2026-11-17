"""Exercise automatic simulation startup through an isolated dashboard API.

한글: 격리 대시보드 API에서 시뮬레이션 자동 시작을 검증한다.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from uuid import uuid4

from test_dashboard_gazebo import ROOT, VENV, request, stop


def main():
    """Run one inspection without prestarting Gazebo. / Gazebo 선행 기동 없이 점검을 한 번 실행한다."""
    if sys.argv[1:] not in ([], ['--cancel-preparing'], ['--cancel-navigation']):
        raise ValueError('unsupported test option')
    cancel_stage = {'--cancel-preparing': 'gazebo_preparing', '--cancel-navigation': 'gazebo_navigation'}.get(sys.argv[1] if sys.argv[1:] else '')
    with tempfile.TemporaryDirectory(prefix='auto-gazebo-test-', dir='/tmp') as folder:
        directory = Path(folder)
        env = os.environ.copy()
        for key in ('JETINSPECT_LAN_IP', 'JETINSPECT_LAN_CIDR', 'ROS_STATIC_PEERS', 'ROS_DISCOVERY_SERVER',
                    'FASTRTPS_DEFAULT_PROFILES_FILE', 'FASTDDS_DEFAULT_PROFILES_FILE', 'CYCLONEDDS_URI'):
            env.pop(key, None)
        env.update({'PYTHONPATH': str(ROOT / 'tools/ops/backend') + ':' + str(ROOT / 'tools/ops'),
                    'MISSION_BROWSER_TEST_DB': str(directory / 'missions.sqlite3'),
                    'MISSION_TEST_CHILD_LOG_DIR': str(directory / 'child-logs'),
                    'MISSION_TEST_AUTO_GAZEBO': '1'})
        server_log = (directory / 'server.log').open('w+')
        server = subprocess.Popen([str(VENV), '-m', 'uvicorn', 'browser_test_server:app', '--host', '127.0.0.1', '--port', '18765'],
                                  env=env, stdout=server_log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            deadline = time.monotonic() + 20
            while True:
                try:
                    request('/api/missions')
                    break
                except (OSError, URLError):
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(.5)
            mission = request('/api/missions', {'request_id': str(uuid4()), 'mode': 'gazebo',
                                                'kind': 'inspect_stack_light', 'parameters': {}})
            mission_id = mission['id']
            request(f'/api/missions/{mission_id}/start', {})
            deadline = time.monotonic() + 420
            last = None
            cancel_sent = False
            while time.monotonic() < deadline:
                mission = request(f'/api/missions/{mission_id}')
                pair = mission['state'], mission['stage']
                if pair != last:
                    print('STATE', pair, flush=True)
                    last = pair
                if cancel_stage and mission['state'] == 'running' and mission['stage'] == cancel_stage and not cancel_sent:
                    request(f'/api/missions/{mission_id}/cancel', {})
                    cancel_sent = True
                    print('CANCEL requested during', cancel_stage, flush=True)
                if mission['state'] in ('succeeded', 'failed', 'interrupted', 'canceled'):
                    events = request(f'/api/missions/{mission_id}/events')['events']
                    print('RESULT', json.dumps(mission), flush=True)
                    print('STAGES', [event['stage'] for event in events], flush=True)
                    log = directory / 'child-logs' / f'{mission_id}.log'
                    if log.exists():
                        print('CHILD_LOG', log.read_text(errors='replace')[-5000:], flush=True)
                    if cancel_stage:
                        if not cancel_sent or mission['state'] != 'canceled':
                            raise RuntimeError('preparation cancellation not confirmed')
                        return
                    if (mission['state'] != 'succeeded' or mission['reason'] != 'inspection_observed' or
                            'gazebo_preparing' not in [event['stage'] for event in events] or
                            'gazebo_inspection' not in [event['stage'] for event in events]):
                        raise RuntimeError('automatic Gazebo inspection did not succeed')
                    return
                time.sleep(2)
            raise RuntimeError('automatic Gazebo inspection timed out')
        finally:
            stop(server)
            server_log.close()


if __name__ == '__main__':
    main()
