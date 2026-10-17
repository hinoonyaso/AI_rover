# 041 — 팔 서보 위치 읽기가 범위 밖(펄스 −16)인데 그대로 /joint_states에 나감 (2026-10-15)

- 상태: **방어 추가(2026-10-17)** — 범위 밖 위치는 버림. 원인(서보 3이 왜 −16을 보냈는지)은 미확인
- 관련: `src/jetrover_base/src/rrc_protocol.cpp` `decode_bus_servo_position`, `src/base_node.cpp` 위치 응답 처리, T6 L2(`docs/benchmarks/arm_grasp_l2_faults_20261015.md`)

## 증상
robot.launch 시작 직후 `/joint_states`의 joint3이 **2.161 rad**로 3번(약 10 s) 같은 값. 홈은 1.663, 스캔 후 홈 복귀 때 1.667이었다.
2.161 rad는 펄스 약 **−16**(서보 범위 0~1000 밖). 약 15분 뒤 같은 관절이 1.667(펄스 103)로 읽혔다. 그 사이 joint3에 보낸 명령은 없다
(`on_arm_command`는 메시지에 이름이 있는 관절만 보내고, 이 시간에는 `r_joint`만 보냈다; 보정 재명령도 명령한 관절만).
`arm/servo_stats`: 서보 3의 실패 응답 8회(다른 서보 2회 안팎).

## 추정 원인
서보 3이 한 번 잘못된 위치(−16)를 성공 응답으로 돌려주고, 이어진 응답이 실패(success ≠ 0)라 값이 갱신되지 않고 남았다.
버스 서보는 범위 끝을 넘으면 음수를 보고할 수도 있어 "실제로 그 자세였다"를 완전히 배제하지는 못한다(사용자 육안 확인 없음).

## 위험
`decode_bus_servo_position`/base_node가 범위 밖 펄스를 그대로 저장한다 → 그 관절의 `arm/command`는 잘못된 현재값 기준으로 스텝 제한을 판정하고,
MoveIt/브리지·트림이 틀린 자세를 믿는다. 이번에는 joint3을 움직이지 않아 영향 없음.

## 조치 (2026-10-17)
- base_node: 위치 응답이 `arm_reading_min..arm_reading_max`(0..1000) 밖이면 **버린다**(관절 값·파지 입력 미반영), `ServoStats::record_invalid`로
  요청은 끝내되 읽기로 치지 않음 → `arm/servo_stats`에 `invalid_replies`, `age_s`는 마지막 유효 응답부터 계속 늘어남(브리지 신선도 1.5 s가 막음).
  경고는 5 s에 한 번.
- 확인: 단위 시험 1개(`InvalidPositionEndsTheRequestButIsNotAReading`), jetrover_base 197/197. L1 가짜 장치에서 서보 3이 −16을 3 s 보내는 동안
  joint3 값 그대로(1.676), invalid 10, age 3.05 s → 정상 값(103)으로 돌아오자 1.663, age 0.15 s. 파지 L1 22/22.

## 제안 (나머지, 미적용)
- 한 관절의 마지막 유효 응답이 오래되면(`age_s`) 그 관절 명령을 거부(브리지의 신선도 검사와 같은 기준).
- 재현되면 시작 직후 서보별 원시 응답(펄스, success)을 기록해 원인 확정.
