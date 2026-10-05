# Nav2 반복 주행이 매번 같은 지점에서 "Start occupied"로 막힘 — 실제론 의자였고, inflation_radius가 안전 최소값 미만이었음
- 날짜: 2026-10-05
- 상태: 해결
- 관련: `src/jetrover_navigation/config/nav2_params.yaml`, `src/jetrover_navigation/launch/{localization,nav2}.launch.py`, `maps/lap2_20261005.*`

## 증상
1m 앞으로 가는 간단한 `NavigateToPose`를 3번 연속 보냈는데, 매번 거의 같은 지점(x≈0.6~0.7m)에서
`planner_server: GridBased plugin failed to plan from (...): "Start occupied"` → recovery(spin/
backup/wait) 반복 → `Failed to make progress` → 결국 goal 실패로 끝났다.

## 원인 조사 과정
1. 로컬 costmap을 직접 찍어보니(`/local_costmap/costmap` OccupancyGrid 값 조회) 로봇이 서 있는
   정확한 셀 자체는 비어있었지만, 몇 칸(10~15cm) 옆에 `inflation_radius: 0.3` 설정으로 인한 높은
   코스트(80~99) 구역이 로봇 풋프린트(약 0.16~0.18m)와 겹쳤다 — 1차로 `inflation_radius`를 0.15로
   낮춰봄.
2. 재시도해도 또 막힘. 이번엔 로봇 중심에서 대각선 15~20cm 거리에 **실제 lethal(99) 셀**이 있었다 —
   즉 안전 여유가 아니라 진짜 장애물 코스트였다. 사용자가 로봇을 들어서 원래 시작 위치로 옮기고
   `/initialpose`로 재설정 후 다시 시도 → **같은 지점에서 또 막힘** (3번째).
3. 매번 같은 물리적 지점에서 막히는 걸 보고 사용자가 "그냥 맵 다시 그리자"고 결정. SLAM Toolbox로
   재매핑하면서 그 지점을 다시 스캔했는데도 지워지지 않아서 "고양이가 지나가다 생긴 유령
   장애물인가" 의심했으나, **확인 결과 실제 의자였다** — 즉 기존 지도(`lap1_20260922`)도 같은
   의자를 정확히 잡고 있었던 것이고, "Start occupied"는 버그가 아니라 **로봇이 실제로 그 의자에
   너무 가깝게 접근하는 경로였다는 뜻**이었다.
4. 새 지도로 Nav2를 다시 띄우자 `controller_server`/`planner_server`가 ERROR 로그를 띄움:
   `"The configured inflation radius (0.150) is smaller than the computed inscribed radius (0.170)
   of your footprint, it is highly recommended to set inflation radius to be at least as big as
   the inscribed radius to avoid collisions"` — 1차로 낮췄던 0.15가 **로봇 풋프린트의 inscribed
   radius(0.17)보다 작아서 Nav2 자체 코스트 계산(inscribed/circumscribed 임계값)이 깨지는 안전
   문제**였다.

## 해결
- `inflation_radius`를 0.3 → **0.2**로 조정(global/local costmap 둘 다). 0.15는 Nav2가 직접
  "안전하지 않다"고 경고하는 값이라 썼으면 안 됐다 — **inflation_radius는 항상 풋프린트의 inscribed
  radius 이상**이어야 한다는 걸 이번에 배움.
- 방을 SLAM Toolbox로 다시 돌아서(`ros2 launch jetrover_navigation slam.launch.py`,
  `teleop_twist_keyboard`로 수동 주행) `maps/lap2_20261005.*`로 저장. 의자를 포함해 실제 방
  배치를 정확히 반영. `localization.launch.py`/`nav2.launch.py`의 기본 맵 경로를 이걸로 변경.
- `/slam_toolbox/save_map`(.pgm/.yaml) + `/slam_toolbox/serialize_map`(.data/.posegraph) 둘 다
  호출해서 기존 `lap1_20260922`와 같은 형태(나중에 SLAM 이어서 하거나 지도만 쓰거나 둘 다 가능)로
  저장함.

## 확인/재발 방지
- costmap에서 "Start occupied"/"Failed to make progress"가 **같은 물리적 지점에서 반복**되면,
  설정값 의심보다 **그 지점에 실제로 뭐가 있는지 먼저 눈으로 확인**한다 — 이번처럼 소프트웨어
  버그가 아니라 실제 가구였을 수 있다.
- `inflation_radius`를 낮출 때는 Nav2의 자체 ERROR 로그("smaller than the computed inscribed
  radius")를 반드시 확인한다 — 경고가 뜨면 그 값은 쓰면 안 된다. 풋프린트의 inscribed radius는
  `nav2_costmap_2d`가 기동 시 계산해서 보여주므로, costmap 노드 시작 로그를 보면 알 수 있다.
- SLAM 재매핑 중 "지워지지 않는 장애물 흔적"을 보면 먼저 **실제로 거기 물건이 있는지부터 확인**한다
  (동적 장애물 유령 자국 vs 진짜 가구를 혼동하기 쉽다 — 이번에도 처음엔 잘못 판단했다).
- 지도 파일은 `lap<N>_<날짜>` 네이밍, `.pgm`/`.yaml`(map_server용) + `.data`/`.posegraph`
  (slam_toolbox 재개용) + `_preview.png`(빠른 육안 확인용) 4종 세트로 저장하는 걸 관례로 유지한다.
