# 실기 시험 절차: 정지 상자 회피(8.15 6번) + 사람 대응(8.16 6번)

- 작성 2026-10-25. 신뢰 수준: **계획**. 레벨 **L4(바닥 주행)**, 사용자 입회 필수(전원 스위치 옆).
- 근거: sim 결과 `docs/benchmarks/sim/avoidance_precision_20261020.md`, `docs/benchmarks/sim/dynamic_obstacles_20261022.md`.
- 실기 설정 파일은 시험용 변형으로만 쓰고 **공식 `nav2_params.yaml`은 바꾸지 않는다**(결과를 보고 따로 결정).

## 0. 준비 (시험 전 확인)
- [ ] 배터리 ≥ 11.0 V(시작 전 `/battery` 확인). 10 V 미만이면 중단·충전.
- [ ] 바퀴·팔: 팔 홈 자세(깊이 장애물 게이트가 열려야 함), 바퀴 주변 이물질 없음.
- [ ] 시험 구역(2026-10-25 사용자 결정): **지금 로봇이 놓인 자리를 출발점으로** 바닥 테이프 표시, 상자는 로봇 정면 0.5 m(경로 가운데).
  목표는 출발 방향으로 B 1.30 m / D 1.00 m 앞(`run_trial.py --start X Y YAW`가 계산). 정면 약 1.6 m·좌우 각 0.5 m가 비어 있어야 한다(LiDAR로 확인).
  출발 좌표는 로봇을 켜고 스캔 매칭(`scan_match_init.py`)으로 한 번 재서 아래 명령의 X Y YAW에 넣는다. 들어서 옮기면 바퀴가 안 돌아
  AMCL이 모르므로, 회차마다 같은 테이프 위에 놓고 `run_trial.py`가 시작할 때 스캔 매칭으로 확인한다(15 cm / 10° 넘으면 다시 놓기).
  자리를 처음 표시할 때는 `python3 tools/nav/start_guide.py X Y YAW`로 어긋난 정도를 볼 수 있다.
- [ ] 상자: 신발 상자(높이 약 12 cm, LiDAR에 안 보임) — 이전 B 시험과 같은 것.
- [ ] 로봇 앞뒤 1 m에 다른 물체 없음. 사람 시험 때 걸어갈 사람 1명(로봇을 향해 달려오지 않는다).

## 1. 실행 (Jetson, 터미널마다 `source ~/jetrover_ws/install/setup.bash`)
```bash
# 1) 베이스 + LiDAR + EKF
ros2 launch jetrover_bringup robot.launch.py
# 2) 카메라: 지우기 전용 바닥 점 켬 + 상자 두께에 맞춘 연장 0.25 m (기본값은 끔 / 0.15 m), 시험 중엔 colorizer 끔
ros2 launch jetrover_perception camera.launch.py colorizer:=false depth_publish_clearing:=true depth_extrude_m:=0.25
# 3) Nav2 + AMCL, 시험용 변형
ros2 launch jetrover_navigation nav2.launch.py params_file:=$HOME/jetrover_ws/tools/nav/ab_params/nav2_params_real_test.yaml
# 4) 정밀 접근 노드
ros2 run jetrover_navigation precise_approach.py
```
- `nav2_params_real_test.yaml` = sim 최종 설정(정지 영역은 2절 결정에 따름). sim 전용 값(깊이 margin 100 mm, 최소 높이 0.09 m)은 launch에서만 바뀌므로 들어가 있지 않다.
- 시작 직후 확인(로봇 정지 상태, L2): `ros2 topic hz /depth_cam/depth/points_clear`(약 7 Hz), 컨트롤러 경고 없음, RViz에 정지 영역이 로봇 몸 주변에서 비어 있음
  (정지 영역 안에 로봇 자신이 잡히면 출발하지 못한다 — 녹화 분석으로는 A·C 시험 0점, B는 벽 옆에서만 잡힘).

## 2. 정지 영역 선택 (sim 비교, 2026-10-25) → **B' `DirStop` 사용**
| sim 시나리오 | A안 `TallStop` (사방 12·앞 16 cm) | B' `DirStop` (앞으로: 앞 16·옆 6 cm, 옆으로: 그쪽 12 cm, 나머지 2 cm) |
|---|---|---|
| 좁은 통로 0.50 m (LiDAR에 보이는 벽 사이) | **0/3** (통로 앞에서 30 s 정지) | 3/3, 벽까지 7~9 cm |
| 좁은 통로 0.60 m | **0/3** | (B안 3/3) |
| D5 사람이 옆에서 와 바로 앞을 가로지름 | 11.1 cm 이상 | **7.3~10.4 cm (평균 9.0)** |
| D6 사람이 경로 위에 서 있음 | 13.2 cm 이상 | 10.0 cm 이상 |
| S4 정지 상자 (B안) | - | 8/8, 4.7~6.6 cm |
- A안은 통로·벽 옆에서 멈춰 실기 B(동쪽 벽까지 몸 옆 약 11 cm, 녹화 `/scan` 분석)에 못 쓴다. B'는 통과하지만 D5 간격이 10 cm 기준에 조금 못 미친다
  (접촉 0, 몸 + 2 cm 비상 정지 영역은 그대로).
- 실기 사람 시험에서 간격을 특히 눈여겨보고, 부족하면 B'의 앞 영역 옆을 더 넓힐지 결정한다.
- Jetson 부하(녹화 재생 `tools/nav/replay_load.sh`): 컨트롤러 CPU 공식 설정 31 % → 시험 변형 45 %(코어 1개 기준), 10 Hz 미달 경고 0.

## 3. 시험 순서
| 순서 | 시험 | 횟수 | 명령 | 사람 판정 |
|---|---|---|---|---|
| 1 | B 상자 우회 | 5 | `python3 tools/nav/benchmark/run_trial.py B <n> --tag real_avoid --approach --start X Y YAW` | 상자 닿음·밀림, 우회 중 벽 근처 정지 여부, 최종 위치 줄자 |
| 2 | 사람 가로지르기 (D 직선 1 m) | 5 | `python3 tools/nav/benchmark/run_trial.py D <n> --tag real_person --approach --start X Y YAW` 시작 후 약 2 s에 로봇 앞 약 0.5 m를 보통 걸음으로 가로지름 | 로봇이 멈췄는지, 사람과 가장 가까울 때 간격(눈대중 10 cm 이상?), 지나간 뒤 다시 출발했는지 |
| 3 | 사람이 경로 위에 서 있다 물러남 (D) | 3 | 위와 같음, 로봇 앞 약 0.5 m에 4 s 서 있다가 왔던 쪽으로 물러남 | 멈춰서 기다렸는지, 간격, 재출발 |
- 회차 사이: 로봇을 출발 테이프로 옮기고(사람이 들어서), 상자 위치 확인. `run_trial.py`가 시작할 때 스캔 매칭으로 출발 위치를 확인한다.
- **중단 조건**: 상자·사람·벽에 닿음, 로봇이 멈추지 않음, STM32 silent, 배터리 < 10.5 V → 전원 스위치 / Ctrl+C(도구가 취소 + 정지 명령).

## 4. 통과 기준 (체크리스트 8.15/8.16 6번)
- B: 성공 ≥ 4/5, 충돌 0(사람 확인), 위치 오차는 줄자.
- 사람: 접촉 0, 멈춘 뒤 재출발. 간격은 사람이 눈대중(정답 기록 없음 — bag의 `/scan`으로 사후 확인).

## 5. 기록
- bag + `meta.json`: `bags/real_avoid/`, `bags/real_person/`. 판정은 `set_meta.py`.
- 결과 문서: `docs/benchmarks/navigation/real_avoid_<날짜>.md`, 체크리스트 8.15/8.16 6번, 문제는 troubleshooting.

## 6. 결과 (2026-10-25)
- `docs/benchmarks/navigation/real_avoid_20261025.md`: B 5/5 접촉 0, 사람 가로지르기 5회 접촉 0(매번 정지 후 재출발). 시험 중 depth 최소 높이를 0.06 m로 바꿈(B03부터). 문제 기록 troubleshooting/055.
- 사람 시험 안내는 "로봇 바퀴가 움직이기 시작하면 걷기"로 해야 타이밍이 맞는다.

