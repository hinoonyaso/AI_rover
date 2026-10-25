# Gazebo 동적 장애물 대응 (반응형, 멈추고 기다리기) — 결과와 최종 설정 (2026-10-22)

PRD `prd/sim-dynamic-avoidance.md`, 시험 계획 `prd/sim-dynamic-avoidance-test-plan.md`, 체크리스트 8.16.
host Gazebo(정답 = gz 모델 자세), 장애물은 `tools/sim/dyn_obstacles.py`가 `set_pose`로 움직인다(사람 = 다리 원 두 개 r 6 cm + 몸통, 낮은 상자 33×22×11 cm).
최종 설정은 시험용 변형 `tools/nav/ab_params/nav2_params_sim_dyn.yaml`이다. **실기 설정은 바꾸지 않았다.**

## 1. 최종 결과 (`Log/sim_avoid/dynfin_*.json`, 정밀 접근 포함, 각 10회 — S2·S4는 왕복 20회)
로봇 A (1.02, 0.30, 83°) → B (1.00, 1.25). 판정: 접촉 0, 장애물 간격 ≥ 10 cm(D4는 정지 상자 기준 ≥ 5 cm), 도착 오차 ≤ 5 cm,
재출발(장애물이 로봇 앞 통로를 벗어난 뒤 0.03 m/s까지) ≤ 2 s, D4는 대기 ≤ 5 s(+0.5 s 여유) 뒤 회피 도착.

| 시나리오 | 모든 기준 동시 만족 | 접촉 | 장애물 최소 간격 | 재출발 최대 | 대기 평균 | 시간 평균 / 최대 |
|---|---|---|---|---|---|---|
| D1 사람이 앞 0.6 m를 0.5 m/s로 가로지름 | 10/10 | 0 | 24.8 cm | 1.4 s | 1.0 s | 13.6 / 15.0 s |
| D2 사람이 정면에서 다가오다 비켜 지나감 | 10/10 | 0 | 34.8 cm | - | 0.1 s | 12.8 / 13.2 s |
| D3 낮은 상자가 0.3 m/s로 가로지름(LiDAR에 안 보임) | 10/10 | 0 | 35.9 cm | 0.1 s | 2.2 s | 15.2 / 15.7 s |
| D4 앞 경로에 상자가 갑자기 나타나 그대로 있음 | **9/10** | 0 | **4.8 cm** (기준 5) | - | 5.1 s | 25.0 / 26.4 s |
| D5 사람이 바로 앞(중심 약 0.4 m)을 0.3 m/s로 가로지름 | 10/10 | 0 | 11.1 cm | 1.8 s | 3.9 s | 17.1 / 18.8 s |
| D6 사람이 경로 위에 4 s 서 있다가 물러남 | 10/10 | 0 | 13.2 cm | 0.1 s | 7.1 s | 20.1 / 20.8 s |

정지 상자 회귀(같은 설정): S1 10/10, S2 20/20(간격 최소 5.3 cm), S4 18/20(간격 4.6·4.9 cm 2회 — 8.15 최종과 같은 수준). 도착 오차는 모두 ≤ 1.9 cm.
판정: 계획서 기준 "≥ 9/10" **달성**(D4 9/10, S4 18/20). D5/D6은 baseline에서 D1~D3이 너무 쉬워 추가한 시나리오다(아래 2절).

## 2. baseline과 바뀐 점 (현재 설정 = 8.15 최종 + depth 지우기 관측원)
| 시나리오 | baseline | 최종 |
|---|---|---|
| D1~D3 | 10/10씩, 간격 12~33 cm, **정지 0회** — 장애물이 0.6 m 넘게 앞에서 먼저 지나가 '멈추고 기다리기'가 시험되지 않음 | 같은 수준 + D5/D6 추가 |
| D4 | 간격 2.4~4.4 cm, 기다리지 않고 바로 비켜 감 | 간격 4.8~6.5 cm, 약 5 s 대기 뒤 회피 |
| D5 (추가) | 간격 5.7~6.7 cm (사람에게 정지 상자처럼 붙음) | 11.1 cm 이상 |
| D6 (추가, 퇴장 방향 수정 후) | 간격 9.4~10.9 cm | 13.2 cm 이상, 재출발 0.1 s |

## 3. 가설별 시험 (각 6~8회, 채택/폐기)
| # | 변경 | 결과 | 판정 |
|---|---|---|---|
| H1 | BT `PathLongerOnApproach`(경로 1.1배 이상 길어지면 주행 취소 + 5 s 대기) — Nav2 goal_patience BT와 같은 방식 | D4에 대기가 생김. 단 9~14 s(두 번 트리거), 지나가는 상자에도 5 s를 다 채워 재출발 2.1 s | 채택 후 H5에서 조정 |
| H2 | collision_monitor `approach`(1 s 안에 닿으면 감속) | 사람 간격 5.7~7.1 cm, 개선 없음 | 폐기 |
| H3 | collision_monitor `TallStop`: LiDAR 전용 정지 영역, 몸 + 12 cm (`sources_names: [scan]`) | D6 11.3~11.8 cm, D5 7.9~9.0 cm | 채택 |
| (진단) | depth 지우기 관측원 유무로 S4 | 있음 3.0~5.4 cm / 없음 5.4~6.7 cm → 2D 지우기가 낮은 상자를 지움 | → H4 |
| H4 | depth 레이어 ObstacleLayer → **VoxelLayer**(z 5 cm × 10) | S4 간격 회복(평균 5.3 cm), 흔적 지움 유지 | 채택 |
| H4f | `TallStop` 앞쪽만 몸 + 16 cm | D5 11.3~12.1 cm | 채택 |
| H5 | BT 1.1 → 1.2배, 대기 5 → 3 s | D3 재출발 0.1~0.5 s. D4는 몸이 85~87° 도는 3회에서 대기 6~10 s·간격 3.9 cm | 채택 |
| H6 | RotationShim `angular_dist_threshold` 1.4 → 1.65(약 95°) | D4 회전 없음, 간격 5.4~7.0, 대기 3.0~5.2 s. S2/S4 회귀 없음 | 채택 |

## 4. 최종 설정 요약 (`nav2_params_sim_dyn.yaml` 머리말에도 있음)
- 8.15 최종(`nav2_params_sim_avoid.yaml`) 위에:
- depth 레이어 VoxelLayer + 지우기 전용 관측원 `depth_clear`(`sparse_point_cloud.py publish_clearing`, sim launch만 켬)
- BT `src/jetrover_navigation/config/behavior_trees/navigate_to_pose_wait_obstacle.xml`(PathLongerOnApproach 1.2배, 3 s 대기)
- collision_monitor `TallStop`(LiDAR만, 몸 + 앞 16 / 옆·뒤 12 cm, 정지)
- RotationShim `angular_dist_threshold` 1.65

## 5. 재현
```bash
# host, 저장소 루트. sim launch가 SIM_DEPTH_CLEARING=1(기본)로 지우기 점을 보낸다.
VARIANTS="sim_dyn" SCENS="dyn S1 S2 S4" REPEATS=10 bash tools/sim/run_variants.sh > /tmp/log 2>&1
# 장애물 시뮬레이션 자체 확인(속도·감지·흔적 지움)
RUNCMD="python3 tools/sim/check_dyn_obstacles.py" PARAMS=tools/nav/ab_params/nav2_params_sim_dyn.yaml bash tools/sim/sim_avoid_run.sh
python3 tools/sim/avoid_trials.py summary --prefix dynfin
```

## 6. 한계와 다음 일
- **실기 미검증**. 특히 `TallStop`은 벽·가구에도 12~16 cm 안으로 못 들어가게 하므로 좁은 통로 통과를 막을 수 있다(sim 방에서는 문제없었음). VoxelLayer는 Jetson 부하 확인 필요.
- 반응형이라 예측은 없다. 로봇보다 빠르게 로봇 쪽으로 오는 장애물, 옆·뒤에서 오는 낮은 물체(깊이 카메라는 정면만)는 범위 밖.
- 장애물 모델은 위치만 옮기는 방식이라 로봇을 피하지 않는다. 시나리오가 사람을 로봇 쪽으로 걷게 하면 '접촉'이 나오는데 로봇 잘못이 아니다(D6 첫 설계, troubleshooting/054). `dyn_contact_moving`으로 구분한다.
- 카메라 바닥 시야 끝(약 0.76 m) 너머로 늘린 장애물 점은 지울 광선이 없어 몇 칸 남는다(053). 로봇이 다가가면 지워진다.
- D4 기준(간격 ≥ 5 cm)은 정지 상자 기준을 적용한 해석이다(PRD의 10 cm는 움직이는 장애물 기준).

## 7. 실기 준비 (2026-10-25)
- 실기 B 녹화(`bags/ab_mppi/trial_B01`, `bags/e6v2_encoder/trial_B02`)의 `/scan`을 로봇 기준으로 바꿔 보니 `TallStop` 안에 로봇 자신은 0점이지만,
  상자를 오른쪽으로 돌 때 동쪽 벽이 몸 옆 약 11 cm에 들어와 3 s 동안 6~27점 → 실기에서 벽 옆 정지 위험.
- sim 좁은 통로(N50/N60, `dyn_obstacles.py`): `TallStop` 0/6 통과, 방향별 `DirStop` 6/6. `DirStop`의 앞 영역 옆을 +2 → +6 cm로 넓힌 B'로
  D5 사람 간격 평균 7.3 → 9.0 cm(아직 10 cm 미만), D6 10 cm 이상 유지. 실기 시험 변형 `tools/nav/ab_params/nav2_params_real_test.yaml` = sim 최종 + B'.
- Jetson 부하(녹화 재생 `tools/nav/replay_load.sh`, 25 s): 컨트롤러 CPU 공식 31 % / sim 최종 48 % / 실기 시험 변형 45 %(코어 1개 기준), 제어 주기 경고 0.
  재생에는 카메라 드라이버·지우기 점이 없으니 실기 L2에서 다시 본다.
- 절차서 `prd/real-avoidance-test-procedure.md`.
