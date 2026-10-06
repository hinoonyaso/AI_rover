# docs/ — 설계·로드맵·사례·벤치마크

| 문서 | 내용 |
|---|---|
| [ROADMAP.md](ROADMAP.md) | **재정렬된 개발 순서**, 단계별 게이트(통과 조건), MVP 범위, 하드웨어 의존성 |
| [architecture.md](architecture.md) | 시스템 구조 (Current vs Target), TF 트리, odometry 파이프라인, 하드웨어 추상화 방향 |
| [design/depth-obstacle.md](design/depth-obstacle.md) | RGB-D 근거리 장애물 처리: 현재 방식(임시), 한계, 목표 방식, 검증 항목 |
| [case-studies/nav-depth-obstacle.md](case-studies/nav-depth-obstacle.md) | Failure → Root Cause → Fix 사례 (의자 충돌 → depth costmap), 포트폴리오용 |
| [benchmarks/navigation/tuning-history.md](benchmarks/navigation/tuning-history.md) | `nav2_params.yaml`의 파라미터별 튜닝 이력 (설정 파일 주석에서 분리 예정분) |
| `benchmarks/navigation/*.md/csv` | Nav2 baseline 결과 (시험 후 생성, 계획: [prd/nav2-baseline-test-plan.md](../prd/nav2-baseline-test-plan.md)) |

다른 문서 위치: PRD/시험 계획 `prd/`, 진행 체크리스트 `checklist/`, 오류 기록 `troubleshooting/`, 환경 설치 기록 `setup/`.
신뢰 수준 표기(확정/추정/계획/폐기)는 `AGENTS.md`의 규칙을 그대로 쓴다. 이 폴더의 문서에서 **측정하지 않은 수치는 "목표" 또는 "미측정"으로 표기**한다.
