# TEST PLAN: Navigation BT (정밀 도착 BT, `prd/navigation-bt.md`)

- 작성 2026-10-28. 신뢰 수준: 계획. 체크리스트 9번.

| parent task | 레벨 | 통과 기준 |
|---|---|---|
| 9.1 `PreciseApproach` BT 노드 | L0 | `colcon build`/`colcon test`(jetrover_nav_plugins) 통과, gtest: 포트 읽기·목표 전달, 서버 없음/거부/중단 시 FAILURE |
| 9.2 `navigate_to_pose_precise.xml` | L0 + L5(sim) | XML이 bt_navigator에 로드됨(오류 로그 없음). 정밀 접근 실패를 흉내 냈을 때 Nav2+정밀 접근을 정확히 1번 더 하고 실패로 끝남 |
| 9.3 launch 통합 | L5(sim) | `nav2.launch.py` 하나로 정밀 접근 노드까지 뜸, 기본 BT 목표는 지금과 같은 동작(회귀 없음) |
| 9.4 실패 이유 보고 | L0 + L5(sim) | 막힘/시작 거리 초과/시간 초과가 결과 `error_code`(또는 메시지)로 구분됨 |
| 9.5 sim 검증 | L5 sim | 정밀 BT로 직선·S2·S4·D 시나리오 각 10회: 한 번의 요청으로 정답 위치 오차 ≤ 3 cm, 간격·시간·접촉 기준 회귀 없음 |
| 9.6 실기 검증 | L5 실기 | 직선 3회·상자 우회 3회 줄자 오차 ≤ 3 cm, 접촉 0 (사용자 입회) |
| 9.7 목표 허용 오차 재검토 | L5 | 넓혔을 때 시간·정확도 비교 표, 바꾸면 tuning-history 기록 |
