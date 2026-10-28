# PRD: Navigation BT — 한 번의 내비게이션 요청으로 "가서 정확히 맞추기" (체크리스트 9번)

- 작성: 2026-10-25. 확정: 2026-10-28(사용자 결정 3개 받음, 아래 "결정"). 신뢰 수준: **계획**.
- 관련: 실기 결과 `docs/benchmarks/navigation/real_avoid_20261025.md`(정밀 접근 + 재위치로 도착 −3~+1 cm), `src/jetrover_navigation/scripts/precise_approach.py`,
  BT `src/jetrover_navigation/config/behavior_trees/navigate_to_pose_wait_obstacle.xml`(공식 기본), troubleshooting/055.

## 목표
지금은 정확히 도착하려면 ① Nav2 `NavigateToPose` → ② 끝나면 `precise_approach` 액션을 따로 호출해야 한다(시험 도구 `run_trial.py --approach`만 그렇게 한다).
미션(17번 Mission BT)·웹 관제가 쓰기 전에 **내비게이션 요청 한 번으로** 다음이 일어나게 한다.
1. Nav2로 목표 근처까지(회피·대기 포함, 지금 공식 BT 그대로). 경로가 목표 앞에서 끊기면 성공으로 치지 않는다(아래 발견된 문제)
2. 정밀 도착이 필요한 목표면: 정지 → 스캔 매칭 재위치 → 정밀 접근(2 cm·2°)
3. 실패하면 정해진 복구(재시도/보고)

## 발견된 문제 (이 BT가 함께 풀 것)
- **목표 근처가 막히면 목표 앞에서 '성공'**(실기 D09, sim D7 2026-10-25): 사람이 목표 근처에 서 있으면 플래너가 가장 가까운 빈 곳까지만 경로를 만들고(허용 0.25 m),
  Nav2는 그 끝에서 성공을 낸다. 목표에서 28~30 cm 떨어진 채 끝나고 정밀 접근은 시작 거리 제한(0.28~0.30 m)으로 건너뛴다.
  → 경로 끝이 요청 목표에서 일정 거리(예: 10 cm) 넘게 떨어지면 성공이 아니라 대기·재계획 후 재시도, 끝내 안 되면 '목표 막힘'으로 보고.

## 범위 (제안)
- BT에 정밀 접근 단계를 넣는 방법 하나를 고른다(결정할 것 1).
- 목표마다 "정밀 도착 필요" 여부를 넘기는 방법(결정할 것 2).
- 정밀 접근이 붙은 뒤 Nav2 목표 허용 오차를 0.10/0.08에서 넓힐지 재검토(넓히면 목표 앞 진동·시간 감소, 정확도는 정밀 접근이 맡음).
- sim(정답 위치)과 실기(줄자)로 검증: 직선·상자 우회·사람 시나리오에서 정확도·시간·안전 회귀 없음.

## 비범위
- 미션 BT(17번), 음성/웹, 컨트롤러 상황별 전환(MPPI/DWB) — 필요하면 다음 PRD.
- 사람 구분(2단계 동적 대응).

## 구현 방법 후보 (결정할 것 1)
| 방법 | 내용 | 장점 | 단점 |
|---|---|---|---|
| A. C++ BT 노드 | `jetrover_nav_plugins`에 `PreciseApproach` BT 액션 노드(Nav2 `BtActionNode`) 추가, bt_navigator `plugin_lib_names`에 등록, BT XML에서 `FollowPath` 성공 뒤 실행 | Nav2 표준 방식, 취소·피드백·복구가 BT 안에서 일관 | C++ 플러그인·빌드, BT 안에서 스캔 매칭(외부 프로세스) 처리 필요 |
| B. 별도 액션 서버(파이썬) | `navigate_precise` 액션: 안에서 NavigateToPose → precise_approach를 차례로 호출 | 구현 빠름, 지금 노드 재사용 | Nav2 BT 바깥 — 복구·취소 경로가 두 군데 |
| C. 미션 쪽에서 두 번 호출 | 미션 BT가 Nav2 → precise_approach를 순서대로 | 새 코드 거의 없음 | 9번 목표(한 번의 요청)와 다름, 미션마다 반복 |

추천: **A**(체크리스트 9번 "Custom BT node" 항목과 맞고, 미션 BT가 단일 액션만 쓰면 된다). 재위치는 지금처럼 정밀 접근 노드 안에서 한다(BT 노드는 액션만 부름).

## 결정 (2026-10-28, 사용자)
1. 구현 방법: **A. C++ BT 노드**.
2. 정밀 도착 범위: **목표마다 지정**. 방법: `NavigateToPose` 목표의 `behavior_tree` 필드(Nav2 표준)로 BT 파일을 고른다 —
   비우면 기본 `navigate_to_pose_wait_obstacle.xml`(지금과 같음), 정밀 도착이 필요하면 `navigate_to_pose_precise.xml`.
   새 메시지·플래그 없이 미션/웹이 목표마다 고를 수 있다.
3. 정밀 접근 실패(시작 거리 초과·시간 초과·목표 막힘): **1회 재시도 후 실패 보고**. 재시도 = Nav2로 목표 근처까지 다시 간 뒤 정밀 접근 한 번 더.
   실패 결과에는 이유(막힘/시작 거리 초과/시간 초과)를 담는다.

## 설계 (확정, 2026-10-28 구현에서 조정)
- **BT 노드: 새 C++ 플러그인 대신 Nav2 내장 `NavigateToPose` BT 액션 노드를 쓴다.** 정밀 접근 서버가 `NavigateToPose` 액션 타입이라
  내장 노드의 `server_name="precise_approach"` 포트만 바꾸면 결정 A(BT 안의 액션 노드: 취소·피드백·재시도가 BT 안에서 일관)를 그대로 만족한다.
  bt_navigator 기본 플러그인 목록에 이미 있어 `plugin_lib_names` 등록·빌드·gtest가 필요 없다(유지할 코드 0줄).
  `jetrover_nav_plugins`에 전용 노드를 만드는 것은 이 노드로 부족한 점(예: 전용 포트)이 생길 때로 미룬다.
- `navigate_to_pose_precise.xml` = `RecoveryNode(number_of_retries=1)` 안에 `Sequence`[`navigate_to_pose_wait_obstacle.xml`의 주행 부분 복사,
  `NavigateToPose name="PreciseApproach" server_name="precise_approach"`], 재시도 전 `Wait 2 s`.
  costmap 비우기는 넣지 않았다 — 막힌 목표는 주행 부분의 자체 복구가 이미 비우고, 정밀 접근 실패 뒤 지우면 사람·상자 흔적까지 지워 안전 쪽이 나쁘다.
- 실패 이유: `precise_approach.py`가 결과 `error_code`에 9101(시작 거리 초과)/9102(시간 초과)/9103(위치 없음)을 담고,
  bt_navigator `error_code_names`에 `precise_approach_error_code`를 더해 NavigateToPose 결과로 전달한다. 막힘은 Nav2 계획기 코드(`compute_path_error_code`).
  먼 목표는 거부(이유 없음) 대신 수락 후 9101로 중단한다.
- `nav2.launch.py`가 `precise_approach.py`를 함께 띄운다(인자 `precise_approach`, 기본 true; sim은 `relocalize` false). 따로 띄우면 같은 서버가 둘이 된다.
- Nav2 목표 허용 오차(0.10/0.08)는 정밀 BT가 실기 검증된 뒤 재검토(넓히면 목표 앞 진동·시간 감소).

## 제약
- AGENTS.md 안전 규칙, 공식 설정 변경은 tuning-history 기록. 후진 금지 유지.
- 정밀 접근은 `/cmd_vel_nav`로 내므로 안전망(속도 평활기·collision_monitor) 그대로.
- 실기 시험은 사용자 입회(L4).

## 완료 기준 (제안)
- sim: 직선·S2/S4·D 시나리오 각 10회에서 한 번의 요청으로 도착 오차 ≤ 3 cm(정답), 기존 기준(간격·시간·접촉) 회귀 없음.
- 실기: 직선 3회·상자 우회 3회, 줄자 오차 ≤ 3 cm, 접촉 0.
