# Nav2 첫 통합 launch: 설정 오류 3개 + 재시도 중 좀비 프로세스 누적
- 날짜: 2026-10-04
- 상태: 해결
- 관련: `src/jetrover_navigation/config/nav2_params.yaml`, `src/jetrover_navigation/launch/nav2.launch.py`, `nav2_bringup/launch/navigation_launch.py`

## 증상
`ros2 launch jetrover_navigation nav2.launch.py`(map_server+amcl + nav2_bringup의
`navigation_launch.py`)를 처음 띄웠을 때 `lifecycle_manager_navigation`이 매번 "Failed to bring up
all requested nodes"로 중단됐다. 고치고 재시도하길 4번 반복했는데, **마지막엔 `ros2 node list`에
`route_server`/`waypoint_follower`가 4개씩 중복으로 떴다**("share an exact name" 경고).

## 원인
세 가지가 섞여 있었다.

1. **설정 오타**: `GridBased.plugin`을 `"nav2_smac_planner/SmacPlanner2D"`(ROS1식 `package/Class`)로
   썼는데, pluginlib이 실제로 요구하는 건 `"nav2_smac_planner::SmacPlanner2D"`(C++ 네임스페이스 `::`).
   에러 메시지 자체가 정확한 등록된 타입 목록을 보여줘서 바로 잡았다.
2. **`nav2_bringup`의 `navigation_launch.py`가 생각보다 많은 노드를 기본으로 띄운다**: 이 프로젝트가
   처음에 염두에 둔 건 controller/planner/bt_navigator/behavior_server뿐이었는데, 실제로는
   `collision_monitor`, `docking_server`, `route_server`, `smoother_server`(경로 스무딩, velocity
   smoother와는 다른 노드), `waypoint_follower`까지 `lifecycle_nodes` 목록에 **하드코딩**되어 있어서
   꺼지는 launch 인자가 없다. `collision_monitor`/`docking_server`는 yaml에 파라미터가 아예 없어서
   lifecycle configure 자체가 실패했다 — `nav2_bringup/params/nav2_params.yaml`(apt로 설치된 공식
   예시)의 해당 섹션을 그대로 가져와 메꿨다(`docking_server`는 실제 충전 도크가 없어서 lifecycle만
   통과시키는 플레이스홀더).
3. **재시도할 때마다 이전 시도의 프로세스를 다 못 죽였다**: `pgrep -af "map_server|amcl|controller_server|...`
   처럼 내가 떠올린 이름만 패턴에 넣고 죽였는데, `route_server`/`waypoint_follower`는 그 패턴에
   없어서 매 실패마다 좀비로 남았다. 4번 실패하는 동안 4세대가 겹쳐 쌓였다.

## 해결 또는 우회
- 플러그인 이름을 `::`로 수정.
- `collision_monitor`/`docking_server` 섹션을 `nav2_bringup`의 공식 예시(`/opt/ros/jazzy/share/nav2_bringup/params/nav2_params.yaml`)에서
  그대로 가져와 `nav2_params.yaml`에 추가.
- 좀비 정리는 `pgrep`에 미리 짐작한 이름 목록을 쓰지 말고, **`ros2 node list`로 실제 떠 있는 노드를
  먼저 보고 거기 나온 이름으로 `pgrep -af`를 다시 돌려서** 전부 찾아 죽였다.

## 확인/재발 방지
- `nav2_bringup`의 `navigation_launch.py`를 쓸 땐 **그 파일의 `lifecycle_nodes` 리스트를 먼저
  읽고**(`$(ros2 pkg prefix nav2_bringup)/share/nav2_bringup/launch/navigation_launch.py`) 뭐가
  딸려오는지 미리 확인한다 — 지금(Jazzy) 기준: `controller_server, smoother_server, planner_server,
  behavior_server, bt_navigator, bt_navigator_navigator_...(내부), waypoint_follower, velocity_smoother,
  collision_monitor, docking_server, route_server`.
- Nav2처럼 **노드가 많은 launch를 재시도할 때는 `pgrep` 패턴을 미리 정해두지 말고, 매번
  `ros2 node list`로 실제 그래프를 먼저 확인**한다(troubleshooting/004의 "시험용 프로세스 확인"
  원칙을 다중 프로세스 launch에도 그대로 적용).
- 설정 안 한 노드가 있는지 미리 알고 싶으면 launch 전에 `ros2 launch <pkg> <file> --show-args`나
  소스를 먼저 읽는다.
