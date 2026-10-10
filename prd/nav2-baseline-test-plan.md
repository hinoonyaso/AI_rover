# TEST_PLAN: Nav2 baseline (open-loop odom, depth 장애물 회피) — 15회

작성 2026-10-06. 이 파일은 원격 저장소에서 빈 파일(0바이트)이었다. `docs/ROADMAP.md`가 "15회", `tools/nav/benchmark/`가 시나리오 `A|B|C`를
가정하고 있어 그 틀에 맞춰 **새로 정의**했다(이전에 의도한 정의가 따로 있었다면 이 문서를 고친다).

## 목적
엔코더 odom 도입(`prd/encoder-odometry.md`) **이전**의 기준 성능을 같은 조건으로 15회 재서 Before/After 표의 "Before"로 쓴다.
태그: `baseline_openloop`. 결과: `docs/benchmarks/navigation/baseline_openloop.{csv,md}`.

## 고정 조건 (시험 중 바꾸지 않는다)
- 지도 `maps/lap2_20261005`, 시작 자세 S = map (1.05, 0.10), yaw 90°(+y 전방). 시험마다 사람이 로봇을 S에 놓고 `/initialpose`로 AMCL을 맞춘다.
- 로봇팔: 주행용 홈 자세(`base.yaml arm_home_pose_rad`, 토크 걸림). 기준 depth `depth_background_ref.npy`는 이 자세용.
- Nav2 설정: `nav2_params.yaml` 현재값(DWB 0.12 m/s, 가속 0.5, footprint 0.40×0.48, 안전망 polygon 실제 크기, 허용 오차 0.15 m/0.4 rad).
- 배터리 ≥ 10.5 V(시작 시 기록). 10 V 미만이면 중단하고 충전. 불필요한 노드(웹 비디오, RViz 과다)는 끈다(CPU 과부하 방지, troubleshooting/028).

## 시나리오 (각 5회)
| ID | 내용 | 목표 | 장애물 | 이동 방법 |
|---|---|---|---|---|
| A | 직선 전진 1.0 m | (1.05, 1.10), yaw 90° | 없음 | `tools/nav/line_goal.py` (직선 웨이포인트) |
| B | 상자 1개 우회 후 직선 복귀 | (1.05, 1.40), yaw 90° | 상자를 S 앞 약 0.5 m, 경로 중앙 | ~~`line_goal.py`~~ **NavigateToPose**(2026-10-10: 직선 경유점 하나가 상자 안에 찍혀 경로 실패 → 변경, 직선 복귀는 최종 좌우 이탈로 판정) |
| C | 대각 이동 + 90° 회전 | (0.50, 0.80), yaw 180° | 없음 | `NavigateToPose` |

상자: 신발 상자(높이 약 0.12 m, LiDAR에 안 보임, depth로만 보임). 시험마다 같은 위치에 다시 놓는다(바닥에 테이프 표시 권장).

## 기록 / 판정
- 절차 자동화: `tools/nav/benchmark/run_trial.py` (rosbag + `meta.json` 틀 + 자동 판정 항목). 사람 판정은 충돌 여부와 줄자 실측.
- **사람이 판정**: 충돌(상자나 벽에 닿았는가, 상자가 밀렸는가), 선택적으로 줄자/각도기로 `measured_final`. AMCL 자기 자세는 독립 정답이 아니다.
- **자동 판정**: 액션 결과(SUCCEEDED/ABORTED), 소요 시간, recovery 횟수, AMCL 최종 자세, B의 선 이탈 최대값/최종값.

## 통과 기준 (시험 1회)
1. 액션 결과 SUCCEEDED, 60 s 이내.
2. 충돌 없음(상자 이동도 충돌로 본다).
3. 최종 위치 오차 ≤ 0.15 m, yaw 오차 ≤ 0.4 rad.
4. B만: 최종 선 이탈 |x − 1.05| ≤ 0.10 m (원래 직선으로 복귀).
한 항목이라도 어기면 fail. 전체 판정은 "성공률(15회 중), 시나리오별 성공률, 평균 소요시간, 평균 recovery, B 우회폭".

## 완료 기준 (이 시험 자체)
1. 15회 기록(rosbag + meta.json)이 `bags/baseline_openloop/`에 있다(bag은 Git 추적 제외).
2. `analyze.py` 결과 CSV/Markdown이 `docs/benchmarks/navigation/`에 있다.
3. 시험 중 이상(과부하, STM32 침묵, 배터리)은 `troubleshooting/`에 기록한다.
4. 체크리스트 8.9/8.10과 `docs/ROADMAP.md` 1번을 실제 수치로 갱신한다.

## 안전
- 사람이 전원 스위치 옆에서 지켜본다. 이상하면 즉시 전원 스위치를 내린다.
- 한 번에 한 목표만 보낸다. 시험이 끝나면 목표 취소/정지를 확인한다(`finally`).

## 분석 도구 실제 bag 검증 (2026-10-10)
`analyze.py`를 실기 bag 4개(F2 MPPI 왕복, `bags/wobble/F2_*`, meta.json은 경로 끝점을 목표로 임시 작성)에 돌려
`straight_trial.py`가 주행 중 TF로 잰 값과 비교했다.

| 회차 | 시간 analyze / trial [s] | 목표 오차, 마지막 /amcl_pose [cm] | 목표 오차, /tf [cm] | trial [cm] |
|---|---|---|---|---|
| F2-1 | 8.9 / 8.9 | 18.1 | 12.7 | 15.3 |
| F2-2 | 18.0 / 18.1 | 20.3 | 13.2 | 12.1 |
| F2-3 | 19.0 / 19.1 | 16.5 | 15.3 | 15.6 |
| F2-4(실패) | 60.0 / 60.0 | 51.5 | 44.5 | 44.0 |

- 시간·성공률·CTE 계산과 mcap bag 읽기는 정상.
- **고침**: 마지막 `/amcl_pose`는 AMCL이 일정 거리/각도 움직여야만 내므로 정지 위치보다 늦어 오차를 3~8 cm 키웠다 →
  bag의 `/tf`(마지막 map→odom × odom→base_footprint)를 우선 사용(`ground_truth` = `tf`), 없을 때만 AMCL.
  단위시험 추가(`compose2d`, 합성 bag의 /tf 경로). 남은 1~3 cm 차이는 임시 meta의 목표(경로 끝점, 격자 반올림) 때문.
- `record_trial.sh`/`run_trial.py`는 이미 `/tf`를 녹화한다(확인함).

## 2026-10-10 개정 (E6 v2) — 출발 초기화와 실측 기준
v1 14회(`bags/e6_command|e6_encoder`, `docs/benchmarks/navigation/e6_interim_20261010.md`)에서 오차가 odom이 아니라 위치 추정에 지배됨을 확인해 바꿨다.
- 출발: `run_trial.py`가 AMCL을 명목 S로 강제하지 않고, 출발 표시 위의 로봇을 **스캔 매칭**(`scan_match_init.py --near S`)으로 찾아 초기화.
  S에서 15 cm / 10° 넘게 벗어나면 다시 놓는다(`--nominal-start`로 예전 동작).
- 실측: 줄자(앞/좌) + **최종 방향**을 실제 출발 위치(스캔 매칭) 기준으로 지도 좌표화(`set_measured.py`).
- 시험 전 costmap 비우기, 통로 점검(`check_clear.py`), 경로 끝 잘림 무효 판정, B는 NavigateToPose — v1 중간에 넣은 것 유지.
- 태그 `e6v2_command` / `e6v2_encoder`, 30회 전부 새로(조건 번갈아).
