# 052. 상자 간격이 가끔 3 cm 안팎, ObstacleFootprint로 바꾸자 5 s 정지 반복, 상자 옆에서 내내 절반 속도

## 증상 (Gazebo, S2/S4, 2026-10-20~21)
1. 1차 최종(BaseObstacle) 40회 중 12회가 상자 간격 5 cm 미만(최소 2.6 cm). 접촉은 0회.
2. ObstacleFootprint로 바꾸자 간격은 해결됐지만 상자 옆에서 약 5 s씩 서는 일이 반복돼 S4가 30~37 s.
3. 정지를 없앤 뒤에도 B 출발(S4BA)이 느려 25 s를 넘는 시행이 남음.

## 원인 (데이터로 확인)
1. 12회 전부 **몸 뒤쪽 모서리**가, 로봇 중심이 상자 중심을 0.27~0.34 m 지나 경로로 복귀할 때 상자에 가장 가까워졌다. 그때 몸은 진행 방향보다 항상 −8°
   (출발 자세가 경로와 8° 어긋나고 Twirling 30이 회전을 억제해 유지됨) → 뒤 모서리가 약 2.3 cm 상자 쪽으로 나옴. Smac2D와 BaseObstacle은 로봇을 중심 한 점(원)으로만 본다.
2. Nav2 로그: `No valid trajectories ... ObstacleFootprint/Trajectory Hits Obstacle` → `[follow_path] Aborting handle` → `Running wait`.
   한 주기만 전부 무효여도 controller `failure_tolerance`(기본 0)가 0이라 FollowPath가 중단되고, BT(`navigate_to_pose_no_backup.xml`)가 1 s 재시도 후 5 s 대기했다.
   (이 BT는 복구 때 코스트맵을 비우지 않는다 — 2026-10-06 결정.) 5 cm 격자에서는 상자 칸이 실제보다 최대 3~4 cm 커 보여 무효 판정이 잦았다.
3. collision_monitor `FootprintSlow`(몸 + 약 10 cm, 속도 50%)가 계획 간격(6~10 cm)을 덮어, 상자 옆을 정상적으로 지나는 동안 내내 감속(B 출발 7~14 s).
   DWB(LimitedAccel)는 실제 속도 근처에서만 후보를 고르므로 감속이 계속 이어졌다. 시행 시간과 감속 시간이 같이 움직였다.

## 해결 (sim 시험용 변형 `tools/nav/ab_params/nav2_params_sim_avoid.yaml`, 실기 설정 불변)
1. DWB 평가자 BaseObstacle → **ObstacleFootprint**(scale 0.02).
2. controller_server **`failure_tolerance: 1.0`**, local 코스트맵 **해상도 0.025**, local footprint 여유 0.03(global 0.05 유지).
3. collision_monitor `FootprintSlow` **몸 + 약 5 cm**(`[[0.23, 0.18], ...]`, 목표 간격과 같음). `FootprintStop`(몸 + 2 cm)은 그대로.
결과(왕복 10회씩): S2 20/20·S4 20/20, 간격 최소 5.7 / 4.9 cm, 시간 최대 13.4 / 21.3 s, 정지 0 s.
`docs/benchmarks/sim/avoidance_precision_20261020.md` 1·3절.

## 확인·재발 방지
- 간격이 모자라면 먼저 "어느 모서리가, 경로의 어느 구간에서" 닿는지 정답 궤적으로 본다(이번엔 12회 전부 같은 패턴이었다).
- 상자 옆 정지는 Nav2 로그의 `No valid trajectories`/`Running wait`와 collision_monitor 상태(시행 JSON `collision_monitor`)부터 본다.
- 실기 적용 전: 감속 영역 축소는 실기 안전 여유를 줄이고, 해상도 2.5 cm는 Jetson 컨트롤러 부하를 늘린다. 실기 B 시험과 컨트롤러 주기 확인이 필요하다.
