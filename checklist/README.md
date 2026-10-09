# 체크리스트

- 전체 항목은 [PROJECT_CHECKLIST.md](PROJECT_CHECKLIST.md)에 있다 (`[x]` 완료 · `[~]` 부분 완료 · `[ ]` 미완료).
- **작업을 끝낼 때마다** 해당 항목의 상태를 바꾸고, 새로 알게 된 사실(수치, 원인)을 항목 옆에 한 줄로 적는다.
- 오류를 만나면 [../troubleshooting/](../troubleshooting/)에 기록한다.
- 프로젝트 전체 기획(JetInspect-M)은 [../prd/jetinspect-m.md](../prd/jetinspect-m.md)
  (+파이프라인 상세 [../prd/jetinspect-m-pipelines.md](../prd/jetinspect-m-pipelines.md)).
  새 기능을 시작할 때의 작업 방식(PRD→Task→실행)은 `AGENTS.md`의 "새 기능 작업 방식" 참고.

## 진행률 (2026-10-10 기준, 2026-10-06 이후 바뀐 행에 날짜 표시)

| 영역 | 상태 |
|---|---|
| Jetson/ROS2 개발환경 | 완료 |
| STM32 protocol 분석 | 완료 |
| Base driver | 거의 완료 |
| IMU | 완료 (gyro scale 97%, accel 스케일 보정은 보류) |
| Open-loop odom | 거의 완료 (바닥 주행 1차 완료: 전진·옆 이동은 명령과 일치(0.99), 회전은 명령의 81%) |
| EKF | 구현 완료 / 실주행 검증 남음 |
| **STM32 안정성** | **호전됨, 원인 미확정** (hang 9회는 전부 2026-09-27 재플래시 이전, 이후 재발 없음 — `troubleshooting/001`). RST 버튼으로 복구 가능. 자체 펌웨어(`firmware/rrc_m4/`)는 L0까지(빌드·호스트 시험). **2026-10-08 ST-Link 도착 → 2026-10-11 SWD 백업부터 시작**(순서표 `firmware/rrc_m4/README.md` "ST-Link 첫날 순서", 스크립트 `swd_backup.sh`). 바퀴 울림(032)도 같은 날 SWD로 원인 측정 예정 |
| TF/URDF | **거의 완료**(2026-10-04): Hiwonder 공식 메쉬+5축 팔+그리퍼+뎁스카메라 전부 TF에 포함, 팔은 실제 서보 각도로 실시간 반영(host RViz에서 실물과 비교 확인됨). 실측 footprint만 남음(전부 Hiwonder 공식값) |
| LiDAR | 동작 (`/scan` 14 Hz, TF·방향 검증 완료). **운영 중 USB 재연결 1회 발견, 드라이버 자동복구 없음** (`troubleshooting/015`) |
| SLAM | 키보드 조종 한 바퀴 완주, hang 없이 지도 완성. **표준 지도(.pgm/.yaml) 저장도 이미 완료**(이전 기록의 "실패"는 stale였음, 2026-09-28 정정). loop closure 정량화, 반복 주행은 남음 |
| **AMCL, Localization** | **소프트웨어 스택 실기 검증 완료**(map_server+amcl+lifecycle_manager, `/amcl_pose`·`map→odom` TF 확인). 실제 주행 기반 relocalization/오차 측정은 남음 |
| Nav2(Costmap/Planner/BT) | **동작, 튜닝 중**(2026-10-10). 직진 흔들림 해결(LimitedAccelGenerator + RotationShim + Twirling, 031). depth 장애물을 local/global costmap 별도 레이어로(LiDAR가 상자 표시를 못 지우게). **상자 회피**: MPPI(Omni, 정면 유지 + 대각 이동)로 왕복 3/4 성공, 우회 15~18 cm(034). 실패 1회(F2-4)는 정체 원인 미확정 → 시험 bag에 costmap 녹화 추가. 메카넘 대각 45° 제한 `LateralRatioCritic` 구현(L0, 주행 전). 시작 시 자동 위치 추정(`scan_match_init`). 파라미터 이력 `docs/benchmarks/navigation/tuning-history.md`. **baseline 15회는 미실시**(분석 도구는 실기 bag으로 검증 완료) |
| Gazebo 시뮬레이션 / 디지털 트윈 | **L0 완료, host 실행 전**(2026-10-09~10): `jetrover_gazebo`(메카넘 ros2_control, LiDAR/RGB-D/IMU, 지도→월드), 컨트롤러 비교 시나리오 `tools/sim/`. 방 스캔 도구(`tools/scan/`)와 스캔용 팔 자세(카메라 0.52 m) 확정, 녹화는 남음 |
| RGB-D 카메라 | **완료**(2026-10-05): TF 연결, RGB/Depth 실측, RGB-Depth 픽셀 정렬, camera_info 캘리브레이션, PointCloud 시각 검증까지 전부 확인됨 |
| Vision AI, 3D Perception | 미완료 |
| **로봇팔** | 위치 읽기(`/joint_states`)·저수준 명령(`arm/command`, `arm/torque`)·토크 완료. **MoveIt2 설정 + 궤적 브리지(`arm/command_timed`) 실기 왕복 4/4**(2026-10-06~07, `jetrover_manipulation`), Setup Assistant 충돌 행렬 병합. 주행용 홈 자세 재설계(joint4 1.45, depth 0.26~0.81 m, 2026-10-09). 남은 것: IK/Pose goal, PlanningScene, `ros2_control` 팔 PRD |
| Mission BT | 미완료 |
| FastAPI, React 관제, DB | 미완료 |
| RAG/Memory | 미완료 |
| **Voice AI(하드웨어)** | **마이크 어레이(XFM-DP)/스피커 하드웨어 확인 완료**(녹음↔재생 왕복 확인). VAD/STT/LLM/TTS는 전부 미착수(엔진 자체 미설치) |
| 시스템 통합 | 미완료 |

## 지금 당장 남은 일 (2026-10-10)
개발 순서(PRD 13절, 2단계 세분화는 `docs/ROADMAP.md`): **2단계(Nav2) 진행 중** — `Nav2 baseline → 엔코더 odom → Before/After → DWB vs MPPI`.
1. **STM32 SWD 백업 → 자체 펌웨어 브링업**(2026-10-11~, 엔코더 odom의 전제). flash는 단계마다 승인
2. Nav2 baseline 15회(`prd/nav2-baseline-test-plan.md`) — 엔코더 odom 전 "Before" 값
3. LateralRatioCritic 주행 시험(실기 왕복 4회, `diag50_frac` < 5%) — 먼저 host Gazebo에서 `tools/sim/run_scenarios.sh`
4. 방 RGB-D 스캔 녹화(8.14.7) → host 재구성/Blender
5. Perception/Voice 등 뒷 단계는 순서 규칙상 보류(앞당길 땐 사용자 확인)

## 2026-10-06 구조 개선 반영 현황 (외부 리뷰 기반)
표준화·정량평가·재현성 중심으로 전환. 순서/게이트는 `docs/ROADMAP.md`가 기준이다(여기는 진행 요약).
1. [x] README 현재 상태 최신화 (Current vs Target odometry 구분 포함)
2. [~] `firmware_source/*.bin`, `decompile/`를 추적에서 제거하고 `.gitignore` 처리(2026-10-06, 로컬 파일은 유지). **과거 커밋 이력에는 아직 남아 있음** — 이력 삭제(filter-repo + force-push)는 사용자 승인 필요
3. [x] `package.xml` license(Apache-2.0)/maintainer/version 정리 + `LICENSE` 추가. 단 vendor 파생물(Hiwonder URDF/메쉬 등)의 라이선스는 별도 확인 필요
4. [~] Nav2 baseline 15회(3시나리오×5): 계획 `prd/nav2-baseline-test-plan.md` + 기록/분석 도구 작성 완료, **시험 미실시**(사용자 입회 필요). 순서: baseline → ST-Link/엔코더 bring-up → encoder odom+EKF → 동일 15회 재시험(Before/After) → DWB vs MPPI → ros2_control 팔 PRD
5. [x] ROS2 **L0 unit test 구축** (CI 포함, 2026-10-06): RRC 코덱 14 · 메카넘 9(IK↔FK 왕복, C++/Python 골든 벡터) · 서보 변환 8 · watchdog 11 · 명령 검증/파라미터 fail-fast 11 · micro-ROS 기구학 4 · 벤치마크 지표 8 + synthetic rosbag 분석. **실기 regression은 별도(L3/L4, 사용자 입회) — 아래 "현장 확인 필요" 항목 참고**. 세부: `jetrover_base/test/test_rrc_protocol.cpp` 14개 통과(CRC·파서 resync·모터/서보/토크). mecanum IK/FK는 `mecanum.hpp/.cpp`로 분리 후 `test_mecanum.cpp` 7개 통과(IK↔FK 왕복 포함, 2026-10-06). 서보 pulse↔rad 8개(`servo_convert`)·watchdog 11개(`link_watchdog`)도 분리 후 통과, 모두 CI 포함(2026-10-06). 분리한 `base_node.cpp`의 실기 동작은 미검증(L0까지)
6. [ ] STM32 encoder 실기 bring-up → encoder odom + EKF → Nav2 재평가 (→ MPPI A/B)
7. [ ] Arm: `ros2_control` + `FollowJointTrajectory` 설계 (`arm/command`·`arm/torque`는 진단용으로 유지)
8. [x] GitHub Actions CI(`.github/workflows/ci.yml`): 펌웨어 host test + ROS Jazzy colcon build/test(base, microros) 통과 확인(run 9, 2026-10-06). 확장분(static-checks 잡, bringup/navigation/perception 빌드, synthetic rosbag 분석 시험)도 run 10에서 통과

## 안전성/L0 보강 (2026-10-06, 하드웨어 없이, L0까지 — 실기 미검증)
- [x] `/cmd_vel` NaN/Inf 거부 + 정지, `arm/command` NaN/Inf 전체 거부 (`command_guard`, 단위시험 11개). **발견한 실제 구멍**: `std::clamp`는 NaN을 못 거르고, 팔 step 검사(`abs(...) > max`)도 NaN에서는 거짓이라 통과 → `troubleshooting/029`
- [x] STM32 침묵 중 0이 아닌 `cmd_vel` 거부(저장 안 함 → 복구 후 옛 명령 부활 방지). 0 명령은 허용
- [x] 시작 시 파라미터 fail-fast: 형상/타임아웃/서보(부호 ±1, pulse 범위, range>0, home pose finite) 검증, 실패 시 `invalid_argument`로 종료(exit 1)
- [x] 정적 검사 CI `tools/ci/static_checks.py`: Python 문법, YAML/XML 파싱, package.xml/setup.py TODO 검사 (검사 중 `navigate_through_poses_no_backup.xml` 주석의 `--`(XML 위반, 동작엔 영향 없었음) 발견·수정)
- [x] synthetic rosbag으로 `analyze.py` 검증(`tools/nav/benchmark/test_analyze_bag.py`): CI run 10(ROS Jazzy 컨테이너)에서 통과 — rosbag2 읽기 경로와 지표 수치가 알려진 값과 일치. **2026-10-10 실기 bag 4개로도 검증**(시간 일치, 목표 오차는 /tf 기반으로 수정 — `prd/nav2-baseline-test-plan.md`)
- [ ] **현장 확인 필요(실기)**: ① `cmd_vel` NaN을 일부러 보내도 바퀴가 안 도는지 ② STM32 침묵 상황에서 명령 거부 로그 ③ 잘못된 파라미터로 기동 시 즉시 종료 — 모터 시험이라 사용자 입회(L3, 바퀴 띄움)

## 문서화 작업 (2026-10-06, 코드 변경 없음)
- [x] `docs/` 신설: ROADMAP(재정렬 순서·게이트·MVP), architecture(Current vs Target, TF, 센서 커버리지), design/depth-obstacle(임시 방식·한계·검증 항목), case-studies/nav-depth-obstacle(Failure→Root Cause→Fix, 결과 수치는 미측정), benchmarks/navigation/tuning-history
- [x] PRD/TEST_PLAN 추가: `prd/encoder-odometry*.md`, `prd/nav2-mppi-ab-test-plan.md`, `prd/nav2-baseline-test-plan.md`에 열린 결정 추가
- [ ] 후속(코드/설정 건드리는 일이라 승인 필요): `nav2_params.yaml` 주석을 "짧은 이유 + tuning-history 링크"로 축약, `ros2 run tf2_tools view_frames`/`rqt_graph` 실기 이미지 저장
