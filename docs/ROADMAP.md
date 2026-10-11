# ROADMAP (2026-10-06 재정렬, 2026-10-08 1단계 갱신)

신뢰 수준: **계획**. 근거와 배경은 외부 리뷰(2026-10-06)와 이 저장소의 실측 기록. 원래의 고정 개발 순서
(`Base/TF → SLAM/Nav2 → RGB-D/YOLO → 3D XYZ → MoveIt2 → Voice → Mission BT → Battery/Safety → 통합`, `prd/jetinspect-m.md` 13절)는
**유지**하고, 그 안의 "SLAM/Nav2" 단계를 아래처럼 정량 검증 중심으로 세분화한다. 음성/LLM을 앞당기지 않는다는 규칙도 그대로다.

## 방향 전환의 요점
기능 추가 중심 → **표준 ROS2 구조 + 실센서 피드백 + 정량평가 + 회귀 테스트**.
~~현재 가장 큰 구조적 약점은 odometry다: STM32(vendor 펌웨어)가 엔코더를 안 보내므로 `wheel_twist`는 명령 속도(open-loop)다.~~
**2026-10-11 갱신**: 자체 펌웨어(rrc_m4)가 엔코더(FUNC 0x21)를 보내고 base_node가 기본값 `wheel_twist_source: auto`로 측정 속도를 쓴다
(E4/E5로 개루프 정확도 개선 확인). 지금 주행의 남은 약점은 odom이 아니라 **도착 정밀도(목표 12~19 cm 앞에서 정지, goal 허용 오차 0.15 m)**와
**정면 장애물 회피 효율**이다 — 아래 2026-10-11 판단 참고.

## 단계와 게이트

| # | 작업 | 하드웨어 | 게이트(통과 조건) | 상태 |
|---|---|---|---|---|
| 0 | 저장소 정리: README, 라이선스, package.xml, CI, ROS2 unit test | 불필요 | CI 초록, README가 실제 상태와 일치 | 완료 (unit test: RRC 코덱·메카넘·서보 변환·watchdog·명령 검증, CI 포함. 안전 로직 L0 보강 — `checklist/README.md`) |
| 1 | **Nav2 baseline** (open-loop odom, 15회) | 로봇 L4 | `prd/nav2-baseline-test-plan.md` 완료 기준 4개 | **E6로 대체(2026-10-10~11)**: 같은 펌웨어에서 command(=open-loop) 대 encoder 15회씩(`docs/benchmarks/navigation/e6v2_20261011.md`). vendor 펌웨어 기준 baseline은 따로 재지 않음 |
| 2 | STM32 엔코더 bring-up | ST-Link, 로봇 L2~L3 | `prd/encoder-odometry-test-plan.md` E1~E3 | **완료(2026-10-10~11)**: 자체 펌웨어 flash·bring-up(`docs/benchmarks/firmware_bringup_20261010.md`), 3,996 ticks/rev, E3 안전 시험 통과(timeout 1.04 s, e-stop 0.86 s, 호스트 SIGKILL 1.30 s), 유휴 8 h·부하 포함 10 h 40 m 소크 리셋 0 |
| 3 | encoder odom + EKF 재구성 | 로봇 L3~L4 | 같은 baseline을 `encoder` 조건으로 재시험, Before/After 표 | **완료(2026-10-11)**: 개루프 정확도 개선(E4/E5), Nav2 폐루프 30회에서는 차이 없음(허용 오차·AMCL 편향에 가려짐) → 기본값 `auto` |
| 4 | DWB vs MPPI A/B | 로봇 L4 | `prd/nav2-mppi-ab-test-plan.md` | **완료(잠정, 2026-10-11, 각 15회)**: 직선은 MPPI, 정면 상자·대각 회전은 DWB 우세 → **기본값 DWB 유지**, MPPI는 변형으로 보관. `docs/benchmarks/navigation/dwb_vs_mppi_20261011.md` |
| 5 | Arm: ros2_control + FollowJointTrajectory 설계 | 불필요(설계) → 로봇 L2 | PRD 승인 → hardware interface가 `arm/command`와 같은 동작 재현 | **다음 차례**(Nav2 동결 후 PRD 작성). 선행 완료: 서보별 데드밴드 보정·읽기 피드백 보정(오차 ±1~2 펄스), 홈 자세 ±1 펄스(2026-10-11) |
| 6 | MoveIt2 단독 joint-space 이동 | 로봇 L2~L3(팔) | perception 없이 목표 관절각 도달·충돌 회피 | 계획 |
| 7 | RGB-D → XYZ → TF | 로봇 | 알려진 위치 물체의 base_link 좌표 오차 측정 | 계획 |
| 8 | 단순 블록 Pick & Place | 로봇 L3~L4 | 성공률 측정(MVP 최소 N회) | 계획 |
| 9 | YOLO/TensorRT | Jetson | 정밀도/FPS/지연 측정 | 계획 |
| 10 | 점검 대상 1개 (Stack Light 권장) | 로봇 | 판정 정확도 | 계획 |
| 11 | Mission BT | 로봇 | 음성 없이 키보드/CLI 지시로 end-to-end 1회 | 계획 |
| 12 | Voice | 마이크/스피커 | 명령 세트 intent 정확도 | 계획 |
| 13 | Dashboard | — | 필요한 최소 화면 | 마지막 |
| 14 | RAG | — | **정말 필요할 때만** | 보류 |


**2026-10-11 판단**: 주행 단계는 goal 허용 오차 0.15 대 0.10 단일 실험 하나만 남기고 종료 기준(체크리스트 8, 위치 정확도와 장애물 안전 분리)을 채우면 Nav2 설정을 동결한다. MVP가 요구하는 주행은 "근처 ±10 cm + 카메라 재검출 보정"(PLAN_ARM_TO_MVP 8단계)이므로 정면 상자 회피 개선·추가 DWB/MPPI 튜닝·대규모 시뮬레이션은 우선순위를 낮춘다. 그다음 AprilTag 정렬(체크리스트 10)과 팔 단계(5~8)로 간다.

게이트를 통과하지 못하면 다음 단계로 넘어가지 않는다. 게이트 결과는 수치로 `checklist/`에 남긴다.
5~13단계의 구체 작업·게이트 수치·준비물·위험은 [PLAN_ARM_TO_MVP.md](PLAN_ARM_TO_MVP.md)(계획, 2026-10-08).

### 1단계 선행 정리 (2026-10-08 갱신 — 아래는 당시 기록, 현재 상태는 위 표와 2026-10-11 판단)
baseline 수치를 엔코더 적용 전 "Before"로 쓰려면 설정 버그가 먼저 없어야 한다. 2026-10-07 실기 시험에서 다음을 찾고 고쳤다
(`troubleshooting/031`, `032`): DWB 후보가 매 주기 vy 전 범위(→ LimitedAccelGenerator), RotateToGoal 허용오차 0.25 > goal checker 0.15
(→ 0.12), 데드존 아래 속도 선택(→ min_speed_xy 0.04 + min_speed_theta 0.1), local costmap에 LiDAR 점 누적(→ scan/depth 레이어 분리),
몸이 비스듬한 채 대각선 주행(→ RotationShim), 팔 홈 자세 게이트 과민(→ 0.08 rad + debounce), AMCL 초기 위치(→ 스캔-지도 자동 매칭).
이들은 "미세조정"이 아니라 설정 충돌/버그 수정으로 보고 진행했다. DWB 쪽 작업이 더 길어지면 4단계(MPPI 비교)를 앞당기는 것을 검토한다.

| 순서 | 작업 | 상태 |
|---|---|---|
| 1-1 | 직진 흔들림 A/B: LimitedAccel+RotationShim vs Standard 각 6회 (`tools/nav/straight_trial.py`) | **완료(2026-10-09)**: 둘 다 6/6, 몸 방향 오차 중앙값 4.5° vs 29° → LimitedAccel 채택. 기본 BaseObstacle(0.1)로 재확인은 1-3에서 |
| 1-2 | 팔 홈 자세 재설계: depth 감지 0.18~0.51 m → near ≤ 0.25, far ≥ 0.8 m (`tools/perception/`) | **완료(2026-10-09)**: joint4 1.45, 0.26~0.81 m, 상자 3위치 검출 — `benchmarks/perception/home_pose_20261009.md` |
| 1-3 | 회피 정리: ~~BaseObstacle 정합~~(불필요), **global costmap 레이어 분리(완료 2026-10-09)**, collision monitor 개입 확인(**원인 아님**), footprint 실측(완료 2026-10-09), 상자 회피 재시험 | 2026-10-09: 상자를 옆으로 옮긴 조건에서 MPPI 성공. **정면 상자는 미해결 — 알려진 한계로 미룸(2026-10-11)** |
| 1-4 | baseline 정식 15회 | E6 v2 30회 + DWB 대 MPPI 15회로 대체(2026-10-11) |
| (추가) | Gazebo 시뮬레이션(`prd/gazebo-sim.md`, gz_ros2_control + mecanum_drive_controller, 지도→월드): Nav2/MPPI를 배터리 없이 반복 시험 | 환경 구축·L0 완료(2026-10-09), host 실행 대기 |

~~알려진 미해결: Nav2 정지 후 바퀴 울림~~ — 자체 펌웨어 이후 재발 없음(사용자 관찰 2026-10-11, SWD 측정 확정은 안 함 — `troubleshooting/032`).

**시험 충돌 기록(2026-10-11까지)**: 실기 주행 시험에서 사용자 확인 충돌 0회. 운영 규칙상 사용자가 충돌을 보고하지 않은 회차는 충돌이 없었던 것으로 확인한 것으로 취급한다. `run_trial.py`가 다음 회차를 시작할 때 이전 회차의 '충돌 없음'을 확정하고, 세션의 마지막 회차는 `tools/nav/benchmark/confirm_last_trial.py`로 따로 확정한다.
처음 외부 분석의 "기준 depth 대신 TF/URDF self-filter + 바닥 제거"는 7단계(RGB-D → XYZ → TF) 근처에서 한다.

## MVP 범위 축소 (프로젝트가 너무 넓어지는 것을 막는다)
최종 데모는 다음 한 줄만 보장한다:
`음성 임무 → 점검 위치로 자율주행 → 설비 1종 판정 → 떨어진 부품 1종 Pick & Place → 결과 보고`
- 점검 대상: **Stack Light + Dropped Part** 두 가지만. Gauge/OCR/Valve/버튼 조작은 확장.
- 초기 perception: `YOLO → BBox 중심 → depth median → camera XYZ → TF → top-down grasp → MoveIt2`. 6D pose·segmentation·grasp network는 이후.
- `prd/jetinspect-m.md`의 나머지 항목(RAG, 풀 대시보드 등)은 MVP 이후이며 지금 착수하지 않는다.

## 포트폴리오 산출물 5종 (진행 추적)
| 산출물 | 위치 | 상태 |
|---|---|---|
| Architecture Diagram | [architecture.md](architecture.md) | 초안 (mermaid) |
| ROS Graph / TF Tree | architecture.md에 TF 트리 텍스트. 실제 `rqt_graph`/`view_frames` 이미지는 실기에서 생성 필요 | 일부 |
| Failure → Root Cause → Fix 사례 | [case-studies/nav-depth-obstacle.md](case-studies/nav-depth-obstacle.md) + `troubleshooting/` | 1건 정리, 결과 수치 미측정 |
| Before/After Benchmark | `docs/benchmarks/navigation/` | baseline 시험 후 |
| End-to-End Demo | — | MVP 완성 후 |

## 하지 않는 것 / 보류하는 것
- `base_node` 전면 `ros2_control` 이행: 엔코더 baseline 확정 후 별도 PoC 브랜치에서 비교만 한다 (현재 코드 폐기 안 함).
- DWB 파라미터 추가 미세조정: baseline 이후 MPPI 비교로 대체 (ROI 감소).
- `line_goal.py`의 core 승격: 실험 도구로 `tools/nav/`에 둔다 (직선 복귀가 일반 자율주행의 최적 행동이 아님).
- `base_node.cpp`에 기능 추가: 필요하면 먼저 내부 클래스를 분리한다 (rrc_transport / base_drive / imu / arm / battery).
