# 034 — 상자 회피 시험: DWB·MPPI 모두 상자 앞에서 진행 못 함 (2026-10-09)

- 상태: **해결(MPPI 3/3 성공)**, 우회 폭 조정 진행 중 — 아래 "2026-10-09 저녁" 참고
- 관련: 031(직진/shim), 026·028(depth 장애물), `prd/nav2-mppi-ab-test-plan.md`
- 조건: 지도 lap2, 로봇 A(1.0, 0.45) → B(1.0, 1.45), 높이 약 10 cm 상자를 범퍼 앞 약 40 cm 가운데, 새 홈 자세(depth 0.26~0.81 m)

## 회차별
| 회차 | 컨트롤러/설정 | 결과 | 관찰(`tools/nav/cmd_chain_monitor.py`) | 원인 → 조치 |
|---|---|---|---|---|
| O1 | DWB, shim 매번 회전 | 60 s 시간 초과, 옆 28 cm | shim이 ±0.4 rad/s 좌우 회전 반복, collision_monitor 개입 없음 | 회피 경로 방향이 1 Hz 재계획마다 바뀜 → `rotate_to_heading_once: true` |
| O2 | DWB, shim 1회 | 시간 초과 | ±0.11 rad/s 좌우 회전만, DWB 평가 30 s에 7번 | shim이 5° 안에 못 들어가 제어권을 안 놓음(명령이 데드존 아래) → shim 시작/종료 35°/11° |
| O3 | DWB, shim 35°/11° | 시간 초과, 목표 37 cm 전 | 처음 10 s는 정면 유지·오른쪽 옆이동으로 우회(의도대로), 상자 옆에서 vy 좌우·미세 회전 반복 | (아래 M2와 같은 원인으로 추정) |
| M1 | **MPPI**(Omni) | 시간 초과 | vx 내내 0, 회전·작은 vy만 | costmap/경로 그림: **전역 경로가 상자를 관통**(global에 상자 없음), local은 LiDAR가 실제로 많이 채움 |
| M2 | MPPI + global 레이어 분리 | 시간 초과, 목표 54 cm 전, 옆 60 cm | 경로가 상자 왼쪽으로 우회, 10 s 동안 0.12 m/s로 우회 진행, 이후 상자 옆에서 vy 진동(119회) | **경로 위 최대 비용 99(inscribed)** = 통로가 footprint 폭 0.50 m에 너무 좁음 |

## 확인한 원인과 조치
1. RotationShim이 회피 중 반복 회전 → `rotate_to_heading_once: true`(목표가 바뀔 때만, Jazzy `isGoalChanged` 확인).
2. shim 종료 기준 5°를 데드존 아래 명령으로는 못 맞춤 → `angular_dist_threshold` 0.6(35°), `angular_disengage_threshold` 0.2(11°).
3. **global costmap에서 LiDAR가 depth 상자를 지움**(local은 10-07에 분리했으나 global은 한 레이어) → global도 `obstacle_layer`(scan)/`depth_layer`(depth) 분리.
   수정 후 전역 경로가 상자를 우회함을 확인.
4. collision_monitor는 5회 모두 주행 중 개입 없음(멈춤의 원인 아님).
5. local costmap을 채우는 건 대부분 LiDAR(벽·가구·사람): 정지 상태 9 s 후 LiDAR만 lethal 173칸, depth만 62칸(거의 상자). 오류가 아니라 좁은 방.

## 남은 원인 (추정)
상자 옆 통로가 플래너 footprint(0.36 × **0.50** m, 2026-10-06 여유 포함, 미실측)로는 inscribed 영역을 지나야 할 만큼 좁음.
collision_monitor 정지 영역은 실제 몸에 맞춘 0.34 × 0.39 m라 폭이 11 cm 차이. → **footprint 줄자 실측 후 재설정**, 상자 위치는 양옆 여유가 있는 곳으로.

## MPPI 첫인상 (튜닝 전, 2회)
- 계산 부하: 컨트롤러 주기 경고 0회(batch 1000, 40 steps, 10 Hz), 전체 load 5~6으로 DWB와 비슷.
- 경로가 정상일 때 0.12 m/s 전진 + 우회를 바로 시작(M2). 좁은 곳에서 vy 진동은 DWB와 비슷 → 판정은 공정 조건(같은 튜닝 예산)에서.

## 덧붙여
- `timeout 3 ros2 topic echo --once /cmd_vel`가 메시지가 없을 때 SIGTERM을 무시하고 멈춰, 같은 명령줄의 뒤 작업이 실행되지 않은 일이 있었다.
  토픽 확인은 rclpy 스크립트(시간 제한 내장)나 `timeout -s KILL`로 한다.

## 2026-10-09 저녁: 상자를 오른쪽으로 20 cm 옮겨 통로 확보 → MPPI 성공, 이후 우회 폭 줄이기
상자: 범퍼 앞 약 40 cm, 로봇 중심선 오른쪽 약 9~40 cm(겹침은 몸 반폭 기준 약 5 cm → 이상적 우회 약 10~15 cm).
| 회차 | 설정 변경 | 결과 | 시간 | 최대 횡이탈 | 몸 회전 최대 | collision_monitor |
|---|---|---|---|---|---|---|
| M3 | (MPPI, footprint 0.36×0.50, inflation 0.40, cost_scaling 5, cost_travel 4) | **성공** | 15.0 s | 40.8 cm | 53° | 개입 없음 |
| M4 | cost_scaling 5→10, cost_travel_multiplier 4→2 | **성공** | 15.8 s | 36.5 cm | 66° | 개입 없음 |
| M5 | **footprint 실측 반영** 0.36×0.50 → 0.38×0.28(실측 36×26 cm + 1 cm), 정지/감속 영역도 실측 기준 | **성공** | 17.0 s | 42.3 cm | 73° | 개입 없음 |
사용자 관찰(M3): "잘 회피했지만 쓸데없이 너무 멀리 회피한다".

M5 bag 분석: 처음 전역 경로의 최대 횡이탈은 **21 cm**(적절)였는데, 지나가는 동안 39 → 42 cm로 바깥으로 밀림.
지도 위 상자 표시는 약 35×30 cm로 실제와 비슷(오른쪽으로 8~15 cm 치우침) — 경로를 미는 것은 상자 주변 **inflation 비용 띠(0.40 m)**.
조치: footprint가 실제 크기(내접 0.14)가 됐으므로 **inflation_radius 0.40 → 0.25**(global/local). **배터리 9.97 V로 주행 확인 전 중단** — 다음 시험 1순위.
남은 관찰: 우회 중 몸을 53~73° 돌림(MPPI PathAngle mode 0이 경로 방향을 보게 함) — 정면 카메라에는 유리하지만 우회 폭을 키울 수 있음.

## 설계 결정 (2026-10-09, 사용자 요구): 회피는 정면 유지 + 대각 이동, 몸 회전은 큰 방향 전환에서만
사용자 관찰: "너무 과하게 왼쪽으로 이동 후 회피한다. 계속 정면을 보면서 메카넘이니까 스무스하게 대각주행하면서 회피하고,
아예 좌·우회전해야 하는 구간에서만 각도를 틀어야 한다."
- 근거: depth 카메라 가로 시야 약 ±41°(fx 362.5, 640 px) → 진행 방향이 몸 정면에서 40° 이내면 카메라가 진행 방향을 본다.
  회피용 대각 이동(30~40°)은 정면 유지로 충분하고, 몸을 돌리면 우회 폭도 커진다(M3~M5: 회전 53~73°, 우회 37~42 cm).
- 설정(주행 확인 전):
  - MPPI `TwirlingCritic` 10 → 30, `wz_std` 0.4 → 0.2 (회피 중 회전 억제)
  - RotationShim `rotate_to_heading_once` true → false, `angular_dist_threshold` 35° → 60°, `forward_sampling_distance` 0.3 → 0.6 m
    (코너·출발처럼 경로 전체 방향이 60° 이상 다를 때만 회전, 장애물 옆 30~45° 꺾임은 무시)
  - inflation_radius 0.25(과도한 옆 이동 대책, 위)
- 확인 지표: `straight_trial.py`의 `yaw_dev_max`(직진 구간 몸 방향 오차, 목표 < 15°)와 `lat_max`(목표 ~15~20 cm), 성공·충돌 없음.
