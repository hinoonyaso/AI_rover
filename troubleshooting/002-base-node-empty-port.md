# base_node가 `Cannot open serial: open : No such file or directory`
- 날짜: 2026-09-20
- 상태: 해결
- 관련: `src/jetrover_base/src/base_node.cpp`, `config/base.yaml`

## 증상
`ros2 run jetrover_base base_node` 실행 시 2초마다 `Cannot open serial: open : No such file or directory`.
경로가 빈 문자열로 출력됐다.

## 원인
`port` 파라미터의 코드 기본값이 빈 문자열이었고, 실제 경로는 `base.yaml`에만 있었다.
yaml은 `--params-file`로 넘길 때만 적용되므로 그냥 실행하면 빈 경로를 열었다.

## 해결 또는 우회
- 코드 기본값을 `/dev/serial/by-id/usb-1a86_USB_Single_Serial_596F003889-if00`으로 바꿨다.
- `base.launch.py`를 추가해서 `ros2 launch jetrover_base base.launch.py`로 실행하면 yaml이 항상 적용된다.

## 확인/재발 방지
설정이 필요한 노드는 launch로 실행한다. 새 터미널에서는 `source ~/jetrover_ws/install/setup.bash`를 먼저 한다.
