"""Exercise voice UI with text and fake microphone in an isolated browser.

한글: 격리 브라우저에서 텍스트와 가짜 마이크로 음성 UI를 시험한다.
"""
import os
from pathlib import Path
import subprocess
import tempfile

from test_mission_browser import ROOT, PYTHON, call, wait_for


def main():
    """Confirm simulated start/cancel and forbid physical actions. / 모의 시작·취소 확인과 실기 거부를 검증한다."""
    with tempfile.TemporaryDirectory(dir='/tmp') as tmp:
        env = os.environ.copy(); env['MISSION_BROWSER_TEST_DB'] = str(Path(tmp) / 'missions.db')
        env['PYTHONPATH'] = str(ROOT / 'backend') + ':' + str(ROOT)
        server = subprocess.Popen([str(PYTHON), '-m', 'uvicorn', 'browser_test_server:app', '--host', '127.0.0.1', '--port', '18765'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        driver = subprocess.Popen(['geckodriver', '--host', '127.0.0.1', '--port', '18444'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        session = None
        try:
            wait_for(lambda: call('http://127.0.0.1:18765/api/missions'))
            wait_for(lambda: call('http://127.0.0.1:18444/status')['value']['ready'])
            caps = {'browserName':'firefox', 'moz:firefoxOptions':{'args':['-headless'], 'prefs':{'media.navigator.streams.fake':True, 'media.navigator.permission.disabled':True}}}
            session = call('http://127.0.0.1:18444/session','POST',{'capabilities':{'alwaysMatch':caps}})['value']['sessionId']
            base = f'http://127.0.0.1:18444/session/{session}'
            call(base+'/url','POST',{'url':'http://127.0.0.1:18765/'})
            def element(selector): return call(base+'/element','POST',{'using':'xpath','value':selector})['value']['element-6066-11e4-a52e-4f735466cecf']
            def click(label):
                el = wait_for(lambda:element(f"//button[normalize-space(.)='{label}']"));call(base+'/element/'+el+'/click','POST',{})
            def content(): return call(base+'/execute/sync','POST',{'script':'return document.body.innerText','args':[]})['value']
            def say(text):
                el = element("//input[@id='voice-text']");call(base+'/element/'+el+'/clear','POST',{});call(base+'/element/'+el+'/value','POST',{'text':text});click('문장 해석')
            nav = wait_for(lambda: element("//button[contains(normalize-space(.), '음성 관제')]"));call(base+'/element/'+nav+'/click','POST',{})
            say('로버 배터리 상태 알려줘');wait_for(lambda:'12.30 볼트' in content())
            say('로버 카메라 연결 방법 알려줘');wait_for(lambda:'시험 문서 원문입니다' in content())
            say('로버 모의 점검 시작해')
            wait_for(lambda:'확인 필요' in content())
            assert call('http://127.0.0.1:18765/api/missions')['missions'] == []
            click('확인')
            wait_for(lambda:'모의 점검을 시작했습니다' in content())
            missions = call('http://127.0.0.1:18765/api/missions')['missions'];assert len(missions)==1 and missions[0]['mode']=='simulation'
            say('로버 모의 임무 취소해');wait_for(lambda:'확인 필요' in content());click('확인')
            wait_for(lambda:'취소' in content())
            say('로버 전진해');wait_for(lambda:'지원하지 않는 요청' in content())
            assert len(call('http://127.0.0.1:18765/api/missions')['missions'])==1
            click('마이크 켜기');wait_for(lambda:'마이크 끄기' in content());click('마이크 끄기');wait_for(lambda:'마이크 켜기' in content())
            print('Firefox: confirmation, simulation-only start/cancel, unsupported action, fake microphone on/off passed')
        finally:
            if session:
                try: call(f'http://127.0.0.1:18444/session/{session}','DELETE')
                except Exception: pass
            for process in (driver,server):
                process.terminate()
                try: process.wait(timeout=8)
                except subprocess.TimeoutExpired: process.kill();process.wait()


if __name__ == '__main__': main()
