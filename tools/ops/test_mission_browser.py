"""Exercise mock missions in Firefox against a disposable local DB.

한글: 임시 로컬 DB를 사용하는 Firefox 모의 임무 상호작용 시험이다.
"""
import json
import os
import sqlite3
from pathlib import Path
import subprocess
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
PYTHON = Path.home() / '.local/share/jetinspect-ops/venv/bin/python'


def call(url, method='GET', payload=None):
    """Call a local HTTP endpoint. / 로컬 HTTP 엔드포인트를 호출한다."""
    data = None if payload is None else json.dumps(payload).encode()
    request = Request(url, data=data, method=method, headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=35) as response:
        return json.load(response)


def wait_for(action, seconds=15):
    """Wait for a bounded condition. / 제한 시간 안에 조건을 기다린다."""
    deadline = time.monotonic() + seconds
    last = None
    while time.monotonic() < deadline:
        try:
            value = action()
            if value:
                return value
        except (HTTPError, URLError, OSError, KeyError) as exc:
            last = exc
        time.sleep(.2)
    raise RuntimeError(f'timed out waiting for condition: {last}')


def main():
    """Run the isolated interaction test. / 격리 화면 상호작용 시험을 실행한다."""
    with tempfile.TemporaryDirectory(dir='/tmp') as tmp:
        env = os.environ.copy()
        env['MISSION_BROWSER_TEST_DB'] = str(Path(tmp) / 'missions.db')
        env['PYTHONPATH'] = str(ROOT / 'backend') + ':' + str(ROOT)
        server = subprocess.Popen([str(PYTHON), '-m', 'uvicorn', 'browser_test_server:app', '--host', '127.0.0.1', '--port', '18765'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        driver = subprocess.Popen(['geckodriver', '--host', '127.0.0.1', '--port', '18444'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        session = None
        upload_tmp = None
        try:
            wait_for(lambda: call('http://127.0.0.1:18765/api/missions'))
            wait_for(lambda: call('http://127.0.0.1:18444/status')['value']['ready'])
            session = call('http://127.0.0.1:18444/session', 'POST', {'capabilities': {'alwaysMatch': {'browserName': 'firefox', 'moz:firefoxOptions': {'args': ['-headless']}}}})['value']['sessionId']
            base = f'http://127.0.0.1:18444/session/{session}'
            call(base + '/url', 'POST', {'url': 'http://127.0.0.1:18765/'})
            def element(selector):
                return call(base + '/element', 'POST', {'using': 'xpath', 'value': selector})['value']['element-6066-11e4-a52e-4f735466cecf']
            def click(text):
                found = wait_for(lambda: element(f"//button[contains(normalize-space(.), '{text}')]"))
                call(base + '/element/' + found + '/click', 'POST', {})
            def content():
                return call(base + '/execute/sync', 'POST', {'script': 'return document.body.innerText', 'args': []})['value']
            click('임무 관리')
            click('임무 생성')
            wait_for(lambda: '생성됨' in content())
            click('모의 실행')
            wait_for(lambda: '모의 성공' in content(), 15)
            assert '상태 이력' in content()
            click('임무 생성')
            second = wait_for(lambda: (items[0] if len(items := call('http://127.0.0.1:18765/api/missions')['missions']) == 2 else None))
            wait_for(lambda: second['id'] in content())
            click('모의 취소')
            wait_for(lambda: '취소 완료' in content())
            gazebo_option = wait_for(lambda: element("//option[@value='gazebo']"))
            call(base + '/element/' + gazebo_option + '/click', 'POST', {})
            click('임무 생성')
            wait_for(lambda: 'Gazebo 실행' in content())
            assert 'GAZEBO' in content()
            inspection_option = wait_for(lambda: element("//option[@value='gazebo_inspection']"))
            call(base + '/element/' + inspection_option + '/click', 'POST', {})
            click('임무 생성')
            wait_for(lambda: '확인된 점검 결과가 없습니다.' in content())
            missions = call('http://127.0.0.1:18765/api/missions')['missions']
            inspection = next(item for item in missions if item['kind'] == 'inspect_stack_light')
            colors = {name: {'state': state, 'reason': None, 'samples': 5, 'duration_s': 2.2}
                      for name, state in [('red', 'on'), ('yellow', 'off'), ('green', 'blinking')]}
            # Populate only the disposable browser DB; no Gazebo or physical robot is started.
            # 한글: 브라우저 전용 임시 DB에만 결과를 넣으며 Gazebo와 실기 로봇은 실행하지 않는다.
            with sqlite3.connect(Path(tmp) / 'missions.db') as db:
                db.execute("UPDATE missions SET state='running', stage='gazebo_inspection' WHERE id=?", (inspection['id'],))
            wait_for(lambda: '현재 단계\n경광등 점검' in content())
            with sqlite3.connect(Path(tmp) / 'missions.db') as db:
                db.execute("UPDATE missions SET state='succeeded', reason='inspection_observed', result=? WHERE id=?",
                           (json.dumps({'source': 'gazebo', 'simulated': True, 'colors': colors}), inspection['id']))
            text = wait_for(lambda: (body if all(value in (body := content()) for value in ('관측 완료', '빨강', '노랑', '초록', '켜짐', '꺼짐', '깜빡임')) else None))
            assert '가상 경광등 관측 결과' in text
            diagnostics = {'received': 8, 'window_frames': 3, 'invalid_time': 2,
                           'gap_resets': 1, 'invalid_format': 0,
                           'color_reasons': {'red': 'fixture_not_found'}}
            with sqlite3.connect(Path(tmp) / 'missions.db') as db:
                db.execute("UPDATE missions SET state='failed', reason='inspection_unconfirmed', result=? WHERE id=?",
                           (json.dumps({'source': 'gazebo', 'simulated': True,
                                        'diagnostics': diagnostics}), inspection['id']))
            wait_for(lambda: (body if all(value in (body := content()) for value in
                                        ('관측 진단', '수신 영상 8개', '시각 오류 2개', '시험판의 위치')) else None))
            # Upload only a generated synthetic clip to the disposable server.
            # 한글: 격리 서버에 합성 영상만 업로드한다.
            # Firefox snap has a private /tmp; use a temporary visible home directory.
            # 한글: Firefox snap은 /tmp가 격리되므로 홈의 임시 폴더를 사용한다.
            upload_tmp = tempfile.TemporaryDirectory(prefix='jetinspect-browser-', dir=Path.home() / 'Documents')
            video = Path(upload_tmp.name) / 'lights.avi'
            code = ("import cv2,numpy as np,sys; "
                    "w=cv2.VideoWriter(sys.argv[1],cv2.VideoWriter_fourcc(*'MJPG'),10,(48,16)); "
                    "h=np.zeros((16,48,3),np.uint8); "
                    "h[:,:16]=(0,255,220); h[:,16:32]=(27,255,40); h[:,32:]=(60,255,220); "
                    "b=cv2.cvtColor(h,cv2.COLOR_HSV2BGR); "
                    "[w.write(b) for _ in range(40)]; w.release()")
            subprocess.run(['/usr/bin/python3', '-c', code, str(video)], check=True, timeout=10)
            video_input = wait_for(lambda: element("//input[@id='inspection-video']"))
            try:
                call(base + '/element/' + video_input + '/value', 'POST', {'text': str(video)})
            except HTTPError as exc:
                raise RuntimeError('Firefox file input failed: ' + exc.read().decode(errors='replace')) from exc
            for label, value in [('빨강', '0,0,16,16'), ('노랑', '16,0,16,16'), ('초록', '32,0,16,16')]:
                field = element(f"//input[@aria-label='{label} 영역']")
                call(base + '/element/' + field + '/value', 'POST', {'text': value})
            click('영상 검토')
            wait_for(lambda: (body if all(value in (body := content()) for value in
                                        ('실제 성능 미검증', '빨강: 켜짐', '노랑: 꺼짐', '초록: 켜짐')) else None), 40)
            assert element("//img[@alt='첫 관측 표본과 판정 영역']")
            print('Firefox: mock lifecycle, inspection diagnostics and synthetic video review passed')
        finally:
            if upload_tmp:
                upload_tmp.cleanup()
            if session:
                try:
                    call(f'http://127.0.0.1:18444/session/{session}', 'DELETE')
                except Exception:
                    pass
            for process in (driver, server):
                process.terminate()
            for process in (driver, server):
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == '__main__':
    main()
