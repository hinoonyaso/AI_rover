# TEST_PLAN: SLAM/Nav2 완성

레벨 정의는 `AGENTS.md`의 "테스트 레벨과 완료 기준"(L0~L5) 그대로 쓴다.

| Parent Task | 필요 레벨 | 통과 기준 |
|---|---|---|
| 7.1 Initial Pose 확인 | L4(바닥 주행, 하지만 정지 상태로도 가능) | AMCL 활성화 직후 `/amcl_pose`가 로봇의 실제 위치/자세와 육안으로 봐서 맞음 |
| 7.2 저속 이동 추적 | L4 | 1 m 이상 이동 명령 후 `/amcl_pose` 변화량이 줄자 실측과 ±10cm 이내로 일치 |
| 7.3 kidnap/relocalization | L4 | 위치를 바꾼 뒤 수 초~수십 초 내 particle filter가 새 위치로 수렴(공분산 감소, pose가 실제 위치로 이동) |
| 7.4 오차 기록 | L4 | 수치(오차 cm, drift) 하나 이상 `checklist`에 기록됨 |
| 8.1 패키지 설치 | L0 | `ros2 pkg list`에 전부 나타남, `colcon build` 영향 없음(순수 apt) |
| 8.2 Costmap 설정 | L0→L4 | L0: yaml 문법 오류 없이 노드 기동. L4: 실제 `/scan` 기반 장애물이 costmap에 반영됨(RViz로 확인) |
| 8.3 Global Planner | L0→L4 | L0: `planner_server` lifecycle configure/activate 성공. L4: 목표 지점까지 경로가 실제로 생성됨(빈 경로/실패 아님) |
| 8.4 Local Controller(DWB) | L0→L4 | L0: `controller_server` activate 성공. L4: 로봇이 실제로 경로를 따라 움직임, 옆이동(vy) 명령이 나오는지 확인(mecanum 활용 여부) |
| 8.5 BT Navigator | L0 | 기본 BT XML로 `bt_navigator` activate 성공, 에러 로그 없음 |
| 8.6 Recovery | L4 | 의도적으로 막힌 상황(장애물 바로 앞 목표 등)에서 recovery(스핀/백업 등)가 실제로 실행됨 |
| 8.7 launch 통합 | L0 | 전체 Nav2 스택이 한 launch로 기동, 모든 노드 lifecycle active, 크래시 없음 |
| 8.8 NavigateToPose 1회 | L4 | 짧은 거리(1~2m) 목표를 보내고 로봇이 충돌 없이 도착, 액션 결과 success |
| 8.9 오차 측정 반복 | L4 | 3회 이상 반복, 목표 위치 오차(cm)와 yaw 오차(도) 전부 기록 |
| 8.10 지표 기록 | L4 | CTE RMS 등 정량 지표가 checklist/문서에 수치로 남음 |
| 8.11 시나리오별 시험 | L4 (여유 있을 때) | 각 시나리오(직선/코너/좁은 통로/장애물)마다 성공 여부 기록 |

## 안전 메모
- L4(바닥 주행) 전부 AGENTS.md 안전 규칙 적용: 사전 고지, 주변 공간 확보, 저속(0.05~0.1 m/s)부터,
  사용자가 근처에 있을 것.
- 8.8~8.11은 Nav2가 자율적으로 속도를 내는 구간이라 특히 조심한다 — `max_linear`/`max_angular`
  같은 Nav2 velocity limit을 낮게 잡고 시작한다(기존 `jetrover_base`의 `max_linear: 0.2 m/s`보다
  낮거나 같게).
