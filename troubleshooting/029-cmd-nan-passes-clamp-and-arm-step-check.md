# 029 — NaN/Inf 명령이 `std::clamp`와 팔 step 검사를 통과한다 (코드 리뷰로 발견, 수정됨)

- 날짜: 2026-10-06
- 상태: 해결 (L0 — 단위시험 통과, **실기 미검증**)
- 관련: `src/jetrover_base/src/base_node.cpp`, `include/jetrover_base/command_guard.hpp`, `test/test_command_guard.cpp`

## 증상 (이론적 구멍, 실제 사고는 없었다)
`/cmd_vel`에 NaN이 들어오면 `std::clamp(NaN, lo, hi)`는 NaN을 그대로 돌려주므로 `mecanum_inverse` → 바퀴 rps NaN → RRC 모터 패킷으로 나갈 수 있었다.
vendor 펌웨어가 NaN을 어떻게 처리하는지는 **확인된 적이 없다**(자체 펌웨어에는 NaN 처리 코드가 있다).
`arm/command`도 같다: `std::abs(NaN - cur) > arm_max_step_rad`는 NaN 비교라서 **거짓** → step 가드를 통과하고, `round(NaN)`의 정수 변환은 정의되지 않은 동작(UB)이다.

## 원인
입력 검증 없이 clamp/비교에만 의존했다. NaN은 모든 비교가 거짓이라 "범위 검사"류 가드를 조용히 통과한다.

## 해결
- `decide_cmd_vel()`(순수 함수): clamp **전에** NaN/Inf를 거부하고 모터를 정지.
- STM32 침묵 중 0이 아닌 명령도 거부(저장 안 함 → 복구 직후 옛 명령이 되살아나지 않음). 0 명령은 허용.
- `arm/command`: `all_finite(position)` 실패 시 전체 거부(기존 atomic reject 구조 유지).
- 시작 시 파라미터 검증(`validate_base_params`/`validate_arm_params`): 0/음수/NaN, 서보 부호 ±1 아님, pulse 범위 역전 등은 노드 기동을 거부(exit 1).
- 단위시험 11개: NaN/Inf 각 필드, clamp가 NaN을 못 거른다는 사실 자체, 침묵 중 거부/0 허용, 파라미터 경계.

## 확인·재발 방지
- 실기 확인 필요(L3, 바퀴 띄움, 사용자 입회): NaN `cmd_vel`을 보내도 바퀴가 안 도는지, 잘못된 파라미터로 기동 시 즉시 종료되는지.
- 앞으로 범위 검사는 `!(x <= max)` 형태이거나 finite 검사를 먼저 둔다.
