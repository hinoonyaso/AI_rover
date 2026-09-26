# teleop_twist_keyboard로 조종하면 로봇이 잠깐 움직이다 멈춤
- 날짜: 2026-09-20
- 상태: 우회
- 관련: `base_node`의 `cmd_vel_timeout` 파라미터

## 증상
키를 눌러도 잠깐 움직이고 멈춘다. 로그에 `cmd_vel timeout (0.50s), stopping motors`가 찍힌다.
(명령은 정상적으로 도착한다는 뜻이다.)

## 원인
`teleop_twist_keyboard`는 키를 누를 때만 메시지를 보낸다. 키를 눌러도 OS 자동 반복이 시작되기까지
0.3~0.6초가 걸려서, 그 사이에 host watchdog(0.5초)이 명령이 끊겼다고 판단해 정지시킨다.
(STM32에는 timeout이 없으므로 이 watchdog이 유일한 정지 수단이다.)

## 해결 또는 우회
키보드 조종용으로만 timeout을 늘린다.
`ros2 run jetrover_base base_node --ros-args -p cmd_vel_timeout:=1.0`
기본값은 0.5초로 유지한다 (Nav2는 초당 20회 이상 보내므로 문제없다).

## 확인/재발 방지
`ros2 topic info /cmd_vel`로 발행자/구독자가 연결됐는지 확인한다.
