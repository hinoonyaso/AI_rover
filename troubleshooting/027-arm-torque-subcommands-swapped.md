# 027 — 로봇팔 토크 ON/OFF 서브커맨드가 호스트 코드에서 뒤집혀 있었음 (해결, 2026-10-05)

## 증상
`arm/torque` 토픽으로 "OFF"를 보내도 팔이 안 풀려서 손으로 못 움직였다(RST를 눌러도 마찬가지). 서보 상태 읽기는 "OFF 후 1"이었다.

## 원인
`rrc_protocol.hpp`가 `kRrcBusServoSubTorqueOn=0x0B / Off=0x0C`로 정의했는데(공식 `board.cpp`의 `enable ? 0x0B : 0x0C`를 따름),
**실물은 0x0B = 토크 해제(limp), 0x0C = 토크 걸기(load)**였다. 공식 PDF 텍스트("0x0B unload, 0x0C load")와 서보 프로토콜(`LOAD_OR_UNLOAD`: 1=loaded)과도 일치한다.
상태 읽기(0x0D)의 값도 **1 = 걸림, 0 = 풀림**이다(이전 체크리스트의 "1=힘빠짐"은 반대였음).
이전 코드가 큰 문제 없이 동작한 이유: "ON"이 사실 해제였고, 그 뒤 보내는 hold 이동 명령이 서보를 걸면서 현재 위치로 목표를 덮어써서 우연히 안전했다.

## 해결
- `rrc_protocol.hpp`: On=0x0C, Off=0x0B로 수정(실기 확인 주석).
- `base_node.cpp::set_arm_torque`: 걸 때는 **hold 이동을 먼저**(옛 목표값으로 튀지 않게) 보내고 그 뒤 0x0C. 해제는 0x0B.
- 새 펌웨어(`lib/core/bus_servo.c`)는 PDF대로 0x0B=unload였으므로 맞았고, 0x0D(토크 상태 읽기)를 추가하고 시험을 보강했다.
- 진단 도구: `tools/stm32_diagnostics/arm_torque_probe.py`(상태 읽기/ON/OFF), `arm_pos_watch.py`(위치 샘플링).

## 확인
`python3 tools/stm32_diagnostics/arm_torque_probe.py off`(base_node 정지 상태) 후 팔이 손으로 움직이고 상태가 0인지.
