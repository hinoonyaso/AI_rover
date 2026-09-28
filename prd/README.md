# PRD / TEST_PLAN (3-File System의 1번째·3번째 파일)

이 프로젝트는 Ryan Carson 방식의 "3-File System"(PRD 생성 → Task 분해 → Task 순차 실행)에
로봇 프로젝트라 하드웨어 통합 시험 비중이 큰 걸 반영해 **TEST_PLAN**을 더한 4파일 구조를 쓴다:
`AGENTS.md`(전체 규칙) + `prd/<슬러그>.md`(PRD) + `checklist/PROJECT_CHECKLIST.md`(Task) +
`prd/<슬러그>-test-plan.md`(TEST_PLAN). 자세한 실행 규칙은 `AGENTS.md`의 "새 기능 작업 방식" 참고.
여기는 PRD와 TEST_PLAN 파일만 모아둔다.

## 언제 쓰나
`checklist/PROJECT_CHECKLIST.md`의 새 섹션을 시작하거나, 기존 섹션 중 규모가 큰 항목을 처음
착수할 때. 오탈자 수정이나 한두 줄짜리 작업에는 안 쓴다 — 이미 한 일(예: STM32 hang 조사,
UART1 부트로더 검증)처럼 대화하면서 자연스럽게 풀리는 조사/디버깅 작업에도 강제하지 않는다.
**계획 자체가 크고 사용자와 범위를 먼저 맞춰야 하는 새 기능"**에 쓴다(예: Voice AI, MoveIt2 통합).

## 파일명
`prd/<슬러그>.md` (예: `prd/voice-ai.md`). 슬러그는 `checklist/PROJECT_CHECKLIST.md`의 해당
섹션 제목과 대응시킨다.

## 만드는 순서
1. 요구사항이 애매하면 먼저 사용자에게 **명확화 질문**을 한다(범위, 비범위, 제약, 완료 기준).
   추측으로 채우지 않는다.
2. 아래 틀로 PRD를 쓴다.
3. PRD 승인 후, `checklist/PROJECT_CHECKLIST.md`의 해당 섹션을 **parent task + sub-task**로
   다시 쓴다(2번째 파일 = Task 목록. 새 파일을 만들지 않고 기존 체크리스트를 그 역할로 쓴다 —
   진행 상황을 두 군데서 따로 관리하면 어긋난다는 걸 이미 겪었다: `troubleshooting/`와
   `checklist/`가 어긋났던 사례가 있었음).
4. `prd/<슬러그>-test-plan.md`를 쓴다: 그 parent task들마다 AGENTS.md "테스트 레벨과 완료 기준"의
   L0~L5 중 어느 레벨까지 필요한지, 실제 통과 기준(수치/재현 조건)이 뭔지 적는다. 하드웨어가
   얽힌 항목(모터·팔 등)은 L2~L4의 안전 규칙(바퀴 띄우기, 전원 스위치 옆 대기 등)을 그대로 적용한다.
5. 실행은 AGENTS.md의 규칙대로 **한 sub-task씩** 한다.

## TEST_PLAN 틀
```markdown
# TEST_PLAN: <기능 이름>

| Parent Task | 필요 레벨(L0~L5) | 통과 기준 |
|---|---|---|
| 1. ... | L1 (가상 시리얼/시뮬레이션) | ... |
| 2. ... | L3 (바퀴 띄운 모터 시험) | ... |
```

## PRD 틀
```markdown
# PRD: <기능 이름>

## 목표
(이 기능이 왜 필요한가, 어떤 문제를 푸는가)

## 범위
- (포함하는 것)

## 비범위 (지금은 안 하는 것)
- (제외하는 것 — 나중 단계로 미루는 것 포함)

## 제약
- AGENTS.md의 안전 규칙, 확정된 사실과 충돌하지 않아야 함
- (하드웨어 한계, 의존 패키지, 이 기능만의 제약)

## 완료 기준
(체크리스트를 `[x]`로 바꾸는 기준 — AGENTS.md의 공통 기준에 이 기능만의 구체적 기준을 더한다)
```
