# TEST_PLAN: 음성 → 실제 임무 연결

작성 2026-11-22. PRD `prd/voice-mission-control.md`.

| 단계 | 레벨 | 시험 | 통과 기준 |
|---|---|---|---|
| V1 의도 | L0 | "출발점으로 돌아와"·"멈춰"·"정지"·"취소"·"계속해"·"종료"·"실제 로봇 출발점 복귀" 분류 | 각각 return_home·pause·pause·dismiss·resume·end·unsupported |
| V1 동작 규칙 | L0 | 가짜 임무 저장소·작업자로 복귀 확인 전 미실행, 주행 중 정지 즉시 전달, 대기 요청만 있을 때 "취소"는 대기 취소, 재개·종료, 전달 실패 안내 | `test_robot_voice.py MotionTests` 통과 |
| V1 API | L0 | 주행 단계에서만 pause, 일시정지 단계에서만 resume, 작업자 없음 503, 조회자 403 | `test_mission_routes.py`, 접근 제어 미들웨어 |
| V1 작업자 | L0 | 단계 기록(주행→일시정지→주행→복귀), 실행 중 자식에 명령 전달, 다른 임무 거부 | `test_gazebo_worker.py` |
| V1 Gazebo | L1(시뮬) | 격리 Gazebo에서 return_to_start 실행 중 pause → 정지 확인 → resume → 두 구간 완료 | 결과 `succeeded/returned_to_start`, 일시정지 중 새 목표 없음 |
| V1 음성 종단 | L2 | 실제 마이크로 "출발점으로 돌아와" → 확인 → "멈춰" → "계속해" → 완료/"종료" (Gazebo) | 각 단계 응답과 임무 단계 일치, 실제 로봇 구동 없음 |
| V2 게이트 | L0 | 각 게이트 미충족 시 실행 0회 | 게이트별 거부 시험 |
| V2 실기 | L4 | 061 해결·별도 승인 후. 저속, 사용자 전원 스위치 곁 | 별도 실기 절차서 |
