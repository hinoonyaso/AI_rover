# 053. 동적 장애물 시뮬레이션 준비: 옮긴 모델이 LiDAR에서 안 사라짐, 지나간 장애물 흔적이 코스트맵에 남음, 끊긴 시험의 잔여 프로세스

체크리스트 8.16 1번(2026-10-22). 도구: `tools/sim/dyn_obstacles.py`, `tools/sim/check_dyn_obstacles.py`.

## 1. 사람 모델을 옮겨도 LiDAR 값이 그대로
- 증상: `set_pose`로 `person_0`을 로봇 앞에 놓고 숨겨도 LiDAR 정면 거리가 숨기기 전후로 같았다. `gz model -p`의 위치는 바뀌어 있었다.
- 원인(확인): 숨기는 위치를 **바닥 아래(z = −5)**로 둔 것. 처음부터 앞에 둔 모델은 잘 보였고, 앞으로 옮기는 것도 반영됐지만 바닥 아래로 보낸 뒤에도 LiDAR에 계속 남았다.
  (처음엔 static 모델의 렌더링 미반영을 의심해 일반 모델 + 중력 끔으로 바꿨는데, 그것만으로는 해결되지 않았다.)
- 해결: 방 밖 바닥 위 (8, 8)에 세워 둔다. 놓기·숨기기·4 cm 단위 이동이 모두 LiDAR에 바로 반영됨. 모델은 일반 모델 + 중력 끔(놓은 자리에 머묾, Gazebo 정답 토픽에도 나옴).

## 2. 지나간 장애물의 흔적이 local 코스트맵에 계속 남음
- 증상: 사람(D1)·낮은 상자(D3)가 로봇 앞을 지나간 뒤 6 s가 지나도 경로 위 칸이 80~154칸 표시돼 있었다.
- 원인(코드와 시험으로 확인): `sparse_point_cloud.py`는 기준 깊이보다 가까운 **장애물 점만** 보낸다. Nav2 ObstacleLayer의 지우기는 관측된 점까지 광선을 긋는데,
  장애물이 떠나면 보낼 점이 없어 지울 광선도 없다. depth `clearing: true/false`가 정지 상자 시험에서 차이가 작았던 것도 같은 이유로 보인다(추정).
- 해결: `sparse_point_cloud.py`에 `publish_clearing`(기본 false) — 기준과 margin 안으로 같은 픽셀(빈 바닥)을 `depth/points_clear`로 보낸다.
  sim launch가 켜고(`SIM_DEPTH_CLEARING`, 기본 1), sim 변형 `nav2_params_dyn_clr.yaml`의 depth 레이어에 `depth_clear`(marking false, clearing true,
  `min_obstacle_height -0.2` — launch의 −0.1→0.09 치환을 피해 바닥 점을 받음)를 추가했다. 실기 설정은 그대로.
- 결과: 흔적 D1 80 → 3칸, D3 154 → 0칸(즉시). 남은 3칸은 로봇 중심에서 0.76~0.78 m — 카메라가 바닥을 보는 끝 너머(장애물 점을 시선 뒤로 25 cm 늘린 부분)라
  지울 광선이 닿지 않는다. 로봇이 다가가면 시야에 들어와 지워질 것으로 추정(8.16 3단계에서 확인).

## 3. `timeout`으로 끊은 시험이 Gazebo·Nav2·브리지를 남김 → 다음 실행의 Nav2가 안 뜸
- 증상: `map_server: Unable to start transition 1 from current state active`, `Failed to bring up all requested nodes`. 확인해 보니 이전 실행의 Gazebo·Nav2와 `set_pose` 브리지 7개가 남아 있었다.
- 원인: 바깥 `timeout`이 래퍼 bash만 죽여서 정리 단계가 돌지 않았고, 브리지는 `ros2 run` 래퍼 PID만 종료해 실제 브리지가 남았다. 같은 ROS 도메인에 같은 이름의 노드가 생겨 lifecycle이 꼬였다.
- 해결(`tools/sim/sim_avoid_run.sh`): 정리를 `trap cleanup EXIT`로 묶고, 시험을 서브셸 백그라운드 + `wait`로 돌려 신호를 바로 처리, 브리지를 프로세스 그룹으로 종료,
  시작할 때 남은 Gazebo/Nav2/브리지가 있으면 중단. 확인: `timeout 120`으로 끊은 뒤 남은 프로세스 0.

## 확인 방법
`RUNCMD="python3 tools/sim/check_dyn_obstacles.py" PARAMS=tools/nav/ab_params/nav2_params_dyn_clr.yaml bash tools/sim/sim_avoid_run.sh`
→ D1/D3 속도 오차, 감지 비율, 경로 위 흔적 칸 수와 지워진 시간. 깊이 점은 광학 프레임이라 3D 변환이 필요하다(2D yaw만 쓰면 점이 로봇 앞에 몰려 보임 — 도구 오류로 0/8을 낸 적 있음).
