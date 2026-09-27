# LiDAR USB가 운영 중 재연결되고 rplidar_composition이 스스로 복구 안 됨
- 날짜: 2026-09-28
- 상태: 우회 (재시작으로 회복, 근본 원인/재발 방지는 미해결)
- 관련: `journalctl -k`, `rplidar_composition`, `jetrover_bringup/config/lidar.yaml`, `troubleshooting/012-ch341-module-missing.md`

## 증상
`robot.launch.py`(base+EKF+LiDAR)를 띄우고 약 30분 뒤, AMCL(`localization.launch.py`) 시험 중
`/scan`이 완전히 끊겼다. `rplidar_composition` 프로세스는 살아있고 에러 로그도 없었으며,
`ros2 topic info /scan`은 publisher가 있다고 보고했지만 실제로는 3초간 0개 메시지(직접 rclpy로
QoS 맞춰 재확인해도 0개). 사용자가 확인한 바로는 **LiDAR는 물리적으로 계속 돌고 있었다**(모터 정지 아님).

## 원인
`journalctl -k`로 확인: 00:43:54에 LiDAR용 CH340 어댑터가 USB disconnect 후 새 장치 번호로
재열거됐다(`ttyUSB0` → `ttyUSB2`).
```
ch341-uart ttyUSB0: usb_serial_generic_read_bulk_callback - urb stopped: -32
usb 1-2.1.4: USB disconnect, device number 9
ch341-uart ttyUSB0: ch341-uart converter now disconnected from ttyUSB0
usb 1-2.1.4: new full-speed USB device number 15 using tegra-xusb
ch341-uart converter now attached to ttyUSB2
```
`/dev/serial/by-path/...` 심링크는 커널이 즉시 새 장치(`ttyUSB2`)로 갱신했지만,
**이미 실행 중이던 `rplidar_composition`은 launch 시점에 연 파일 디스크립터(옛 `ttyUSB0`)를 계속
붙잡고 있어서 재연결을 못 했다.** `base_node`에는 "Serial 자동 reconnect" 기능이 있지만
(`checklist/PROJECT_CHECKLIST.md` 1번 섹션), **`rplidar_ros`(rplidar_composition)에는 이런 기능이 없다.**
USB 재연결 자체의 근본 원인(전원 불안정, 케이블, 허브 등)은 확인하지 못했다.

## 해결 또는 우회
`robot.launch.py`(정확히는 rplidar_composition 노드)를 재시작하면 새 by-path 심링크(현재 장치)로
다시 열려서 즉시 복구된다. 이번엔 전체 launch를 재시작했다(개별 노드만 재시작하는 방법은 안 써봄).

## 확인/재발 방지
- `/scan`이 갑자기 멈추면(특히 `ros2 topic info`엔 publisher가 있다고 나오는데 실제 메시지가 안 오면)
  `journalctl -k --since "-10min" | grep -i usb`로 재연결 여부부터 확인한다.
- **`ros2 topic hz`/`ros2 topic echo --once`는 QoS가 안 맞으면(예: publisher가 `BEST_EFFORT`나
  `TRANSIENT_LOCAL`인데 도구 쪽 기본 QoS가 안 맞으면) 조용히 아무것도 안 받고 끝난다** — 이번에
  `/scan`(BEST_EFFORT)과 `/amcl_pose`(TRANSIENT_LOCAL) 둘 다 이 문제로 헷갈렸다. 진단할 땐
  `rclpy`로 직접 QoS를 맞춰서(`ros2 topic info -v`로 실제 publisher QoS 확인 후) 구독하는 게 확실하다.
- 근본 원인(왜 재연결됐는지)과 `rplidar_ros`에 자동 재연결을 추가할지는 아직 결정 안 함 —
  자주 재발하면 `checklist/PROJECT_CHECKLIST.md`의 "장시간 USB 안정성 시험" 항목에서 계속 관찰한다.
