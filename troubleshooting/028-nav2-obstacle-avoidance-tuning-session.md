# 028 — depth 장애물(상자) 회피 시험: 멈춤/충돌/대각선 종료 해결 과정 (2026-10-05~06)

LiDAR가 못 보는 낮은 상자를 depth 포인트클라우드로 피해 직선 경로로 복귀하는 시험에서 나온 문제와 원인/조치. 관련: 021, 023, 026, 027.

| 증상 | 원인 | 조치 |
|---|---|---|
| 상자 앞에서 멈춤 | depth가 local costmap에만 있어 전역 경로가 상자를 통과 (026) | global costmap obstacle_layer에도 depth_cloud |
| 상자를 침(정면) | ① 카메라는 앞면만 봄 → 몸통은 free ② 감지 0.5 m인데 0.2 m/s로는 옆으로 비킬 시간 부족 ③ collision_monitor가 depth를 안 봄 ④ BaseObstacle 가중치 0.02 | ① `sparse_point_cloud` `extrude_depth_m=0.3` ② `max_vel_x` 0.12 ③ collision_monitor에 depth 소스 ④ 0.1 |
| 회피가 "요란" | 가속 한계 큼(1.0/1.0/2.0) | 0.5/0.5/1.0 (DWB + velocity_smoother) |
| 목표 0.15 m 앞에서 항상 멈춤 | 목표 근처 저속(모터 데드존 추정) + 좁은 허용 오차 | `min_speed_xy` 0.05, xy 허용 0.15, yaw 0.4 (0.1/0.25는 80초+recovery 7회로 더 나빴음) |
| 직선으로 복귀 못 함, 대각선으로 끝남 | BT `RemovePassedGoals radius=0.7`이 0.3 m 간격 웨이포인트를 즉시 삭제, 재계산 3초 간격 | radius 0.12, 재계산 1 Hz, `tools/nav/line_goal.py`(직선 웨이포인트) |
| RViz로 보내면 이동 중 멈춤 | **collision_monitor가 플래너용 확대 footprint(0.40×0.48)를 써서 상자(+연장 점)를 "안"으로 판단 → 감속/정지** | 안전망 polygon을 실제 크기+여유 `[[0.19,0.21],...]`로 고정 |
| inflation 경고 | footprint 확대(내접 0.24) > inflation 0.2 | inflation 0.3 |

## 기타
- CPU 과부하(load 10+)에서 TF 조회/플래너가 timeout: 웹 비디오 서버·depth 컬러라이저를 끄면 해소. 시험 중에는 불필요한 노드를 띄우지 않는다.
- Nav2 재시작 시 이전 프로세스가 남으면 노드 이름이 중복돼 lifecycle 활성화가 실패한다: `/proc/*/exe`로 `nav2_*`를 모두 종료 → `ros2 daemon stop/start` → 재실행. AMCL 초기 위치는 재시작마다 (0,0,0)이므로 `/initialpose`를 다시 보낸다.
- 새 홈 자세/기준 depth/margin 60 mm: 체크리스트 8.12 참고. 팔 토크 서브커맨드는 027.
- **남은 한계**: 감지 범위가 앞 18~51 cm뿐이라 빠른 속도 회피는 불가(0.12 m/s로 제한). 박스 앞면만 보이는 문제는 연장 점으로 근사한 것(실제 깊이는 모름). 반복 시험 횟수가 적다(성공 정량화는 8.9/8.10에서 계속).
