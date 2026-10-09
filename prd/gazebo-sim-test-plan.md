# TEST_PLAN: JetRover Gazebo 시뮬레이션

| Parent Task | 레벨 | 통과 기준 |
|---|---|---|
| 1. description sim_mode | L0 | sim_mode=false 출력이 변경 전 URDF와 동일, sim_mode=true에서 바퀴 4개 continuous(axis y) + 구 충돌 |
| 2. 월드 생성기 | L0 | 지도 점유 칸 수와 벽이 덮는 칸 수 일치, `gz sdf -k` 통과 |
| 3. sim xacro(ros2_control·센서·마찰) | L0 | `gz sdf -p`로 SDF 변환 성공, 플러그인/센서 태그 존재 |
| 4. launch/브리지/EKF/보조 노드 | L0 | 빌드·lint, launch 인자 확인(`--show-args`) |
| 5. host 실행 | L5-sim | 데모 메카넘 확인 → JetRover: 키보드 전후좌우·회전 방향 일치, /scan /depth_cam/depth/image_raw(16UC1) /imu/data_raw /odom 발행, Nav2 A→B 직진·상자 회피(실기 F2와 같은 좌표) |
