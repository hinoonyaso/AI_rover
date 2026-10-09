# TEST_PLAN: MPPI LateralRatioCritic

| Parent Task | 레벨 | 통과 기준 |
|---|---|---|
| 1. critic 계산 함수 + 단위시험 | L0 | 45°/slack 경계, 초과량 선형, vx<0 → 전진 0 취급, 배치×시간 텐서 합산·model_dt 곱 확인 |
| 2. 플러그인 패키지/등록 | L0 | `colcon build/test` 통과, MPPI가 `Critic loaded : jetrover_nav_plugins::LateralRatioCritic` 로그 |
| 3. 실기 회피(상자 오른쪽 20 cm, 범퍼 앞 ~35 cm) | L5 | 왕복 4회: 성공 ≥ 3, 명령 각도 > 50° 시간 비율 < 5%(vx > 0.03), 최대 옆 속도·우회 시작 지점을 이전(F2 시리즈)과 비교, 상자 접촉 0. 배터리 ≥ 10.3 V에서 시작 |

## 측정 방법 (2026-10-10 추가)
- "명령 각도 > 50° 시간 비율" = `diag50_frac`(`tools/nav/trial_metrics.py`): `/cmd_vel_nav` 중 속도 ≥ 0.03 m/s인 명령에서
  `atan2(|vy|, vx) > 50°`의 비율(순수 옆이동 90°, 후진 > 90°). 제자리 회전·정지는 제외. `straight_trial.py`가 v3 CSV에 기록.
- 실기 전에 시뮬레이션에서 A/B: `tools/sim/run_scenarios.sh`(S2 = 3번 시험과 같은 좌표, S3 = F2-4 정체 지점),
  `mppi` vs `mppi_nolr`(이 critic만 끔). 기준은 `tools/sim/README.md`.
