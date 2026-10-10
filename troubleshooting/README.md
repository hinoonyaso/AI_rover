# 트러블슈팅 기록

**오류나 예상 밖의 동작이 생길 때마다** 이 폴더에 파일 하나를 추가한다. 해결이 안 됐어도 적는다(상태만 `미해결`).
파일명은 `NNN-짧은-제목.md`(번호는 이어서), 아래 목록에도 한 줄 추가한다.

## 작성 형식
```
# 제목
- 날짜: YYYY-MM-DD
- 상태: 해결 / 우회 / 미해결
- 관련: 파일, 명령, 로그

## 증상
(무엇이 어떻게 보였나. 로그 원문은 짧게 인용)

## 원인
(확인된 원인. 추정이면 "추정"이라고 쓰고 근거를 적는다)

## 해결 또는 우회
(실제로 한 조치와 결과)

## 확인/재발 방지
(같은 문제인지 알아보는 방법, 다시 안 생기게 한 것)
```

## 목록

| # | 제목 | 상태 |
|---|---|---|
| 001 | [STM32 펌웨어 hang](001-stm32-firmware-hang.md) | 미해결 |
| 002 | [base_node가 `open : No such file`로 시리얼을 못 엶](002-base-node-empty-port.md) | 해결 |
| 003 | [teleop으로 조종하면 0.5초 만에 멈춤](003-teleop-stops-after-half-second.md) | 우회 |
| 004 | [시험 후 노드가 남아 포트/파이프를 점유](004-leftover-processes.md) | 해결 |
| 005 | [`src/` 안에 build/install/log 생성](005-colcon-build-inside-src.md) | 미정리 |
| 006 | [손으로 90° 돌렸는데 yaw가 절반만 나옴](006-hand-rotation-half-yaw.md) | 해결(측정법) |
| 007 | [펌웨어 ZIP에 소스가 없고 .hex뿐](007-firmware-zip-hex-only.md) | 정보 |
| 008 | [재부팅하면 /tmp의 시험 스크립트가 사라짐](008-tmp-wiped-on-reboot.md) | 해결 |
| 009 | [rclpy Twist에 정수를 넣으면 assertion으로 죽음](009-rclpy-int-vs-float.md) | 해결 |
| 010 | [옆 이동이 1.45배로 보였음 (눈대중 측정 오차)](010-mecanum-strafe-scale.md) | 해결(가설 폐기) |
| 011 | [robot_state_publisher에 URDF를 `-p`로 넘기면 죽고 시험은 exit=0](011-rsp-urdf-cli-param.md) | 해결 |
| 012 | [CH340이 있는데 `/dev/ttyUSB*`가 없음 (`ch341` 모듈 없음)](012-ch341-module-missing.md) | 해결 |
| 013 | [Orbbec DaBai DCW: depth 센서 시리얼 없음 → SDK v2 열거 실패](013-orbbec-sdk-v2-no-serial-bug.md) | 해결 (SDK v1 소스 빌드) |
| 014 | [colcon build -j6 + 스왑 0B로 SSH가 끊기고 시스템이 멈춤](014-oom-during-build.md) | 해결 (스왑 4G 추가 + -j2) |
| 015 | [LiDAR USB가 운영 중 재연결되고 rplidar_composition이 스스로 복구 안 됨](015-lidar-usb-reconnect-no-recovery.md) | 우회 (재시작으로 회복) |
| 016 | [host RViz에서 base_link 메쉬만 "Could not load mesh resource" 에러](016-urdf-mesh-file-find-not-package.md) | 해결 (벤더 xacro의 `file://$(find)` 한 줄을 `package://`로 수정) |
| 017 | [Nav2 첫 통합 launch: 설정 오류 3개 + 재시도 중 좀비 프로세스 누적](017-nav2-bringup-hidden-nodes-zombies.md) | 해결 (플러그인 이름/누락 설정 수정, `ros2 node list`로 좀비 정리) |
| 018 | [호스트 RViz의 Nav2 Goal/2D Pose Estimate가 Jetson에 전혀 안 닿음](018-host-rviz-nav2-goal-not-reaching-jetson.md) | 해결 (Jetson+호스트 양쪽 다중 NIC로 인한 Fast-DDS 디스커버리 비대칭 + "Nav2 Goal" 툴이 Navigation 2 패널 없이는 아무것도 안 쏘는 설계) |
| 019 | [RGB-D 카메라가 Nav2 풀스택과 같이 돌 때 IR+PointCloud 켜면 조용히 멈춤](019-camera-hang-ir-pointcloud-with-full-stack.md) | 해결(우회) (재부팅까지 해도 안 풀렸는데 `enable_ir`/`enable_point_cloud`를 끄니 바로 해결 — USB가 아니라 자원 경합으로 추정) |
| 020 | [Nav2 반복 주행이 매번 같은 지점에서 "Start occupied"로 막힘 — 실제론 의자, inflation_radius도 안전 최소값 미만이었음](020-nav2-remap-chair-and-inflation-radius.md) | 해결 (의자 반영된 새 지도로 재매핑 + inflation_radius를 Nav2가 요구하는 안전 최소값(inscribed radius) 이상인 0.2로 조정) |
| 021 | [Nav2 자율주행 중 의자 다리와 충돌 — 2D LiDAR 사각지대로 추정](021-nav2-collision-with-chair-leg.md) | 우회 (근본 원인 미해결, 의자 피하는 경로로 재시도해서 성공) |
| 022 | [Nav2 후진 중 로봇 뒤쪽 완전 사각지대에서 물체를 밀고 지나감](022-nav2-rear-blind-spot-backup-collision.md) | 해결 (DWB min_vel_x=0으로 후진 차단 + BT에서 BackUp recovery 노드 제거) |
| 023 | [self-filter가 로봇 앞 35cm 물체를 "자기 자신"으로 오인해서 지워버림](023-depth-self-filter-ate-real-obstacle.md) | 해결 (풋프린트 사각형 방식 → 기준 depth 이미지와의 차이 비교 방식으로 교체) |
| 024 | [micro-ROS 라이브러리 빌드가 sudo 없는 환경에서 rosdep/libstdc++ 헤더 때문에 막힘](024-microros-build-env-no-sudo.md) | 해결 (rosdep install no-op shim + libstdc++ 헤더를 사용자 로컬 툴체인에 추가) |
| 025 | [디컴파일 재구성 패키지의 TIM8/핀 이름 오류, 부저 핀 문서 충돌](025-stm32-gpio-decompile-name-map-errors.md) | 해결 (TIM9로 정정, PA8 채택, PINMAP.md에 정리) |
| 026 | [depth로만 보이는 장애물 앞에서 DWB가 멈추고 회피 못 함](026-depth-obstacle-not-in-global-costmap.md) | 해결 (global costmap에도 depth_cloud 추가, 카메라 감지거리가 짧은 한계는 남음) |
| 027 | [로봇팔 토크 ON/OFF 서브커맨드(0x0B/0x0C)가 뒤집혀 있어 OFF해도 안 풀림](027-arm-torque-subcommands-swapped.md) | 해결 (0x0B=해제, 0x0C=걸기 확인, 호스트 코드/순서 수정) |
| 028 | [depth 장애물(상자) 회피 시험: 멈춤/충돌/대각선 종료, collision_monitor 과민 반응](028-nav2-obstacle-avoidance-tuning-session.md) | 대부분 해결 (설정 정리, 반복 시험 필요) |
| 029 | [NaN/Inf 명령이 std::clamp와 팔 step 검사를 통과](029-cmd-nan-passes-clamp-and-arm-step-check.md) | 해결 (L0, 실기 미검증) |
| 030 | [MoveIt2 설정/Setup Assistant 충돌 매트릭스(TRAC-IK 5자유도 실패, 그리퍼 쌍 누락 등)](030-moveit-setup-and-srdf-collision-matrix.md) | 해결 (plan_only 검증) |
| 031 | [Nav2 직진 중 좌우 흔들림(DWB 후보가 매 주기 vy 전 범위), min_speed_xy 무효, depth 기준이 팔 자세에 종속](031-nav2-lateral-wobble-and-depth-reference-gate.md) | 조치함, 실기 미검증 (LimitedAccelGenerator, 홈 자세 게이트, 진단 도구) |
| 032 | [Nav2 시험 후 정지 상태에서 바퀴 "웅" 소리(탭하면 멈춤)](032-wheel-hum-after-nav2-stop.md) | 미해결 (정지 프레임 0x03 효과 없음, 펌웨어 속도 루프 미세진동 추정, 탭하면 멈춤) |
| 033 | [팔을 움직인 뒤 팔 관절 TF·카메라 color TF가 안 나옴](033-arm-tf-stops-after-arm-moves.md) | 미해결 (launch 재시작으로 복구, 재발 없음) |
| 034 | [상자 회피 시험: DWB·MPPI 모두 상자 앞에서 진행 못 함(shim 반복 회전, global에 상자 없음, 좁은 통로)](034-box-avoidance-stuck-dwb-mppi.md) | 해결 (MPPI 3/3 성공), 우회 폭 조정 중 (footprint 실측 반영, inflation 0.25 미확인) |
| 035 | [자체 펌웨어 첫 flash: lockup(크리스털 16 MHz를 8 MHz로 가정 → 336 MHz) + 0.8초마다 IWDG 리셋(LCD 태스크 스택 넘침)](035-rrc-m4-first-flash-lockup-and-reset-loop.md) | 해결 (HSE 16 MHz/PLL vendor와 동일, LCD 버퍼 정적화, 실기 확인) |
| 036 | [자체 펌웨어 모터 첫 시험: 오른쪽 앞바퀴 엔코더 부호 반전 → PID(목표 0)가 최대 PWM까지 가속, e-stop도 못 멈춤](036-rrc-m4-right-wheel-runaway-encoder-sign.md) | 해결 (M2 PWM 짝 교체·부호 전부 +1, 부호 가드, e-stop 유지 — 4바퀴 실기 확인) |
| 037 | [자체 펌웨어: 전원 완전 차단 후 IMU 값이 멈춤(소프트 리셋 누락)](037-rrc-m4-imu-frozen-after-cold-boot.md) | 해결 (QMI8658 소프트 리셋, 멈춘 값 감지, 냉간 부팅 확인) |
| 038 | [자체 펌웨어: 배터리 값이 부팅 직후 첫 측정값으로 고정(ADC DMA 재시작 거부)](038-rrc-m4-battery-value-frozen.md) | 해결 (매번 Stop 후 Start, 실기 확인) |
