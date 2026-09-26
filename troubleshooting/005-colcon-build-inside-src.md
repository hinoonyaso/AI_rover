# `~/jetrover_ws/src/` 안에 build/install/log가 생김
- 날짜: 2026-09-20
- 상태: 미정리 (삭제 대기)
- 관련: `~/jetrover_ws/src/build`, `src/install`, `src/log`

## 증상
`ros2 run` 실행 중인 바이너리 경로가 `~/jetrover_ws/src/install/...`로 나왔다. 워크스페이스 루트의 `install/`과 다른 복사본이다.

## 원인
`~/jetrover_ws/src`에서 `colcon build`를 실행했다. colcon은 현재 위치를 워크스페이스 루트로 삼는다.

## 해결 또는 우회
- 항상 `cd ~/jetrover_ws && colcon build --packages-select <pkg>`로 빌드한다.
- `src/build`, `src/install`, `src/log`는 사람이 확인한 뒤 삭제한다 (`src/build`에는 `COLCON_IGNORE`가 들어 있다).
  소스가 아닌 폴더라서 삭제해도 소스는 안 지워진다. 삭제 전에 확인한다.

## 확인/재발 방지
`which`/`pgrep -ax`로 실행 중인 바이너리 경로가 `~/jetrover_ws/install/`인지 본다.
