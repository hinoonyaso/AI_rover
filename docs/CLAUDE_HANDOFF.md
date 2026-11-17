# 작업 인수인계

이 문서는 2026-11-11 현재 `jetrover_ws`의 저장소 기록과 사용자가 제공한 이전 대화 요약으로 작성했다. 이전 환경의 `/home/sang/AI_rover`와 그곳의 원본 인수인계 문서는 현재 환경에서 찾지 못했다. 로컬에서 발견된 Claude 대화와 메모리·파일 이력은 `/home/sang/claude_backup_20261111/README.md`에 보존했다. 기록은 2026-10-07~2026-11-11(UTC) 범위이며 JSON 해석 불가 2줄이 원문에 있다. 이 범위 밖의 대화나 다른 환경의 원본까지 복구된 것은 아니다. 이 워크스페이스는 같은 Git 원격 저장소의 별도 작업 사본이다.

- 현재 진행 상태와 시험 결과: [체크리스트](../checklist/PROJECT_CHECKLIST.md), [로드맵](ROADMAP.md). 과거 요약보다 날짜가 있는 최신 기록을 우선한다.
- 자체 STM32 펌웨어는 실기에 flash·검증됐다. 추가 flash와 실기 구동에는 사용자 승인이 필요하다. 자세한 내용은 [펌웨어 README](../firmware/rrc_m4/README.md)와 [프로젝트 지침](../AGENTS.md).
- 2026-10-28 발 끼임 사고 이후 안전 대책은 미완료다. `footprint_padding` 후보의 시뮬레이션 결과는 실기 검증이 아니며 공식 적용은 결정 대기다. [체크리스트 8.16](../checklist/PROJECT_CHECKLIST.md), [사고 기록](../troubleshooting/056-depth-filter-removed-feet.md)을 확인한다.
- 정밀 접근은 costmap을 보지 않아 사람 발에 가까워질 수 있다. 경로 비용 검사는 후보이며 미결정이다. [체크리스트 9](../checklist/PROJECT_CHECKLIST.md) 참조.
- DWB/MPPI 비교는 잠정 완료, 팔 MVP는 경로 A, `ros2_control`은 이후 PoC다. [로드맵](ROADMAP.md) 참조.
- AprilTag 정렬은 초안 단계이며 사용자 결정이 남아 있다. [PRD](../prd/apriltag-alignment.md).
