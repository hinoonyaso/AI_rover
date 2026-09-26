# rclpy: Twist에 정수를 넣으면 assertion으로 프로세스가 죽음
- 날짜: 2026-09-20
- 상태: 해결
- 관련: `tools/stm32_diagnostics/odom_raw_test.py`

## 증상
```
python3: .../geometry_msgs/msg/_vector3_s.c:67: ... Assertion `PyFloat_Check(field)' failed.
Aborted (core dumped)
```
Python 예외가 아니라 프로세스가 abort된다. 이때 같이 띄운 자식 프로세스(`base_node`)가 남았다 (004 참고).

## 원인
`Twist.linear.x = 0`처럼 **정수**를 넣었다. 메시지 필드는 float만 받고, C 확장이 assert로 죽는다.

## 해결 또는 우회
메시지에 값을 넣을 때 `float(...)`로 감싼다 (`t.linear.x = float(vx)`).

## 확인/재발 방지
시험 스크립트의 `finally`에서 자식 프로세스를 정리한다. abort 뒤에는 `pgrep -ax base_node`로 남은 노드를 확인한다.
