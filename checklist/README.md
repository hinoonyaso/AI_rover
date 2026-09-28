# 체크리스트

- 전체 항목은 [PROJECT_CHECKLIST.md](PROJECT_CHECKLIST.md)에 있다 (`[x]` 완료 · `[~]` 부분 완료 · `[ ]` 미완료).
- **작업을 끝낼 때마다** 해당 항목의 상태를 바꾸고, 새로 알게 된 사실(수치, 원인)을 항목 옆에 한 줄로 적는다.
- 오류를 만나면 [../troubleshooting/](../troubleshooting/)에 기록한다.
- 프로젝트 전체 기획(JetInspect-M)은 [../prd/jetinspect-m.md](../prd/jetinspect-m.md)
  (+파이프라인 상세 [../prd/jetinspect-m-pipelines.md](../prd/jetinspect-m-pipelines.md)).
  새 기능을 시작할 때의 작업 방식(PRD→Task→실행)은 `AGENTS.md`의 "새 기능 작업 방식" 참고.

## 진행률 (2026-09-28 기준)

| 영역 | 상태 |
|---|---|
| Jetson/ROS2 개발환경 | 완료 |
| STM32 protocol 분석 | 완료 |
| Base driver | 거의 완료 |
| IMU | 완료 (gyro scale 97%, accel 스케일 보정은 보류) |
| Open-loop odom | 거의 완료 (바닥 주행 1차 완료: 전진·옆 이동은 명령과 일치(0.99), 회전은 명령의 81%) |
| EKF | 구현 완료 / 실주행 검증 남음 |
| **STM32 안정성** | **미해결(hang 9회, 원인 미확정). RST 버튼으로 즉시 복구 가능, DTR/RTS 자동 리셋 경로는 닫음. → 원인 규명 대신 자체 펌웨어 재작성 착수: UART1 ROM 부트로더 검증·전체 flash 백업·재플래시·기능 전수 검증(부저/OLED/IMU/배터리/바퀴모터/로봇팔서보) 완료, 프로토콜 코덱 구현·테스트 완료(`firmware/rrc_m4/`). **ST-Link 도착 대기 중** — 오면 SWD로 핀맵 확정 후 실제 브링업. 계획: `~/.claude/plans/enchanted-chasing-sky.md`** |
| TF/URDF | 부분 완료 (URDF 기본 트리, `base_footprint` 체계, 실제 로봇 TF 확인. 팔/카메라/실측 footprint 남음) |
| LiDAR | 동작 (`/scan` 14 Hz, TF·방향 검증 완료). **운영 중 USB 재연결 1회 발견, 드라이버 자동복구 없음** (`troubleshooting/015`) |
| SLAM | 키보드 조종 한 바퀴 완주, hang 없이 지도 완성. **표준 지도(.pgm/.yaml) 저장도 이미 완료**(이전 기록의 "실패"는 stale였음, 2026-09-28 정정). loop closure 정량화, 반복 주행은 남음 |
| **AMCL, Localization** | **소프트웨어 스택 실기 검증 완료**(map_server+amcl+lifecycle_manager, `/amcl_pose`·`map→odom` TF 확인). 실제 주행 기반 relocalization/오차 측정은 남음 |
| Nav2(Costmap/Planner/BT) | 미완료 |
| RGB-D 카메라 | 동작 (Orbbec DaBai DCW, SDK v1 소스 빌드로 해결). TF 연결·calibration 남음 |
| Vision AI, 3D Perception | 미완료 |
| **로봇팔(하드웨어)** | **버스 서보 ID 확인 완료**(관절 1~5, 그리퍼 10, raw 프로토콜로 실기 검증). MoveIt2/URDF/IK는 미완료 |
| Mission BT | 미완료 |
| FastAPI, React 관제, DB | 미완료 |
| RAG/Memory | 미완료 |
| **Voice AI(하드웨어)** | **마이크 어레이(XFM-DP)/스피커 하드웨어 확인 완료**(녹음↔재생 왕복 확인). VAD/STT/LLM/TTS는 전부 미착수(엔진 자체 미설치) |
| 시스템 통합 | 미완료 |

## 지금 당장 남은 일
1. ST-Link 도착 대기 → 도착하면 SWD로 STM32 핀맵 확정, 신규 펌웨어 브링업 시작
2. AMCL: 실제 로봇을 움직여서 relocalization/localization error 측정
3. 위 둘과 병행 가능: `prd/jetinspect-m.md`를 참고해 Perception(YOLO11n)이나 Voice(STT 엔진)
   중 하나를 골라 PRD→Task 분해부터 시작 (`AGENTS.md` "새 기능 작업 방식" 참고)
