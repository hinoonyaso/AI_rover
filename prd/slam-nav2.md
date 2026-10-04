# PRD: SLAM/Nav2 완성 (개발 순서 2단계)

## 목표
JetInspect-M 개발 순서(`prd/jetinspect-m.md` 13절)의 2단계. SLAM은 이미 지도 생성·저장까지 끝났고
(`checklist` 6번), AMCL도 소프트웨어 연동까지는 확인됐다(`checklist` 7번). 이번 단계의 목표는
**실제 로봇을 움직여 AMCL localization을 물리적으로 검증**하고, **Nav2로 저장된 지도 위에서
`NavigateToPose`가 실제로 동작**하게 만드는 것이다 — 3단계(Perception) 이후 설비 점검 미션이
자율주행을 전제로 하므로, 이게 없으면 뒤 단계 전부가 막힌다.

## 범위
- AMCL 물리 검증: 로봇을 실제로 움직여서 `/amcl_pose`가 실제 위치를 따라가는지, relocalization이
  되는지 확인 (`checklist` 7번 남은 항목)
- Nav2 최소 구성: Costmap(Static+Obstacle+Inflation), Global Planner(SmacPlanner2D 또는 NavFn),
  Local Controller(**초기 DWB** — `prd/jetinspect-m-pipelines.md` 3절에 이미 "초기 DWB, 최종 MPPI"로
  정해둠, 이번 단계는 DWB까지만), Recovery(ClearCostmap/Spin/BackUp/Wait), `NavigateToPose` 액션
- 기존 저장된 지도(`maps/lap1_20260922.yaml`, 67×67 @ 0.05m ≈ 3.35×3.35m 방 하나) 안에서의 주행
- 정량 측정: Goal 위치오차, Localization 안정성(pose drift), 성공률(`checklist` 8번의 지표 정의 재사용)

## 비범위 (이번 단계에서 안 함)
- MPPI 컨트롤러 전환(최종 단계, 나중에)
- Nav2 BT 커스터마이징(`checklist` 9번) — 기본 BT로 `NavigateToPose`만 되면 충분, 커스텀 BT는 Mission
  단계(개발 순서 7단계)에서
- AprilTag 정밀 정렬(`checklist` 10번, 별도 단계)
- 새 지도/넓은 공간 매핑 — 지금 있는 작은 방 지도로 충분
- 동적 장애물 회피 고급 시나리오(사람 추적 등) — 기본 Costmap 장애물 회피만

## 제약
- AGENTS.md 안전 규칙 그대로: 로봇이 실제로 움직이는 시험은 **사전에 알리고**, 주변 공간을 확보하고,
  바닥 주행은 저속(0.05~0.1 m/s)부터, 사용자가 로봇 근처/전원 스위치 가까이 있어야 한다
- Mecanum이라 `robot_model_type: nav2_amcl::OmniMotionModel`은 이미 설정됨 — 유지
- STM32 hang은 재플래시 이후 안 났지만 "해결"은 아니다(`troubleshooting/001`) — 장시간 주행 시험 중
  재발 가능성을 염두에 두고, `STM32 silent` 로그를 계속 지켜본다
- 로봇팔은 아직 안 움직이지만(모터 명령 없음), 주행 중 팔이 LiDAR 시야(뒤쪽 약 160°)를 가린다는 건
  기존에 확인된 사실 — Costmap이 이 사각지대를 장애물로 오인하지 않는지 확인 필요

## 완료 기준
AGENTS.md 공통 기준(빌드/재현 가능한 config/실물 검증/수치 문서화) + 이 단계 전용:
- AMCL: 로봇을 1m 이상 이동시켰을 때 `/amcl_pose`가 실제 이동과 같은 방향/거리로 따라감(눈대중 또는
  줄자 비교), kidnap 복구 1회 이상 시연
- Nav2: RViz(또는 CLI)에서 목표 pose를 주면 `NavigateToPose`가 성공적으로 완주, 목표 위치 오차를
  최소 1회 측정해서 수치로 남김
- `checklist` 7/8번 섹션의 관련 항목이 `[x]`로 바뀜
