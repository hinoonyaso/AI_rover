# 대시보드 임무 → Gazebo 주행 반복 시험 (2026-11-16)

신뢰 수준: 격리 시뮬레이션 실측. 실제 로봇, Stack Light 점검 및 전체 임무 시험이 아니다.

## 조건
- 도메인 31, `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`, Fast DDS, `GZ_IP=127.0.0.1`, 시험별 고유 실행의 Gazebo partition. 외부 discovery peers 및 DDS 프로필 환경 변수 제거.
- 각 회차마다 Gazebo와 Nav2를 종료하고 Gazebo를 새로운 시작점 `(1.02, 0.37, 1.45 rad)`에서 재기동했다. 두 번째 시작 시 Gazebo 활성 프로세스가 하나뿐임을 확인했다. Gazebo `gui:=false depth_obstacles:=true`, Nav2 `use_sim_time:=true`, MPPI 설정, 정밀 접근 비활성. 시작 자세와 GazeboSimSystem·clock을 검증했다.
- 별도 localhost 시험 API와 임시 SQLite에 `gazebo` / `navigate_demo` 임무를 생성·시작했다. 관리자 → 독립 실행기 → Gazebo Nav2 → 임무 상태 및 이력을 통해 결과를 확인했다. 목표는 `map` 기준 `(1.00, 1.45, 1.571 rad)`이며 Action 처리 제한은 180초(준비 단계 제외)다.

## 결과

| 회차 | 임무 상태 이력 | 결과 | 시작~결과 기록 벽시계 |
|---|---|---|---|
| 1 | created → queued → running → succeeded | Nav2 성공 | 약 131초 |
| 2 | created → queued → running → succeeded | Nav2 성공 | 약 125초 |

별도로 시작한 초기 시험에서는 Gazebo가 종료 후 남아 있는 것이 발견됐다. 두 번째 시험이 기존 인스턴스에 연결됐을 가능성을 배제할 수 없어 해당 결과는 반복 성능 근거에서 제외했다. 시험 프로세스 그룹 종료를 보강하고 격리 Gazebo partition을 사용한 뒤 위 두 회차를 다시 수행했다. 두 회차 후 Gazebo·Nav2 시험 프로세스가 남지 않은 것을 확인했다.

상태 전이·중복·Gazebo/모의 구분·실제 로봇 모드 거부·결과 기록 장애 복구 등 관련 자동 테스트 30건, 시작 자세 가드 2건을 통과했다. Firefox에서는 모의 임무 생성·실행·취소와 Gazebo 임무 선택을 확인했다. 실제 Gazebo 실행의 브라우저 클릭은 시험하지 않았고, 격리 API에서 실행했다. Nav2 최종 위치 ground truth 오차와 더 많은 반복 횟수는 아직 측정하지 않았다. 실행 중인 Gazebo 목표 취소의 실제 통합 시험도 남아 있다.

최종 결과 보존 로직을 두 회차 이후 보강했으며, 일시적 저장 장애 시 결과 유지·복구는 별도 단위 테스트로 확인했다. 2/2 결과는 장기적인 안정성이나 실제 로봇의 안전·성능을 보증하지 않는다.
