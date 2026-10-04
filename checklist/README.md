# 체크리스트

- 전체 항목은 [PROJECT_CHECKLIST.md](PROJECT_CHECKLIST.md)에 있다 (`[x]` 완료 · `[~]` 부분 완료 · `[ ]` 미완료).
- **작업을 끝낼 때마다** 해당 항목의 상태를 바꾸고, 새로 알게 된 사실(수치, 원인)을 항목 옆에 한 줄로 적는다.
- 오류를 만나면 [../troubleshooting/](../troubleshooting/)에 기록한다.
- 프로젝트 전체 기획(JetInspect-M)은 [../prd/jetinspect-m.md](../prd/jetinspect-m.md)
  (+파이프라인 상세 [../prd/jetinspect-m-pipelines.md](../prd/jetinspect-m-pipelines.md)).
  새 기능을 시작할 때의 작업 방식(PRD→Task→실행)은 `AGENTS.md`의 "새 기능 작업 방식" 참고.

## 진행률 (2026-10-04 기준)

| 영역 | 상태 |
|---|---|
| Jetson/ROS2 개발환경 | 완료 |
| STM32 protocol 분석 | 완료 |
| Base driver | 거의 완료 |
| IMU | 완료 (gyro scale 97%, accel 스케일 보정은 보류) |
| Open-loop odom | 거의 완료 (바닥 주행 1차 완료: 전진·옆 이동은 명령과 일치(0.99), 회전은 명령의 81%) |
| EKF | 구현 완료 / 실주행 검증 남음 |
| **STM32 안정성** | **호전됨, 원인 미확정 (hang 9회는 전부 2026-09-27 재플래시 이전). 재플래시 후 2026-10-04까지 일주일 가까이 hang 재발 없음(원인 규명은 아님, `troubleshooting/001` "2026-10-04 업데이트" 참고). RST 버튼으로 즉시 복구 가능, DTR/RTS 자동 리셋 경로는 닫음. 자체 펌웨어 재작성은 별도로 계속 진행 중: UART1 ROM 부트로더 검증·전체 flash 백업·프로토콜 코덱 구현·테스트 완료(`firmware/rrc_m4/`). **ST-Link 도착 대기 중** — 오면 SWD로 핀맵 확정 후 실제 브링업. 계획: `~/.claude/plans/enchanted-chasing-sky.md`** |
| TF/URDF | **거의 완료**(2026-10-04): Hiwonder 공식 메쉬+5축 팔+그리퍼+뎁스카메라 전부 TF에 포함, 팔은 실제 서보 각도로 실시간 반영(host RViz에서 실물과 비교 확인됨). 실측 footprint만 남음(전부 Hiwonder 공식값) |
| LiDAR | 동작 (`/scan` 14 Hz, TF·방향 검증 완료). **운영 중 USB 재연결 1회 발견, 드라이버 자동복구 없음** (`troubleshooting/015`) |
| SLAM | 키보드 조종 한 바퀴 완주, hang 없이 지도 완성. **표준 지도(.pgm/.yaml) 저장도 이미 완료**(이전 기록의 "실패"는 stale였음, 2026-09-28 정정). loop closure 정량화, 반복 주행은 남음 |
| **AMCL, Localization** | **소프트웨어 스택 실기 검증 완료**(map_server+amcl+lifecycle_manager, `/amcl_pose`·`map→odom` TF 확인). 실제 주행 기반 relocalization/오차 측정은 남음 |
| Nav2(Costmap/Planner/BT) | **설정 완료 + 실주행 1회 성공**(2026-10-04): costmap/SmacPlanner2D/DWB/BT navigator/behavior/collision_monitor 전부 설정, 원격(호스트) RViz에서 보낸 goal로 실제 주행 확인. 호스트↔Jetson DDS 디스커버리(다중 네트워크 인터페이스) + RViz 툴 설정 문제 해결(`troubleshooting/018`). 반복 시험/오차 측정/지표 기록은 남음(8.9~8.11) |
| RGB-D 카메라 | **거의 완료**(2026-10-04): TF 연결, RGB/Depth 실측, RGB-Depth 픽셀 정렬(물체 경계 겹침 확인), camera_info 캘리브레이션 값 전부 확인됨. PointCloud 시각 검증만 남음 |
| Vision AI, 3D Perception | 미완료 |
| **로봇팔** | 서보 ID 확인 + **실시간 위치 읽기(`/joint_states`) 완료**(관절 1~5, 그리퍼 10, 실물과 RViz 자세 일치 확인). MoveIt2/IK/명령 송신(움직이기)은 미완료 |
| Mission BT | 미완료 |
| FastAPI, React 관제, DB | 미완료 |
| RAG/Memory | 미완료 |
| **Voice AI(하드웨어)** | **마이크 어레이(XFM-DP)/스피커 하드웨어 확인 완료**(녹음↔재생 왕복 확인). VAD/STT/LLM/TTS는 전부 미착수(엔진 자체 미설치) |
| 시스템 통합 | 미완료 |

## 지금 당장 남은 일
개발 순서(PRD 13절) 기준 **1단계(Base/TF)는 끝났고, 2단계(SLAM/Nav2)는 핵심 동작까지 확인됨**:
1. Nav2: 반복 주행 시험(3회+)으로 목표 위치/yaw 오차 측정, 성능 지표 기록 (8.9~8.10)
2. AMCL: 실제 로봇을 움직여서 relocalization/localization error 측정 (7.1~7.4)
3. ST-Link 도착 대기(별도 트랙) → 도착하면 SWD로 STM32 핀맵 확정, 신규 펌웨어 브링업 시작
4. 2단계 끝나기 전엔 Perception/Voice/MoveIt2 등 뒷 단계는 손대지 않는다 (개발 순서 고정 규칙)
