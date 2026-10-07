# ROADMAP (2026-10-06 재정렬, 2026-10-08 1단계 갱신)

신뢰 수준: **계획**. 근거와 배경은 외부 리뷰(2026-10-06)와 이 저장소의 실측 기록. 원래의 고정 개발 순서
(`Base/TF → SLAM/Nav2 → RGB-D/YOLO → 3D XYZ → MoveIt2 → Voice → Mission BT → Battery/Safety → 통합`, `prd/jetinspect-m.md` 13절)는
**유지**하고, 그 안의 "SLAM/Nav2" 단계를 아래처럼 정량 검증 중심으로 세분화한다. 음성/LLM을 앞당기지 않는다는 규칙도 그대로다.

## 방향 전환의 요점
기능 추가 중심 → **표준 ROS2 구조 + 실센서 피드백 + 정량평가 + 회귀 테스트**.
현재 가장 큰 구조적 약점은 odometry다: STM32(vendor 펌웨어)가 엔코더를 안 보내므로 `wheel_twist`는 *명령 속도*이고(open-loop),
IMU yaw rate만 실측이다. 이 상태로 Perception/Manipulation을 올리면 그 위의 모든 성능이 부정확한 odom 위에 쌓인다.

## 단계와 게이트

| # | 작업 | 하드웨어 | 게이트(통과 조건) | 상태 |
|---|---|---|---|---|
| 0 | 저장소 정리: README, 라이선스, package.xml, CI, ROS2 unit test | 불필요 | CI 초록, README가 실제 상태와 일치 | 완료 (unit test: RRC 코덱·메카넘·서보 변환·watchdog·명령 검증, CI 포함. 안전 로직 L0 보강 — `checklist/README.md`) |
| 1 | **Nav2 baseline** (open-loop odom, 15회) | 로봇 L4 | `prd/nav2-baseline-test-plan.md` 완료 기준 4개 | 계획·도구 완료, **선행 정리(1-1~1-3) 진행 중**(아래), 시험 미실시 |
| 2 | STM32 엔코더 bring-up | ST-Link, 로봇 L2~L3 | `prd/encoder-odometry-test-plan.md` E1~E3 | ST-Link 도착(2026-10-08), 착수 예정 금요일(2026-10-09) |
| 3 | encoder odom + EKF 재구성 | 로봇 L3~L4 | 같은 baseline을 `encoder_ekf` 태그로 재시험, Before/After 표 | 계획 (`prd/encoder-odometry.md`) |
| 4 | DWB vs MPPI A/B | 로봇 L4 | `prd/nav2-mppi-ab-test-plan.md` | 계획 |
| 5 | Arm: ros2_control + FollowJointTrajectory 설계 | 불필요(설계) → 로봇 L2 | PRD 승인 → hardware interface가 `arm/command`와 같은 동작 재현 | **3·4 이후에 PRD 작성** |
| 6 | MoveIt2 단독 joint-space 이동 | 로봇 L2~L3(팔) | perception 없이 목표 관절각 도달·충돌 회피 | 계획 |
| 7 | RGB-D → XYZ → TF | 로봇 | 알려진 위치 물체의 base_link 좌표 오차 측정 | 계획 |
| 8 | 단순 블록 Pick & Place | 로봇 L3~L4 | 성공률 측정(MVP 최소 N회) | 계획 |
| 9 | YOLO/TensorRT | Jetson | 정밀도/FPS/지연 측정 | 계획 |
| 10 | 점검 대상 1개 (Stack Light 권장) | 로봇 | 판정 정확도 | 계획 |
| 11 | Mission BT | 로봇 | 음성 없이 키보드/CLI 지시로 end-to-end 1회 | 계획 |
| 12 | Voice | 마이크/스피커 | 명령 세트 intent 정확도 | 계획 |
| 13 | Dashboard | — | 필요한 최소 화면 | 마지막 |
| 14 | RAG | — | **정말 필요할 때만** | 보류 |

게이트를 통과하지 못하면 다음 단계로 넘어가지 않는다. 게이트 결과는 수치로 `checklist/`에 남긴다.
5~13단계의 구체 작업·게이트 수치·준비물·위험은 [PLAN_ARM_TO_MVP.md](PLAN_ARM_TO_MVP.md)(계획, 2026-10-08).

### 1단계 선행 정리 (2026-10-08 갱신)
baseline 수치를 엔코더 적용 전 "Before"로 쓰려면 설정 버그가 먼저 없어야 한다. 2026-10-07 실기 시험에서 다음을 찾고 고쳤다
(`troubleshooting/031`, `032`): DWB 후보가 매 주기 vy 전 범위(→ LimitedAccelGenerator), RotateToGoal 허용오차 0.25 > goal checker 0.15
(→ 0.12), 데드존 아래 속도 선택(→ min_speed_xy 0.04 + min_speed_theta 0.1), local costmap에 LiDAR 점 누적(→ scan/depth 레이어 분리),
몸이 비스듬한 채 대각선 주행(→ RotationShim), 팔 홈 자세 게이트 과민(→ 0.08 rad + debounce), AMCL 초기 위치(→ 스캔-지도 자동 매칭).
이들은 "미세조정"이 아니라 설정 충돌/버그 수정으로 보고 진행했다. DWB 쪽 작업이 더 길어지면 4단계(MPPI 비교)를 앞당기는 것을 검토한다.

| 순서 | 작업 | 상태 |
|---|---|---|
| 1-1 | 직진 흔들림 A/B: LimitedAccel+RotationShim vs Standard 각 6회 (`tools/nav/straight_trial.py`) | 일부 실측(Standard vy 뒤집힘 42~98/분, LimitedAccel 0~8회), shim 적용 후 재시험 대기 |
| 1-2 | 팔 홈 자세 재설계: depth 감지 0.18~0.51 m → near ≤ 0.25, far ≥ 0.8 m (`tools/perception/`) | 도구 완료, 실측 대기(팔 입회) |
| 1-3 | 회피 정리: 시험 전용 BaseObstacle 0.02 ↔ 기본 0.1 정합, global costmap 레이어 분리, collision monitor 개입 확인, footprint 실측 | 대기 |
| 1-4 | baseline 정식 15회 | 1-1~1-3 후 |

알려진 미해결: Nav2 정지 후 바퀴 울림(호스트 정지 명령으로 안 꺼짐, 2단계 자체 펌웨어에서 정지 시 출력 차단으로 해결 예정 — `troubleshooting/032`).
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
