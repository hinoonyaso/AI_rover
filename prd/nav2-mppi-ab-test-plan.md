# TEST_PLAN: DWB vs MPPI A/B (Nav2 컨트롤러 비교)

신뢰 수준: **계획**. 선행: Nav2 baseline(`prd/nav2-baseline-test-plan.md`) + 엔코더 odom 재시험(`prd/encoder-odometry-test-plan.md` E6).
`prd/slam-nav2.md`는 MPPI를 "최종 단계"로 미뤄 뒀는데, DWB 세부 튜닝의 ROI가 줄었으므로 **엔코더 적용 후 같은 환경에서 비교**하는 것으로 앞당긴다
(`prd/jetinspect-m-pipelines.md` 3절 "초기 DWB, 최종 MPPI"와 일관됨).

## 공정성 규칙
- **독립 변수는 컨트롤러 하나**: 지도, 시나리오(A/B/C 15회), odom(encoder_ekf), costmap/inflation/collision_monitor, 속도 한계(max 0.12 m/s 등)를 동일하게.
- **튜닝 예산을 같게**: 각 컨트롤러에 동일한 튜닝 횟수(예: 3회 반복)만 허용하고, 최종 파라미터를 고정한 뒤 15회 측정. "한쪽만 많이 튜닝"을 막는다.
- MPPI는 메카넘이므로 `Omni` 모션 모델 사용. 시작점은 nav2 기본 예제값, 변경 내역을 `docs/benchmarks/navigation/tuning-history.md`에 기록.
- 후진 금지·BackUp 제거 등 안전 제약은 양쪽 동일 유지 (후방 사각지대, troubleshooting/022).

## 지표
baseline 7개(Success, Collision, Goal pos/yaw 오차, CTE RMS, 시간, Recovery) + 추가:
| 추가 지표 | 측정 |
|---|---|
| 경로 길이 | `analyze.py`의 `path_len_m` |
| 컨트롤러 계산 지연/주기 | Nav2 로그 또는 `/controller_server` 진단 (측정 방법은 첫 시험에서 확정) |
| CPU 사용률 | `top`/`pidstat` 또는 tegrastats (Orin Nano 8GB, GNOME 데스크톱 동시 구동 주의 — 부하가 크면 TF timeout, troubleshooting/028) |
| 속도 프로파일 | `/cmd_vel` bag (진동/요란함 정량화: 가속도 RMS 등) |

## 판정
수치표로 비교하고, **개선뿐 아니라 악화/동률도 그대로 기록**한다. 결론은 "MPPI가 항상 낫다"가 아니라 "이 환경·센서·odom 조건에서 어느 쪽이 어떤 지표에 강한가"로 쓴다.
CPU 예산 초과(다른 노드 지연 유발)는 성공률이 같아도 감점 요소로 별도 표기.

## 실행 방식 (2026-10-11 확정)
E6 v2(2026-10-11, `docs/benchmarks/navigation/e6v2_20261011.md`)가 끝나 선행 단계가 충족됐다. 엔코더 odom은 `wheel_twist_source: auto`(실제로는 엔코더)가 기본값이다.
- **DWB 쪽은 새로 재지 않고 E6 v2의 encoder 15회(`bags/e6v2_encoder`, 시나리오 A/B/C 각 5회)를 그대로 쓴다.** 같은 날, 같은 지도·odom·costmap·속도 한계(0.12 m/s)·기본 `nav2_params.yaml`(RotationShim + DWB LimitedAccel). 바뀌는 건 컨트롤러 하나.
- **MPPI**: `tools/nav/ab_params/make_variants.sh`가 만드는 `nav2_params_mppi.yaml`(RotationShim 유지 + MPPI Omni, `config/mppi_followpath.yaml`: 샘플 1000, 40스텝, vx/vy 0.12, wz 0.4, LateralRatioCritic 포함). 측정 중 파라미터를 바꾸지 않는다(튜닝 예산은 2026-10-09~10에 양쪽 모두 소진한 것으로 본다).
- 태그 `ab_mppi`, 시나리오 A/B/C 각 5회(총 15회). 최종 자세는 **스캔 매칭**(`set_measured_scan.py`)으로 잰다. A는 E6 v2에서 줄자로 쟀으므로 MPPI A는 **줄자와 스캔 매칭을 둘 다** 남겨 두 방법의 차이를 확인한다(방법이 다른 데서 오는 편향 분리).
- CPU: `tegrastats --interval 500 --logfile Log/ab_mppi_<시나리오>.tegra`를 블록마다 켠다(sudo 불필요). 속도 프로파일은 bag의 `/cmd_vel` 가속도 RMS와 명령 각도 > 50° 시간 비율.
- 한계: DWB 쪽은 오전·MPPI는 오후라 배터리(12.0 → 11.6 V)와 서보 발열 차이가 끼어든다. MPPI와 DWB 결과가 애매하게 겹치면 DWB를 나중에 5회 더 재서 순서 효과를 본다.

## 상태
- [~] 2026-10-11 착수: DWB 기준(E6 v2 encoder 15회) 확보, MPPI 15회 진행 예정.
