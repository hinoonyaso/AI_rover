# ROADMAP (2026-10-06 재정렬)

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
| 1 | **Nav2 baseline** (open-loop odom, 15회) | 로봇 L4 | `prd/nav2-baseline-test-plan.md` 완료 기준 4개 | 계획·도구 완료, 시험 미실시 |
| 2 | STM32 엔코더 bring-up | ST-Link, 로봇 L2~L3 | `prd/encoder-odometry-test-plan.md` E1~E3 | ST-Link 대기 |
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
