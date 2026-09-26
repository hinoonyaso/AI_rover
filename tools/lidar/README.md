# LiDAR 도구

- `check_orientation.py`: 물체를 로봇 근처에 두고 실행하면 `base_link` 기준으로 가장 가까운 물체의 방향을 출력한다
  (0° = 정면, +90° = 왼쪽). 실제 `lidar_frame → base_link` TF를 써서 URDF 장착 yaw를 끝까지 검증한다.
  LiDAR 드라이버와 `robot_state_publisher`가 떠 있어야 한다.

## 알려진 특성 (RPLIDAR A1M8, fw 1.29)
- `/scan` 약 14 Hz: 어댑터가 모터를 최대 속도로 돌려서 실제 회전이 14 Hz다 (드라이버에 속도 파라미터 없음). 각도 해상도 약 0.64°.
- 스캔 −72°~+90°(로봇 뒤쪽 약 160°)는 로봇팔 기둥/몸체에 가려 반환이 없다.
- 포트는 by-path로 지정 (`ttyUSB0/1` 번호는 재부팅마다 바뀜). `drivers/ch341/`의 모듈이 필요하다.
