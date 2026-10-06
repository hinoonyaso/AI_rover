# 체크리스트

- 전체 항목은 [PROJECT_CHECKLIST.md](PROJECT_CHECKLIST.md)에 있다 (`[x]` 완료 · `[~]` 부분 완료 · `[ ]` 미완료).
- **작업을 끝낼 때마다** 해당 항목의 상태를 바꾸고, 새로 알게 된 사실(수치, 원인)을 항목 옆에 한 줄로 적는다.
- 오류를 만나면 [../troubleshooting/](../troubleshooting/)에 기록한다.
- 프로젝트 전체 기획(JetInspect-M)은 [../prd/jetinspect-m.md](../prd/jetinspect-m.md)
  (+파이프라인 상세 [../prd/jetinspect-m-pipelines.md](../prd/jetinspect-m-pipelines.md)).
  새 기능을 시작할 때의 작업 방식(PRD→Task→실행)은 `AGENTS.md`의 "새 기능 작업 방식" 참고.

## 진행률 (2026-10-06 기준)

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
| Nav2(Costmap/Planner/BT) | **설정 완료, 실주행 1회 성공 + 2회차 중 충돌**(2026-10-05): DDS/RViz 툴 문제(`troubleshooting/018`) 해결 후 Trial 1 성공(거리오차 4.8%, 각도오차 5.3°, 7.2/8.9). 방 재매핑(의자가 진짜 장애물이었음, `lap2_20261005`) + inflation_radius 안전값 보정(`troubleshooting/020`). **Trial 2 중 로봇이 의자 다리에 충돌**(2D LiDAR 사각지대로 추정, `troubleshooting/021`, 미해결) — 자율주행 일시 중단, 반복 시험/지표 기록은 이 안전 문제 해결 후 재개 |
| RGB-D 카메라 | **완료**(2026-10-05): TF 연결, RGB/Depth 실측, RGB-Depth 픽셀 정렬, camera_info 캘리브레이션, PointCloud 시각 검증까지 전부 확인됨 |
| Vision AI, 3D Perception | 미완료 |
| **로봇팔** | 서보 ID 확인 + **실시간 위치 읽기(`/joint_states`) 완료**(관절 1~5, 그리퍼 10, 실물과 RViz 자세 일치 확인). **저수준 위치 명령(`arm/command`)·토크(`arm/torque`)·home pose 완료**(2026-10-05, 실기 검증, 진단/bring-up용 인터페이스). MoveIt2 / IK / `FollowJointTrajectory`(ros2_control)는 미완료 |
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

## 2026-10-06 구조 개선 반영 현황 (외부 리뷰 기반)
표준화·정량평가·재현성 중심으로 전환. 순서/게이트는 `docs/ROADMAP.md`가 기준이다(여기는 진행 요약).
1. [x] README 현재 상태 최신화 (Current vs Target odometry 구분 포함)
2. [~] `firmware_source/*.bin`, `decompile/`를 추적에서 제거하고 `.gitignore` 처리(2026-10-06, 로컬 파일은 유지). **과거 커밋 이력에는 아직 남아 있음** — 이력 삭제(filter-repo + force-push)는 사용자 승인 필요
3. [x] `package.xml` license(Apache-2.0)/maintainer/version 정리 + `LICENSE` 추가. 단 vendor 파생물(Hiwonder URDF/메쉬 등)의 라이선스는 별도 확인 필요
4. [~] Nav2 baseline 15회(3시나리오×5): 계획 `prd/nav2-baseline-test-plan.md` + 기록/분석 도구 작성 완료, **시험 미실시**(사용자 입회 필요). 순서: baseline → ST-Link/엔코더 bring-up → encoder odom+EKF → 동일 15회 재시험(Before/After) → DWB vs MPPI → ros2_control 팔 PRD
5. [~] ROS2 unit test: `jetrover_base/test/test_rrc_protocol.cpp` 14개 통과(CRC·파서 resync·모터/서보/토크). mecanum IK/FK는 `mecanum.hpp/.cpp`로 분리 후 `test_mecanum.cpp` 7개 통과(IK↔FK 왕복 포함, 2026-10-06). 서보 pulse↔rad 8개(`servo_convert`)·watchdog 11개(`link_watchdog`)도 분리 후 통과, 모두 CI 포함(2026-10-06). **분리한 `base_node.cpp`의 실기 동작은 미검증(L0까지)**
6. [ ] STM32 encoder 실기 bring-up → encoder odom + EKF → Nav2 재평가 (→ MPPI A/B)
7. [ ] Arm: `ros2_control` + `FollowJointTrajectory` 설계 (`arm/command`·`arm/torque`는 진단용으로 유지)
8. [x] GitHub Actions CI(`.github/workflows/ci.yml`): 펌웨어 host test + ROS Jazzy colcon build/test(base, microros) 통과 확인(run 9, 2026-10-06). **이후 확장분(static-checks 잡, bringup/navigation/perception 빌드, synthetic rosbag 분석 시험)은 push 후 결과 확인 전 → 아래 안전성 항목 참고**

## 안전성/L0 보강 (2026-10-06, 하드웨어 없이, L0까지 — 실기 미검증)
- [x] `/cmd_vel` NaN/Inf 거부 + 정지, `arm/command` NaN/Inf 전체 거부 (`command_guard`, 단위시험 11개). **발견한 실제 구멍**: `std::clamp`는 NaN을 못 거르고, 팔 step 검사(`abs(...) > max`)도 NaN에서는 거짓이라 통과 → `troubleshooting/029`
- [x] STM32 침묵 중 0이 아닌 `cmd_vel` 거부(저장 안 함 → 복구 후 옛 명령 부활 방지). 0 명령은 허용
- [x] 시작 시 파라미터 fail-fast: 형상/타임아웃/서보(부호 ±1, pulse 범위, range>0, home pose finite) 검증, 실패 시 `invalid_argument`로 종료(exit 1)
- [x] 정적 검사 CI `tools/ci/static_checks.py`: Python 문법, YAML/XML 파싱, package.xml/setup.py TODO 검사 (검사 중 `navigate_through_poses_no_backup.xml` 주석의 `--`(XML 위반, 동작엔 영향 없었음) 발견·수정)
- [~] synthetic rosbag으로 `analyze.py` 검증(`tools/nav/benchmark/test_analyze_bag.py`) — CI(ROS 컨테이너)에서만 실행 가능, **결과 확인 필요**
- [ ] **현장 확인 필요(실기)**: ① `cmd_vel` NaN을 일부러 보내도 바퀴가 안 도는지 ② STM32 침묵 상황에서 명령 거부 로그 ③ 잘못된 파라미터로 기동 시 즉시 종료 — 모터 시험이라 사용자 입회(L3, 바퀴 띄움)

## 문서화 작업 (2026-10-06, 코드 변경 없음)
- [x] `docs/` 신설: ROADMAP(재정렬 순서·게이트·MVP), architecture(Current vs Target, TF, 센서 커버리지), design/depth-obstacle(임시 방식·한계·검증 항목), case-studies/nav-depth-obstacle(Failure→Root Cause→Fix, 결과 수치는 미측정), benchmarks/navigation/tuning-history
- [x] PRD/TEST_PLAN 추가: `prd/encoder-odometry*.md`, `prd/nav2-mppi-ab-test-plan.md`, `prd/nav2-baseline-test-plan.md`에 열린 결정 추가
- [ ] 후속(코드/설정 건드리는 일이라 승인 필요): `nav2_params.yaml` 주석을 "짧은 이유 + tuning-history 링크"로 축약, `ros2 run tf2_tools view_frames`/`rqt_graph` 실기 이미지 저장
