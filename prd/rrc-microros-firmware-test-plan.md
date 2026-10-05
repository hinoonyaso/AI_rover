# TEST_PLAN: RRC 보드 자체 펌웨어 + micro-ROS

| Parent Task | 필요 레벨 | 통과 기준 |
|---|---|---|
| 1. 핀맵 확정(문서+바이너리 교차) | L0 | `PINMAP.md`의 모든 핀에 확정/추정/미확인 표시, 문서와 바이너리가 충돌하면 충돌 기록 |
| 2. core 로직(PID/엔코더/메카넘/안전/버튼/서보 램프/SBUS/버스서보/게임패드 파서) | L0 | 호스트 `ctest` 전부 통과. PID는 Hiwonder 문서 수식과 수치 동일, 메카넘은 `jetrover_base`의 호스트측 역기구학과 동일 출력 |
| 3. HAL 드라이버 + FreeRTOS 앱 | L0 | arm-none-eabi 빌드 성공(경고 0 목표), `size`로 flash/RAM 사용량 기록, RRC 모드 .bin 생성 |
| 4. 통신 추상화 + RRC 경로 | L0/L1 | 기존 골든 벡터(PDF 예제 + 실기 캡처) 통과, `robot_set_*` 경유, 명령 timeout 시험 |
| 5. micro-ROS 경로 | L0/L1 | static lib 빌드, MICROROS 모드 .bin 생성, agent↔호스트 빌드 클라이언트로 토픽 왕복 |
| 6. Jetson 측 통합(agent launch, 전환) | L1 | agent 기동, `ros2 topic list`에 인터페이스 표시(가상 클라이언트), 기존 `base.launch.py` 영향 없음 |
| 7. (후속, 별도 승인) 브링업 | L2~L4 | LED→UART→IMU→배터리→모터(바퀴 띄움, 사용자 전원 스위치 옆) 순. 이번 범위 밖 |
