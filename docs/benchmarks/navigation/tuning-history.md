# nav2_params.yaml 튜닝 이력

`src/jetrover_navigation/config/nav2_params.yaml`의 주석에 쌓인 "왜 이 값인가" 기록을 파라미터별로 모은 문서.
**이 값들은 정량 baseline이 아니라 소수 시행(1~3회)에서 나온 경험적 선택이다.** 실제 성능은 `prd/nav2-baseline-test-plan.md`의 15회 시험으로 확정한다.
(설정 파일의 긴 주석을 "짧은 이유 + 이 문서 링크"로 줄이는 작업은 설정 파일 수정이라 별도 승인 후 진행한다. 지금은 이력만 이쪽에 보존.)

| 파라미터 | 변경 | 날짜 | 이유 / 근거 | 관련 |
|---|---|---|---|---|
| `inflation_radius` | 0.3 → (0.15 시도, 내접 반경 경고로 거부) → 0.2 → **0.3** | 2026-10-05 | 0.3은 작은 방에서 "Start occupied". 0.15는 내접 반경(0.17)보다 작아 Nav2가 경고(비용 계산 전제 위반). 이후 플래너용 footprint를 0.40×0.48로 키우자 내접 반경 0.24가 되어 0.2도 오류 → 0.3 | troubleshooting/020 |
| `xy_goal_tolerance` | 0.1 → 0.2 → **0.15** | 2026-10-05 | 0.1은 목표 0.15 m 앞에서 "Failed to make progress"(80초+recovery 7회), 0.2는 도착점이 어긋남. 목표 근처 DWB가 모터 데드존(펌웨어 PWM ±250) 아래 속도를 낸다고 **추정**(미검증) | 028 |
| `yaw_goal_tolerance` | 0.25 → 0.5 → **0.4** | 2026-10-05 | 0.25는 미세조정 장시간, 0.5는 우회 후 20° 틀어진 채 종료 | 028 |
| `min_speed_xy` | 0.0 → **0.05** | 2026-10-05 | 모터 데드존 아래 속도 샘플 방지 (추정) | 028 |
| `max_vel_x` | 0.2 → **0.12** | 2026-10-05 | depth 감지 거리 약 0.5 m라 0.2 m/s에서는 옆으로 비킬 시간 부족 → 상자를 침 | 028 |
| `min_vel_x` | -0.2 → **0.0** | 2026-10-05 | 후방이 LiDAR·depth 모두 사각이라 후진 중 물체를 밀었다 | 022 |
| `behavior_plugins` | [spin, backup, wait] → **[spin, wait]** (+ 기본 BT XML에서 `<BackUp/>` 제거) | 2026-10-05 | BackUp recovery는 `min_vel_x`와 무관하게 후진 `cmd_vel`을 직접 낸다. 기본 BT가 backup 서버에 로드 시점에 연결하므로 BT에서도 같이 제거해야 bt_navigator가 기동 | 022 |
| `BaseObstacle.scale` | 0.02 → **0.1** | 2026-10-05 | 장애물 옆을 아슬아슬하게 지나가 상자를 침 | 028 |
| 가속 한계(DWB, velocity_smoother) | [1.0,1.0,2.0] → **[0.5,0.5,1.0]** | 2026-10-05 | 회피 동작이 "요란" | 028 |
| BT `RemovePassedGoals` radius / 재계산 주기 | 0.7 → **0.12** / 3 s → **1 Hz** | 2026-10-05~06 | 0.3 m 간격 웨이포인트가 즉시 삭제되어 직선 복귀 실패(대각선 종료) | 028, `tools/nav/line_goal.py` |
| global costmap `depth_cloud` | 없음 → **추가** (3 m) | 2026-10-05 | depth가 local에만 있으면 전역 경로가 장애물을 통과, DWB가 앞에서 멈춤 | 026 |
| collision_monitor polygon | 확대 footprint → **실제 크기 + 2~3 cm 여유** `[[0.19,0.21],…]` | 2026-10-05 | 플래너용 확대 footprint(0.40×0.48)를 쓰면 상자(+연장점)가 "안"으로 판정되어 감속/정지 | 028 |
| collision_monitor 소스 | LiDAR만 → **+depth_cloud** (min_height 작게) | 2026-10-05 | 상자가 LiDAR에 안 보여 안전망이 작동한 적이 없었다 | 028 |
| `sparse_point_cloud` `extrude_depth_m` | 0 → **0.3** | 2026-10-05 | 카메라가 앞면만 봐서 몸통이 free로 보임 (휴리스틱) | design/depth-obstacle.md |
| `background_margin_mm` | **60** | 2026-10-05 | depth 노이즈보다 큰 여유 (기준 depth 비교, 30 mm에서 상향) | 023 |
| 홈 자세 `arm_home_pose_rad` | → [0.0, -0.553, 1.688, 1.671, 0.017] | 2026-10-05 | 카메라가 자기 바퀴부터 바닥까지 끊김 없이 보이도록 | checklist 14 |

## 해석 시 주의
- 위 표의 이유 중 **"추정"** 표시는 실제로 검증되지 않았다 (특히 모터 데드존 가설).
- 값들은 서로 얽혀 있다(속도 ↔ 감지 거리 ↔ inflation ↔ footprint ↔ collision_monitor). 하나를 바꾸면 baseline이 무효가 되므로, baseline 시험 중에는 변경하지 않는다.
- 엔코더 odom 적용 후에는 목표 근처 정지 문제(데드존 가설)가 달라질 수 있어 `xy/yaw_goal_tolerance`를 다시 평가해야 한다.
