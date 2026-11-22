# 065 Jetson의 Gazebo 임무가 시간 초과·START_OCCUPIED로 실패

상태: 우회 적용 (2026-11-22). 근본 해결(호스트 PC에서 Gazebo 실행)은 미적용.

## 증상
음성 출발점 복귀(Gazebo `return_to_start`) 시험 3회 중 2회 실패.
- 일시정지 → 재개 뒤 같은 구간이 180초(벽시계) 안에 끝나지 않아 `timeout_cancel_confirmed`. STT 서버를 꺼도 재현.
- 일시정지 없는 대조 1회는 목표 전송 직후 `ABORTED error_code=205`(ComputePathToPose `START_OCCUPIED`).
- 주행 중 collision_monitor가 "depth_cloud 시각 차 1초 초과, invalid source로 정지"를 반복.

## 원인
Jetson에서 Gazebo+Nav2+센서 서비스+대시보드+MySQL+STT 서버가 함께 돌아 load average 약 16(6코어), 메모리 거의 소진, 스왑 1.9GB. 성공 회차에서 시뮬 시간 25초·36초인 구간이 벽시계 약 124초·186초 걸려 **Gazebo가 실시간의 약 1/5로 동작**했다. 벽시계 180초 제한(기존 단일 구간 125~131초, 2026-11-16 기록)과 늦게 도착하는 depth 점 때문에 진행 중인 주행이 실패했다. START_OCCUPIED는 시작 직후 비용지도 정리 전의 경쟁으로 보이며 원인 확정은 아니다.

## 조치
- `gazebo_nav_trial.py` 구간 제한을 **시뮬레이션 시간 180초**로 변경, 벽시계 600초 안전 상한.
- 목표 전송 5초(시뮬) 안의 START_OCCUPIED는 3초 뒤 한 번 재전송.
- 결과: 같은 시험(일시정지 8초 → 재개 → 두 구간) `succeeded / returned_to_start`, 벽시계 355초.

## 남은 것
대시보드 Gazebo 임무가 5~6분 걸린다. AGENTS.md의 원래 계획대로 Gazebo를 호스트 PC에서 돌리거나 Jetson 동시 실행 서비스를 줄여야 실사용 속도가 나온다. 반복 횟수 1회라 안정성 판단에 충분하지 않다.
