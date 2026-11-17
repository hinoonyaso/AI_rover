# GitHub Actions 정적 검사 및 ROS 서식 실패

- 일시: 2026-11-18
- 증상: push 후 `static-checks`와 `ros2-jazzy`가 실패했다. `firmware-host-tests`는 통과했다.
- 원인: `tools/sim/corridor_width.py`의 f-string 안에 Python 숫자 범위가 아닌 `0.89..1.11`을 넣어 구문 분석에 실패했다. 또한 센서 보정 관련 C++ 파일 3개가 `ament_uncrustify` 서식 검사에 실패했다. ROS 빌드 자체는 통과했다.
- 수정: 상자 y 범위를 S2 시나리오 중심과 상자 크기에서 계산하고, C++ 파일에 ROS 서식을 적용했다.
- 확인: Python 전체 정적 검사 및 해당 세 파일의 `ament_uncrustify` 통과, 로컬 `jetrover_base` 기존 테스트 구성 15개 통과, 정적 단계 이후 8개 Python 시험 명령 통과. 로컬 기존 빌드 구성에는 새 가속도 gtest가 아직 반영되지 않았다. GitHub Actions 재실행 결과는 별도 확인한다.
