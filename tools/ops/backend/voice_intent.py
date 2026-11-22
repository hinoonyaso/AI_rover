"""Classify a narrow, non-actuating set of voice commands.

한글: 실제 구동 명령을 포함하지 않는 제한된 음성 요청만 분류한다.
"""
import re

# STT may insert a space inside the compound name ("제트 로버").
# 한글: STT가 복합 호출어 사이에 띄어쓰기를 넣을 수 있다("제트 로버").
WAKE = re.compile(r'^\s*(?:제트\s*인스펙트|제트\s*로버|로버야|로버)(?:[\s,.!?]+|$)', re.IGNORECASE)


def interpret(transcript):
    """Require a wake prefix and return a deterministic intent. / 호출어와 제한된 의도만 인정한다."""
    if not isinstance(transcript, str) or len(transcript) > 300:
        raise ValueError('invalid_transcript')
    match = WAKE.match(transcript)
    if not match:
        return {'intent': 'sleep', 'command': ''}
    raw_command = transcript[match.end():].strip()
    question = raw_command.endswith('?')
    text = raw_command.strip(' .,!?')
    compact = re.sub(r'\s+', '', text.lower())
    if not text:
        return {'intent': 'wake', 'command': text}
    if compact in ('확인', '네', '예', '진행', '실행해', '맞아'):
        return {'intent': 'confirm', 'command': text}
    if compact in ('아니', '아니요', '취소', '취소해', '안해', '그만'):
        return {'intent': 'dismiss', 'command': text}
    # Never turn an ambiguous real-world motion request into a simulated one.
    # 한글: 실기 이동·팔 동작이 섞인 요청은 모의 요청으로 바꾸지 않는다.
    if any(word in compact for word in ('실제', '실기', 'gazebo', '가제보', '주행', '전진', '후진', '로봇팔', '그리퍼', '바퀴', '모터', '운전')):
        return {'intent': 'unsupported', 'command': text}
    simulated = any(word in compact for word in ('모의', '시뮬레이션'))
    if simulated and any(word in compact for word in ('취소', '중단')):
        return {'intent': 'simulation_cancel', 'command': text}
    if simulated and any(word in compact for word in ('점검', '임무')) and any(word in compact for word in ('시작', '실행', '생성')):
        return {'intent': 'simulation_start', 'command': text}
    if (simulated or '임무' in compact) and any(word in compact for word in ('상태', '진행', '결과')):
        return {'intent': 'mission_status', 'command': text}
    if any(word in compact for word in ('문서', '방법', '원인', '어떻게', '설명')):
        return {'intent': 'knowledge', 'command': text}
    if any(word in compact for word in ('배터리', '전압', '센서', '라이다', 'lidar', '카메라', 'imu')) and any(word in compact for word in ('상태', '얼마', '몇', '수신', '연결', '알려')):
        return {'intent': 'status', 'command': text}
    if any(word in compact for word in ('어떻게', '무엇', '뭐야', '뭐냐', '왜', '알려', '설명', '방법', '원인')) or question:
        return {'intent': 'knowledge', 'command': text}
    return {'intent': 'unsupported', 'command': text}
