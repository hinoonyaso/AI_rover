# JetRover ROS2 Jazzy 전체 프로젝트 체크리스트

상태: `[x]` 완료 · `[~]` 부분 완료/추가 검증 필요 · `[ ]` 미완료
작업을 끝낼 때마다 이 파일의 상태를 갱신하고 `README.md`의 진행률 표도 고친다.
0번 섹션은 사용자가 알려준 환경 정보 기준이며, 1~3번은 실제 로봇에서 확인한 내용이다.

## 0. Jetson 개발환경
- [x] Jetson Orin Nano 8GB OS 설치
- [x] Ubuntu 개발환경 기본 설정
- [x] CUDA / nvcc 동작 확인
- [x] SSH 원격접속
- [x] VS Code Remote-SSH 사용
- [x] 자동 로그인
- [x] 화면 잠금/절전 해제
- [x] ROS2 Jazzy 설치
- [x] colcon, rosdep 개발환경
- [x] ~/jetrover_ws workspace 구성
- [ ] Docker 기반 재현 가능한 개발환경
- [ ] 전체 패키지 버전/환경 문서화
- 현재 단계에서는 Docker보다 로봇 기능 구현이 우선이다.

## 1. STM32 / Base Driver
### RRC / Serial
- [x] CH9102 USB-UART 확인 (`1a86:55d4`, `/dev/ttyACM0`)
- [x] STM32 UART2 확인
- [x] 1,000,000 baud 확인
- [x] 안정적인 `/dev/serial/by-id/usb-1a86_USB_Single_Serial_596F003889-if00` 경로 확인
- [x] RRC frame 분석 (`AA 55 FUNC LEN DATA CRC`)
- [x] CRC8-MAXIM 구현, 실제 프레임 607개 CRC 검증
- [x] Streaming parser 구현
- [x] termios serial driver
- [x] Serial 자동 reconnect
- [x] 공식 프로토콜 PDF 확보 (`firmware_source/`)

### Motor
- [x] Motor ID 0~3 확인 (펌웨어는 0부터, 공식 PDF 예제는 1부터라 문서와 다름)
- [x] 4개 바퀴 실제 mapping 확인 (모터 ID 0 왼앞, 1 왼뒤, 2 오른앞, 3 오른뒤 = 보드 포트 1~4; 오른쪽은 전진이 음수)
- [x] Mecanum inverse kinematics
- [x] /cmd_vel → motor packet
- [x] 최대 선속도 제한 (0.2 m/s), 최대 각속도 제한 (1.0 rad/s)
- [x] 실제 모터 구동 확인
- [x] 명령 timeout 0.5초 (host 측 watchdog)
- [x] 정상 종료 시 stop packet
- [x] crash signal(SEGV/ABRT/BUS/FPE/ILL/HUP/QUIT)에서 stop packet (SIGKILL은 불가)

### 남은 안전 문제
- [~] STM32 hang 진단 (**9회 발생**, 원인 미확정. 저전압 단독 가설은 폐기(9.47 V~완충 12 V 전 범위에서 발생). idle 지속이 가장 일관된 조건으로 추정. **2026-09-23: RST 버튼으로 hang 상태에서도 즉시 복구 가능함을 확인** — 이전 "전원 재시작만 복구" 기록은 정정됨. DTR/RTS 소프트웨어 자동 리셋은 4×4 조합까지 다 시험했지만 없음: `troubleshooting/001-stm32-firmware-hang.md`)
- [x] STM32 heartbeat monitor (1초 이상 packet 미수신 감지)
- [x] `/battery_state` 발행 (STM32 배터리 패킷 → `sensor_msgs/BatteryState`, 10 V 미만이면 경고) — hang 시점 전압을 남기기 위함
- [x] hang 진단 도구/기록 (`tools/stm32_diagnostics/`)
- [x] 펌웨어 `.hex` 정적 분석 (IWDG 약 20 ms, `app_task`가 먹이 → 다른 태스크만 막히면 못 잡을 수 있음)
- [x] UART1(ISP/flashing) 포트 특정 — 보드 라벨 "USB serial port 1/flashing download"로 확인, `/dev/ttyACM1`. **실제 ROM 부트로더 응답 검증 완료(2026-09-27)**: 0x7F→ACK, GET(부트로더 v0x31, Read/Write/Erase 등 지원), GET ID(`0x0413`=STM32F40x/41x, 예상과 일치)
- [x] RDP 상태 확인 + 전체 flash 백업 — RDP 없음(512KB 전부 읽기 성공), `firmware_source/RosRobotControllerM4_dumped_backup.bin`에 저장. **`firmware_source/RosRobotControllerM4.hex`와 79,857바이트(약 15%) 다름**(리셋벡터 SP부터 다른 빌드) — 사용자 요청으로 이 vendor hex로 재플래시(mass erase+write+검증 성공, 512KB 바이트 일치). RST로 재부팅 확인, 부저/OLED/IMU/배터리/바퀴 모터/로봇팔 서보 6개(관절1~5+그리퍼10) 전부 정상 동작 확인(2026-09-27)
- [ ] STM32 hang 근본 원인 규명 — 원인 규명 대신 **자체 펌웨어 재작성으로 방향 전환** (아래 참고)
- [ ] MCU 자체 motor command timeout (현재 없음, 13초 확인)
- [ ] task-health 기반 watchdog
- [ ] UART DMA recovery
- [ ] encoder feedback packet (공식 프로토콜에 없음 → 펌웨어 개발 필요. 보드 사양상 모터는 물리적으로 "4채널 인코더 모터"라 엔코더 자체는 있고 펌웨어가 내부 폐루프 속도제어에 쓰고 있을 가능성이 높지만(추정), host로는 여전히 안 옴 — 재플래시 후에도 동일 확인)
- 가장 중요한 미해결 문제는 STM32 firmware hang이다. host 측은 감지·정지 시도까지만 가능하고,
  STM32 자체가 먹통이면 정지 명령을 처리하지 못하므로 완전한 fail-safe가 아니다. RST 버튼 복구는 사람이 있어야 한다.

### 자체 STM32 펌웨어 재작성 (2026-09-27 착수, 소스가 없어 원인 규명이 막혀서 방향 전환)
계획 전체: `~/.claude/plans/enchanted-chasing-sky.md`. 목표는 모터/IMU/배터리(현재 `jetrover_base`와 와이어 호환) +
보드 PDF에 문서화된 전 기능(LED/부저/PWM서보/버스서보/버튼/SBUS/게임패드)까지 새로 구현.
- [ ] **ST-Link 호환보드 구매** (주문 완료, 도착 대기 — 도착 전까지는 하드웨어 안 건드리는 준비 단계만 진행)
- [~] 툴체인 설치 — `arm-none-eabi-gcc`(13.2.1)/`objdump`, `STM32_Programmer_CLI`(2.23.0)는 사용자가 `~/.local/opt/stm32/`에 설치 완료(`setup/ENVIRONMENT_SETUP.md` 8번). `openocd`/`stlink-tools`는 ST-Link 도착 후 설치 예정
- [x] UART1 ROM 부트로더 응답 검증 (읽기 전용: 0x7F→ACK, GET, GET_ID) — 완료, 위 1번 섹션 참고
- [x] RDP 상태 확인 + 전체 flash 백업 — 완료, 위 1번 섹션 참고 (덤으로 vendor hex 재플래시까지 실행됨)
- [~] 정적 리버스엔지니어링으로 GPIO/페리페럴 핀 1차 가설 (`analyze_firmware.py` 확장, 2026-09-27) — MOVW/MOVT로 만들어지는 페리페럴 base 주소만 잡는 방식이라 **정확한 핀은 아직 모름**(1차 활동량 신호만). TIM3/4/5/7/8/9/10/11/12/13/14 다수 사용(PWM/타이밍 후보), USART1/2/3/6+UART5 참조, SPI2 1회(디스플레이 후보), ADC1 1회(배터리 후보), GPIOB/D/H만 잡힘(A/C/E/F/G/I는 이 방식으로 안 잡힘 — LDR 리터럴풀 방식일 가능성, 탐지 방법 한계). **재플래시한 빌드는 IWDG 초기화/refresh 패턴 자체가 안 잡힘**(이전 빌드와 태스크 스택 크기도 다름 — 15% 바이트 차이와 일치, 정말 다른 빌드였다는 재확인). 정확한 핀은 ST-Link 도착 후 SWD로 확정 예정
- [x] 프로토콜 코덱(CRC8-MAXIM + FUNC 0~9) 순수 C, 호스트 유닛테스트 — `firmware/rrc_m4/lib/protocol/` (완료: FUNC0~9 pack/unpack, 골든벡터=PDF 예제+오늘 실제로 로봇에 보낸 프레임, 호스트 테스트 전부 통과, Cortex-M4 타겟 프리스탠딩 컴파일도 확인. 버스서보 부가 서브커맨드·PWM서보 deviation upload 서브커맨드 값은 미확정으로 남겨둠)
- [x] `firmware/rrc_m4/` 프로젝트 뼈대 (CMake) — 코덱 라이브러리만 있음, ARM 링크/CMSIS/HAL vendor는 아직
- [ ] (ST-Link 도착 후) SWD로 정품 펌웨어 관찰하며 핀맵 확정
- [ ] 신규 펌웨어 단계별 브링업 (LED→UART→프로토콜/IWDG 재설계→IMU→배터리→**모터**→부저/LED→버튼→SBUS→PWM서보→버스서보→OLED/블루투스/게임패드 USB Host)

## 2. IMU
- [x] 0x07 packet decoding
- [x] sensor_msgs/msg/Imu, `/imu/data_raw` (약 111 Hz)
- [x] g → m/s², deg/s → rad/s
- [x] 실제 센서 축 확인 (센서 X 오른쪽, Y 뒤, Z 아래)
- [x] STM32 sensor frame → base_link 방향 변환 (x=−y, y=−x, z=−z)
- [x] gyro bias 측정, gyro bias YAML 적용, bias 자동 측정 tool (`tools/imu_calibration/`)
- [x] 3자세 축 검증, 360° 회전 검증
- [~] gyro scale 약 97%
- [~] accel magnitude 약 3% 오차 (축별 배율 차이)
- [ ] temperature별 bias 변화 분석
- [ ] 장시간 Allan variance 분석
- 마지막 두 개는 연구 목적이 아니면 우선순위가 낮다.

## 3. Odometry / State Estimation
- [x] /wheel_twist (TwistWithCovarianceStamped)
- [x] /odom_raw (command 기반 open-loop, 디버깅용)
- [x] Mecanum vx, vy, wz 처리
- [x] robot_localization 설치
- [x] EKF 설정 (`config/ekf.yaml`)
- [x] vx, vy + IMU wz 융합, open-loop 위치는 EKF에 넣지 않음 (twist 전용 입력)
- [x] /odom, odom → base_link TF
- [x] 가상 시리얼 전체 경로 검증 (`tools/stm32_diagnostics/ekf_pipeline_test.py`)
- [x] 정지 상태 실제 로봇 검증 (yaw 드리프트 약 0.8°/분)
- [~] 실제 이동 /odom 검증(왕복 3세트 후 원위치 오차 약 1 cm 이내): 바닥에서 전진/후진/좌/우/회전 완료(0.05~0.1 m/s, STM32 정상). 전진·옆 이동은 명령과 일치(0.99). 1 m 이상 직진과 속도별 반복은 남음

STM32가 encoder feedback을 보내지 않으므로 실제 이동거리가 아니라 명령 속도를 적분한 open-loop odom이다.
- [~] 실제 직진 거리 측정: 0.1 m/s × 3초 명령 30.4 cm → 실측 약 30 cm (1회). 1 m 이상은 아직
- [~] 전진 scale (`odom_linear_scale`): 0.99 → 1.0 유지 (측정 1회, 반복 필요)
- [x] 횡이동 scale: 재측정(줄자)에서 명령 30.4 cm → 실측 30 cm = 0.99 → 1.0 유지. 처음의 "44 cm"는 눈대중 오차였음(troubleshooting/010). 코드에 `odom_lateral_scale` 파라미터는 남겨 두었고 기본 1.0
- [~] angular scale (`odom_angular_scale`): 명령 적분 60° → 자이로 +48.9° (81%, 눈대중 약 45°). EKF는 자이로 yaw를 쓰므로 `odom_raw`에만 영향
- [~] 여러 속도 구간에서 오차 측정: EKF(명령 적분)는 0.05/0.1/0.2 m/s에서 일관(0.301/0.602/0.608 m). 실측(줄자)은 0.2 m/s 등 아직
- [ ] 바닥 종류별 slip 측정
- [ ] (가능하면) STM32 firmware에서 wheel RPS feedback 추가 → encoder 기반 wheel odometry 전환

## 4. Robot Description / TF
목표 TF: map → odom → base_footprint → base_link → {imu_link, lidar_link, camera_link(color/depth optical), arm_base_link → arm}
- [x] **JetRover URDF 실제 메쉬로 교체 (2026-10-03)**: `~/AI_secretary_robot`(사용자의 다른 로컬 프로젝트)에
  Hiwonder 공식 `jetrover_arm_moveit` 패키지 전체(xacro+메쉬)가 있는 걸 발견, `src/jetrover_description/`로
  가져옴(`$(find jetrover_arm_moveit)`→`$(find jetrover_description)`로 치환). 손으로 쓴 박스/실린더
  placeholder(`jetrover_placeholder.urdf`로 보관)는 더 안 쓰고, `description.launch.py`가 이제
  `jetrover.xacro`를 직접 처리한다(`xacro` 설치돼 있음 확인, 패키지 의존성 추가). 상세: `src/jetrover_description/README.md`
- [x] base_footprint (EKF 프레임 = `odom → base_footprint`), [x] base_link (이제 실제 차체 메쉬)
- [x] IMU frame 개념 확정
- [x] imu_link (실제 메쉬 적용. **벤더 xacro의 `imu_joint` rpy(원시 센서축 회전)는 `0 0 0`으로 되돌림** —
  `base_node`가 이미 소프트웨어로 변환하므로 벤더 회전을 그대로 쓰면 이중 변환이 됨. translation은 벤더값=기존값과 일치 확인)
- [x] lidar_link (실제 메쉬, 벤더 xacro 값이 기존 값과 거의 동일(소수점 정밀도만 다름) — 교차 검증됨). 장착 위치 실측은 아직
- [x] **camera_link, depth_cam_link/frame — 이번에 처음 TF 트리에 들어감** (`link4`에 연결, optical 변환까지 벤더 xacro에 있음). 실제 카메라 드라이버의 frame_id가 이 이름과 일치하는지 확인은 아직
- [x] **arm_base_link → 5축 팔(link1~5)+그리퍼(gripper_link+손가락) 전체가 TF 트리에 들어감** (`check_urdf`로 트리 확인 완료, `joint1`~`joint5` + fixed 조인트들). 실제 서보(bus servo ID 1~5+그리퍼10)와 연결하는 컨트롤러/조인트 상태 publish는 아직 없음(14번 섹션)
- [x] robot_state_publisher (`jetrover_description/launch/description.launch.py`, `base.launch.py`에 포함) — xacro 처리로 전환 후 재검증 완료(`/robot_description` 정상 발행, 에러 없음)
- [~] RViz RobotModel 검증 — host Ubuntu 24.04 + RViz2(ROS_DOMAIN_ID=25)로 띄움, 실제 메쉬 반영 확인은 사용자 몫
- [~] TF tree 검증: `check_urdf`로 전체 트리(29개 링크) 확인 완료. 실제 로봇에서 `odom→lidar_link`, `odom→imu_link` 체인은 기존에 확인됨, 새로 추가된 팔/카메라 체인의 실측 검증은 아직
- [ ] 실측 footprint(바퀴/차체 치수를 줄자로 재검증 — 지금은 전부 Hiwonder 공식값)

## 5. LiDAR (RPLIDAR A1, 사용자 확인)
- [x] USB/serial 인식 — `drivers/ch341/`의 모듈을 설치해서 `/dev/ttyUSB*` 생성, **재부팅 후에도 자동 로드 확인**. `ttyUSB0/1` 번호는 재부팅마다 바뀌므로 by-path(`...usb-0:2.1.4:1.0-port0`)로 지정 (GET_INFO로 A1M8 fw 1.29 확인, 헬스 Good)
- [x] Jazzy driver: `ros-jazzy-rplidar-ros` 설치됨 (A1은 115200 baud 예상, 실제 시험은 포트가 생긴 뒤)
- [x] /scan (`jetrover_bringup/launch/lidar.launch.py`), frame_id `lidar_frame` (URDF에서 `lidar_link` 기준 yaw 180°)
- [x] scan frequency 약 14 Hz = **실제 회전 속도**(time_increment×720 = 74.7 ms와 일치; 이 어댑터가 A1 모터를 최대 속도로 돌리는 것으로 추정, 드라이버에 속도 파라미터 없음). 각도 해상도 약 0.64°, 720 bin(0.5°), 범위 0.15~12 m
- [x] 유효 포인트 50%의 원인: **스캔 −72°~+90°(로봇 기준 뒤쪽 약 160°)가 로봇팔 기둥/몸체에 가려짐**. 나머지 구간은 빈틈 거의 없음 → SLAM은 앞쪽 약 200°만 본다. 범위 정확도 검증은 아직
- [~] RViz(사용자 환경은 VS Code SSH라 화면 없음 → `tools/viz/snapshot.py`로 PNG 저장해서 확인, 실시간은 Foxglove 권장): `jetrover_bringup/rviz/jetrover.rviz`(Grid, RobotModel, TF, LaserScan, Odometry; 고정 프레임 odom)와 `rviz.launch.py`. 로봇 화면(:0)에서 12초 시작해 설정 오류 없음 확인, 실제 화면 확인은 사용자 몫
- [x] base_link → lidar_link → lidar_frame TF (URDF, 실제 스캔으로 방향 검증: 정면 물체 +9°(배치 오차 추정), 왼쪽 물체 +90°/+89° → 좌우 반전 없음, 재부팅 후 재확인)
- [ ] 로봇 회전하면서 scan 정합 확인
- [~] 장시간 USB 안정성 시험 — **2026-09-28: 약 30분 운영 중 USB 재연결 1회 발생**(`ttyUSB0`→`ttyUSB2`), `rplidar_composition`이 자동 복구 안 되고 `/scan` 완전히 끊김(재시작으로 회복). 원인 미확정, `troubleshooting/015` 참고. 재발하는지 계속 관찰 필요
- 완료 기준: RViz에서 RobotModel + /scan + /odom + TF 모두 정상

## 6. SLAM (SLAM Toolbox: 2D scan matching + pose graph + loop closure)
- [x] slam_toolbox 설치 (사용자 sudo로 설치 완료). 설정/launch: `jetrover_navigation`
- [x] async mode 결정 (online async, `config/slam_toolbox_online_async.yaml`: base_footprint, 12 m, 작은 움직임에도 갱신)
- [x] /scan, /odom 연결: 정지 상태에서 `slam_toolbox` active, `/map` 발행(0.05 m), `map→base_footprint` TF 정상, 경고 없음
- [x] map 생성: **키보드 조종 한 바퀴 완주, hang 없이 사각형 방 지도 완성** (`tools/viz/out/lap1_final.png`), 로봇이 출발 지점으로 복귀
- [ ] loop closure
- [x] map 저장: `slam_toolbox serialize_map`으로 `~/jetrover_ws/maps/lap1_20260922.{posegraph,data}` 저장 성공. **`nav2_map_server` 설치 완료(2026-09-22 22:31) 후 표준 `.pgm/.yaml`도 저장 성공**(`/slam_toolbox/save_map` result=0, `setup/ENVIRONMENT_SETUP.md` 참고) — 이전 기록의 "실패"는 stale이었음(2026-09-28 정정). map 재로드(`deserialize_map`으로 계속 매핑 또는 AMCL용 로드)는 아직
- [ ] 긴 복도 테스트, 반복 주행 map distortion 확인
- [ ] 성능 기록: loop closure error, 벽 직선성, 재방문 위치 오차, CPU/RAM

## 7. Localization (map_server + AMCL, Mecanum이므로 OmniMotionModel 검토)
- [x] Map Server — `src/jetrover_navigation/launch/localization.launch.py`. **2026-09-28: 단독 실행으로 확인**: `maps/lap1_20260922.yaml` 로드(67×67 @ 0.05m/cell, yaml과 일치), configure→activate lifecycle 전환 성공
- [x] AMCL — `config/amcl.yaml`(`robot_model_type: nav2_amcl::OmniMotionModel`), 빌드 성공. **2026-09-28 실제 로봇(base+LiDAR)으로 소프트웨어 연동 검증 완료**: `ros2 launch jetrover_navigation localization.launch.py`로 map_server+amcl+lifecycle_manager 전부 정상 activate, `/scan` 구독·`/amcl_pose` 발행·`map→odom` TF 전부 확인
- [x] Omni motion model — 실제 activate까지 확인(정지 상태 기준, 회전/횡이동 중 particle filter 반응은 로봇을 움직여야 확인 가능 — 아직)
- [~] Initial Pose — `amcl.yaml`의 (0,0,0) 기본값으로 정상 설정됨(`Setting pose: 0.000 0.000 0.000` 로그 확인). 이게 실제 로봇 시작 위치와 맞는지는 물리적으로 검증 안 함
- [x] /amcl_pose — 발행 확인(x=0,y=0, covariance 0, 정지 상태라 당연한 값). **주의**: 이 토픽은 `TRANSIENT_LOCAL` durability라 기본 QoS로 구독하면 조용히 아무것도 안 받는다(`troubleshooting/015` 참고)
- [x] map → odom — TF 확인(거의 identity, 로봇이 초기 pose에서 안 움직인 상태라 당연)
- [ ] kidnap/relocalization test — 로봇을 실제로 이동시켜야 함 (물리 시험)
- [ ] localization error 측정 — 위와 동일, 물리 시험 필요

## 8. Nav2
- [ ] SmacPlanner2D (Global, cost-aware A*)
- [ ] MPPI Controller, motion_model = Omni (vx, vy, wz)
- [ ] Costmap: Static / Obstacle / Inflation layer, Robot footprint, Local / Global costmap
- [ ] Recovery: Clear Costmap, Backup, Spin, Wait, Retry
- [ ] NavigateToPose, NavigateThroughPoses
- [ ] 직선 주행, 90° 코너, 좁은 복도, 장애물 회피, 횡이동 활용
- [ ] 목표 위치/yaw 정밀도, 반복 주행
- 정량 지표: CTE RMS, Goal Position Error, Goal Yaw Error, Success Rate, Planning/Replanning Latency

## 9. Navigation BT
- [ ] Nav2 BT 구조 이해
- [ ] 기본 NavigateToPose BT
- [ ] Recovery BT
- [ ] Custom BT XML
- [ ] 필요한 Custom BT node (예: ComputePath → FollowPath → 실패 → ClearCostmap → Retry)

## 10. 정밀 위치 정렬 (AprilTag + PnP + TF2)
- [ ] AprilTag detector
- [ ] Tag pose
- [ ] Desk marker, Charging marker, Workstation marker
- [ ] Nav2 coarse approach → AprilTag fine alignment
- [ ] 정차 오차 측정

## 11. RGB-D Camera
- [x] 카메라 확인: **Orbbec DaBai DCW** (RGB `2bc5:0559`+시리얼 있음, Depth `2bc5:0659`+**시리얼 없음**, legacy OpenNI/SDK v1 장치)
- [x] `jetrover_perception` 패키지, udev 규칙 설치로 USB 권한 문제는 해결
- [x] ~~막힘: OrbbecSDK v2 버그~~ **해결**: `ros-jazzy-orbbec-camera`(SDK v2, apt)는 이 장치를 못 찾는 업스트림 버그가 있음
  (`orbbec/OrbbecSDK_v2#51`). **`OrbbecSDK_ROS2`의 `main` 브랜치(SDK v1.10.37)를 소스로 빌드해서 apt 버전을 오버레이**하여 해결 (troubleshooting/013)
- [x] Jazzy driver: 소스 빌드(SDK v1) `orbbec_camera` 정상 동작, `Device DaBai DCW connected`
- [x] RGB topic(`color/image_raw` 640×360 rgb8, 약 23 Hz), Depth topic(`depth/image_raw`, 약 24 Hz), IR(약 23 Hz), CameraInfo, point cloud 모두 발행 확인
- [ ] RGB/Depth alignment (정렬 정확도 검증은 아직)
- [ ] Camera calibration 확인
- [ ] TF 연결 (URDF에 아직 arm 체인이 없어 `depth_cam_link`가 로봇 TF 트리에 안 붙어 있음)
- [ ] RViz image, PointCloud 검증 (`tools/viz/snapshot.py`류 도구로 SSH 환경에서 확인 필요)

## 12. Vision AI
- Detection (YOLO nano급 → ONNX → TensorRT FP16)
  - [ ] 모델 선택, ONNX export, TensorRT engine
  - [ ] ROS2 inference node, /detections
  - [ ] latency, FPS, GPU/RAM 측정
- Segmentation (Manipulation 단계)
  - [ ] instance segmentation, mask
  - [ ] Depth ROI, invalid depth filtering, median depth
- Tracking (ByteTrack)
  - [ ] Person tracking, Object ID 유지, lost/reacquire

## 13. 3D Perception (Detection/Mask → 픽셀(u,v)+Depth → 카메라 내부 파라미터 → XYZ_camera → TF2 → XYZ_arm_base)
- [ ] Pixel + Depth
- [ ] Back-projection, XYZ
- [ ] TF2 transformation
- [ ] object PoseStamped
- [ ] depth noise filtering
- [ ] 반복 측정 표준편차
- [ ] 실제 물체 위치 오차 측정

## 14. Robot Arm / MoveIt2 (MoveIt2 + OMPL + RRTConnect)
- [~] **버스 서보 ID 확인(2026-09-27, raw 프로토콜 레벨, ROS2 드라이버는 아직 없음)**: FUNC5로 ID 1~5 응답(관절, pulse 0~1000↔0~240°), **ID10 = 그리퍼**(ID 6~9,11~15는 무응답). PWM 서보(FUNC4) 채널 1~4는 응답은 하지만(전부 1500 기본값) 실제로 움직여도 육안으로 아무 변화 없음 — 미사용이거나 연결 안 된 채널로 추정. 각 서보 소폭 이동(±40~60 pulse)→원위치 왕복으로 실제 로봇에서 확인함
- [x] **Arm driver — 서보 위치 읽기 (2026-10-03~04)**: `jetrover_base`(`base_node`)에 FUNC5 read-position 폴링(5Hz round-robin, ID 1~5+10)과 `sensor_msgs/JointState` publish(`/joint_states`, 그리퍼는 `r_joint`만 — 나머지 5개 손가락 조인트는 URDF `<mimic>`으로 자동 계산됨)를 추가함. 변환식 `(ticks-center)*rad_per_tick*sign+offset`은 `~/AI_secretary_robot`의 `arm_servo_state_bridge.py`(Hiwonder 공식 jetrover_arm_moveit 부속)에서 가져옴.
  sign=+1 기본값은 틀렸었다(동어반복 검증이었을 뿐 물리 방향 미확인) → `~/AI_secretary_robot`의 실제 캘리브레이션(`config/servo_calibration.yaml`)대로 **sign=-1(전 관절)로 교체, 2026-10-04 사용자가 host RViz에서 실물 팔을 직접 움직이며 최종 확인함(잘 따라옴)** — center=500/offset=0/sign=-1로 확정.
  파라미터는 `config/base.yaml`에 노출(재조정 시 재컴파일 불필요). **모터 명령(write)은 아직 없음** — 지금은 읽기(TF 시각화용)만, 실제 팔을 움직이는 FUNC5 move 명령 송신은 MoveIt2 단계에서
- [x] **URDF 실제 메쉬/조인트 반영 (2026-10-03)**: `jetrover_description`에 Hiwonder 공식 메쉬+xacro 통합 완료(4번 섹션 참고). `joint_limits.yaml`은 `~/AI_secretary_robot/src/control/jetrover_arm_moveit/config/joint_limits.yaml`에 이미 있음(가져오기는 아직 안 함). ID3은 pulse=5로 끝단 근접 — 안전 pulse 범위 확정은 아직
- [ ] IK
- [ ] MoveIt Setup Assistant
- [ ] PlanningScene, Collision model
- [ ] RRTConnect, Pose goal
- [ ] 실제 arm trajectory
- [x] Gripper (ID10으로 확인됨)

## 15. Grasp (1차: Segmentation + Depth + Geometry + Rule-based)
- [ ] Object centroid, orientation estimate
- [ ] pre-grasp / grasp / retreat pose
- [ ] top grasp, side grasp
- [ ] collision check
- [ ] grasp success verification
- [ ] (고도화) AnyGrasp / GraspNet 계열 비교 — 우선순위 낮음

## 16. MoveIt Servo / Visual Servoing
- [ ] MoveIt Servo
- [ ] Cartesian velocity
- [ ] target pose error
- [ ] Visual Servo loop
- [ ] safety velocity limit

## 17. Mission Behavior Tree (BehaviorTree.CPP)
목표: FetchObject = CheckRobotReady → NavigateToDesk → AlignToDesk → DetectObject → EstimatePose → Pick → VerifyGrasp → NavigateToUser → Deliver
- [ ] BehaviorTree.CPP
- [ ] Mission Manager
- [ ] Navigate / Detect / Grasp Action wrapper
- [ ] Retry, Timeout, Fallback, Recovery, Cancel
- [ ] Emergency abort

## 18. FastAPI Backend (React → REST/WebSocket → FastAPI → ROS2 Bridge → Robot)
개발 순서(9단계, 전체 통합 이후)상 아직 착수 안 함. 상세: `prd/jetinspect-m.md` 17절, `prd/jetinspect-m-pipelines.md` 18절.
- [ ] FastAPI project
- [ ] /api/status, /api/mission, /api/navigation/goal, /api/mission/cancel, /api/robot/stop
- [ ] WebSocket
- [ ] ROS2 bridge, ROS2 Action Client
- [ ] Diagnostics aggregation
- FastAPI가 직접 PWM이나 motor packet을 보내지는 않는다.

## 19. React 관제 UI (React + TypeScript + Vite)
- [ ] Dashboard, Robot online/offline
- [ ] Battery, STM32 heartbeat
- [ ] Map, Robot pose, Global path
- [ ] Camera, Detection
- [ ] Current Mission, BT current node
- [ ] CPU/GPU/RAM, Temperature
- [ ] Errors, Mission history
- [ ] Emergency stop / mission cancel

## 20. Robot Screen UI (본체 HMI, Chromium kiosk mode)
- [ ] Battery, Robot state, Current mission
- [ ] Camera
- [ ] Auto / Manual
- [ ] Home, Cancel, Stop
- [ ] 간단한 음성 상태 표시

## 21. Database (초기 MySQL → 최종 PostgreSQL + VectorDB — 2026-09-28 확정, `prd/jetinspect-m.md` 17절)
**신뢰수준: 계획.** SQLite 단일DB안(직전 결정)은 폐기. 초기 개발은 MySQL + SQLAlchemy로 빠르게 가고,
최종 단계에서 PostgreSQL로 이전 + RAG용 별도 VectorDB를 붙인다(제품 미정 — 24번 섹션).
- [ ] MySQL로 초기 스키마 구현: missions, robot_events, detections, system_metrics, alerts
- [ ] locations, documents, document_chunks
- [ ] (최종 단계) PostgreSQL로 마이그레이션

## 22. Semantic Map (desk, charger, door, delivery_station, storage)
- [ ] 장소 이름, x, y, yaw, type, description
- 목표: "책상으로 가" → LLM → desk → DB(x,y,yaw) → Nav2

## 23. LLM / VLM
- LLM: [ ] 자연어 명령 분석 · [ ] Structured JSON · [ ] Mission 생성 · [ ] Tool calling · [ ] BT에 parameter 전달
- VLM: [ ] Scene understanding · [ ] Target disambiguation · [ ] 이미지 질의응답 · [ ] object semantic 판단
- 원칙: VLM → What?, YOLO + Depth → Where?

## 24. RAG (Document → Chunk → Embedding → VectorDB → Top-K → LLM)
자료: JetRover manual, STM32 protocol, STM32 hang NOTES, Nav2 config, MoveIt setup, Camera/LiDAR manual, Troubleshooting, Calibration 기록
- [ ] Document loader, Chunker, Embedding
- [ ] **VectorDB 제품 조사·결정** — PostgreSQL `pgvector` 확장으로 21번 DB 안에 통합할지, Qdrant/Milvus/Chroma 등 독립 VectorDB로 분리할지 미정(계획)
- [ ] Metadata, Retrieval
- [ ] Reranking 필요 여부 검토
- [ ] RAG API
- [ ] 관제 UI Chat

## 25. Robot Memory
- [ ] Mission memory, Detection memory, Object-location memory
- [ ] Error history, Robot event history
- [ ] 자연어 검색

## 26. Voice AI (Mic → VAD → STT → LLM/Intent → BT → Robot → TTS)
- [x] **하드웨어 확인(2026-09-28)**: 마이크 어레이 = USB `card 0` (XFM-DP-V0.0.18, iFlytek 원거리 마이크 어레이 보드, `arecord -D hw:0,0`), 스피커 = USB `card 1` (GeneralPlus USB Audio Device, `aplay -D plughw:1,0`, mono는 `plughw` 필요 — `hw`는 채널 수 불일치로 실패). 4초 녹음 후 재생 왕복으로 실사용 확인(목소리 들림, 무음 아님)
- [ ] VAD, STT, Intent Router, LLM, TTS — **전부 미착수**. STT/TTS 엔진 자체가 아직 하나도 안 깔려 있음(whisper/vosk 등 확인함, 없음)
- 안전 명령 STOP / CANCEL / HOME은 LLM 없이 deterministic하게 처리한다.

## 27. Diagnostics / Monitoring
- [x] STM32 heartbeat, 배터리 전압(`/battery_state`)
- [ ] /diagnostics
- [ ] IMU Hz, LiDAR Hz, Camera FPS
- [ ] Battery
- [ ] Jetson RAM, CPU, GPU, EMC, Temperature
- [ ] Nav2 State, Mission State
- [ ] Error alert
- 웹 관제와 연결한다.

## 28. Logging / Rosbag
- [ ] rosbag 자동 recording (Mission 시작/종료 시)
- [ ] 오류 발생 전후 기록
- [ ] DB에는 rosbag path만 저장
- [ ] Log rotation, disk usage 관리
- 권장 토픽: /cmd_vel /odom /imu/data_raw /scan /tf /tf_static /detections /diagnostics

## 29. Deployment (개발: SSH + tmux)
- [ ] systemd, 자동 ROS bringup
- [ ] FastAPI 자동 실행, DB 자동 실행, React serving
- [ ] watchdog/restart policy, log rotation
- [ ] boot 후 자동 로봇 준비
- Docker: [ ] FastAPI container · [ ] PostgreSQL container · [ ] React build · [ ] ROS2 container 적용 여부 검토 (로봇 제어까지 Docker화는 후순위)

## 30. Edge AI 최적화 (Jetson Orin Nano 8GB)
- [ ] YOLO PyTorch baseline → ONNX → TensorRT FP16 → (필요 시 INT8)
- [ ] FPS, latency, peak RAM, GPU utilization, temperature, power
- [ ] 여러 노드 동시 실행 stress (Nav2 + Camera + YOLO + MoveIt + FastAPI + DB)

## 31. 최종 시스템 통합
"책상에서 빨간 캔 가져와" → Voice/React → LLM → Structured Mission → BehaviorTree.CPP → NavigateToDesk(Nav2) → AprilTag Align → YOLO → RGB-D → 3D XYZ → TF2 → MoveIt2 → Grasp → Verify → NavigateToUser → Deliver → DB/Web 관제에 결과 기록
- [ ] 전체 시나리오 통합 및 반복 시험
