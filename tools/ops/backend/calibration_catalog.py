"""Describe available and planned calibration workflows.

한글: 구현된 보정과 계획된 작업의 범위를 설명한다.
"""

CATALOG = (
    ('imu', 'IMU 자이로·가속도', '자동·반자동', 'candidate', '정지 자이로와 여섯 자세 가속도 후보'),
    ('wheel', '메카넘 휠 방향·속도', '수동 기록', 'record', '방향 수동 관찰 및 실제 포트 피드백과 기준 속도 비교'),
    ('odometry', '오도메트리 거리·회전', '반자동', 'comparison', '실측·ROS 기록 비교 및 명령 적분 배율 후보'),
    ('lidar', 'LiDAR 위치·각도', '반자동', 'candidate', '수동 장착 위치 및 스캔·TF 기반 방향 관찰'),
    ('camera', 'RGB 카메라 내부 파라미터', '검증·반자동', 'candidate', '컬러 체커보드 후보; MJPG 수신 후 PNG 촬영, 독립 검증 필요'),
    ('rgb_depth', 'RGB·깊이 정합', '검증·반자동', 'comparison', '현재 카메라 정보에 근거한 수동 대응점 오차 비교'),
    ('arm', '로봇팔 관절 영점·오프셋', '반자동', 'comparison', '서보 진단과 기준 각도 비교 및 오프셋 후보'),
    ('gripper', '그리퍼 개폐·파지', '반자동', 'candidate', '기준 각도 비교와 개폐 폭 2점 후보; 파지 구동 미지원'),
    ('tcp', '카메라–팔 외부 파라미터·TCP', '반자동', 'candidate', '고정 자세 대응점 및 다중 자세 핸드아이·TCP 후보'),
    ('footprint', '로봇 외형 크기', '실측 입력', 'candidate', '기준점에서 네 방향 실측으로 외형 후보 생성'),
    ('battery', '배터리 전압', '외부 측정값 입력', 'candidate', '최신 전압 비교 및 다점 선형 후보; 안전 기준 미변경'),
)


def calibration_catalog():
    """Return fresh catalog records; planned is not an implemented measurement.

    한글: 새 목록을 반환하며 계획 항목을 구현된 측정으로 표시하지 않는다.
    """
    return [{'id': key, 'name': name, 'method': method, 'availability': availability, 'description': description}
            for key, name, method, availability, description in CATALOG]
