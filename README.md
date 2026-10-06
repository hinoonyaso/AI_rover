# AI_rover

Hiwonder JetRover(메카넘 휠 + 5-DoF 로봇팔 + 그리퍼) 위에 ROS 2 Jazzy 기반 자율주행·인식·조작·미션·관제 시스템을 처음부터 쌓아 가는 프로젝트.
Hiwonder 기본 소프트웨어를 쓰지 않고, STM32(RRC 보드) 프로토콜을 직접 분석해서 드라이버부터 만들었다.

- 호스트: Jetson Orin Nano 8GB, Ubuntu + ROS 2 Jazzy
- 저수준: STM32F407 (RRC 보드), CH9102 USB-UART, 1,000,000 baud
- 센서: RPLIDAR A1M8, Orbbec DaBai DCW (RGB-D), 보드 IMU
- 개발 방식: VS Code Remote-SSH (RViz 화면을 못 보므로 PNG 저장 / 웹 스트리밍 도구를 씀)

## 진행 상황 (2026-10-06 기준)

| 영역 | 상태 |
|---|---|
| Base driver (`base_node`), IMU, EKF | 완료 (바닥 주행 1차 검증). odom은 **cmd_vel 적분 open-loop** (아래 "Current vs Target") |
| URDF / TF | 거의 완료 (공식 메쉬 + 팔 + 카메라 TF, 실측 footprint만 남음) |
| LiDAR | 완료 (`/scan` 약 14 Hz) |
| SLAM (slam_toolbox) | 완료 (지도 저장까지), loop closure 정량평가 남음 |
| AMCL | 소프트웨어 스택 실기 검증 완료, relocalization 오차 정량평가 남음 |
| Nav2 (DWB) | 동작 — 실주행 성공/충돌 사례 기록, **obstacle avoidance 튜닝 중**, 반복시험 baseline 남음 |
| RGB-D 카메라 | 완료 (TF, 정렬, camera_info, PointCloud 확인) |
| Depth 장애물 | 동작 (임시 근거리 방식: background-depth 비교 sparse cloud → local/global costmap). 정량평가 남음 |
| 로봇팔 저수준 | 위치 읽기(`/joint_states`) + 위치 명령(`arm/command`) + torque + home pose 완료. **bring-up/진단용 인터페이스** |
| MoveIt2 / Vision AI / Mission BT / 웹 관제 / LLM | 예정 |
| Voice | 마이크·스피커 하드웨어 확인 완료, SW(VAD/STT/TTS) 예정 |
| 자체 STM32 펌웨어 (`firmware/rrc_m4/`) | **L0(호스트 단위시험)까지 완료, 실기 flash/bring-up 전** (RRC + micro-ROS 두 빌드) |
| **STM32 안정성** | 재플래시(2026-09-27) 이후 hang 재발 없음, **원인은 미확정** — 아래 "알려진 문제" 참고 |

로드맵·아키텍처·설계 노트는 [docs/](docs/README.md). 항목별 상세는 [checklist/PROJECT_CHECKLIST.md](checklist/PROJECT_CHECKLIST.md), 요약은 [checklist/README.md](checklist/README.md).

## 구조

```
[계획] React / HMI / Voice → FastAPI → Mission Manager (BehaviorTree.CPP)
[계획]      ┌── Nav2 (+SLAM/AMCL) ── LiDAR
            ├── Perception (RGB-D, YOLO)
            └── MoveIt2 ── Arm
[구현] EKF (robot_localization) ← wheel_twist + imu/data_raw
[구현] jetrover_base (base_node) ── RRC, 1 Mbps ── STM32F407 ── 모터 / IMU
```

위 도식의 `[계획]`은 아직 없는 부분이다 (Nav2/Perception은 동작 중이나 MoveIt2/Mission/관제는 계획).

### Current vs Target (odometry)

| | 입력 | 한계 |
|---|---|---|
| **Current** | `cmd_vel`에서 유도한 open-loop `wheel_twist`(vx, vy) + IMU yaw rate | 명령 ≠ 실측. 회전은 실측 이동량이 명령의 약 81% |
| **Target** | 엔코더 기반 wheel odometry + IMU | 자체 STM32 펌웨어(`/rrc/wheel_rps`)의 실기 검증 후 전환, Nav2 baseline 재평가 |

STM32(vendor 펌웨어)는 엔코더/바퀴 속도를 호스트로 보내지 않는다. 그래서 현재 EKF에는 `wheel_twist`와 자이로 yaw rate만 들어간다.

## 저장소 구성

| 경로 | 내용 |
|---|---|
| `src/jetrover_base/` | 베이스 드라이버 (`base_node`, RRC 프로토콜, 크래시 가드, EKF 설정) |
| `src/jetrover_description/` | URDF, `robot_state_publisher` launch |
| `src/jetrover_bringup/` | 전체 실행 launch (`robot.launch.py`, `lidar.launch.py`, `rviz.launch.py`) |
| `src/jetrover_navigation/` | SLAM Toolbox, AMCL, Nav2(DWB) 설정/launch |
| `src/jetrover_perception/` | 카메라 launch, `web_video_server`, depth sparse point cloud (이후 YOLO/Depth) |
| `src/jetrover_microros/` | micro-ROS 펌웨어용 호스트 브리지 + agent launch |
| `firmware/rrc_m4/` | 자체 STM32 펌웨어 (호스트 단위시험 L0 완료, flash 전) |
| `tools/` | 진단·시험 스크립트 (`stm32_diagnostics/`, `imu_calibration/`, `lidar/`, `viz/`) |
| `drivers/ch341/` | Jetson 커널에 없는 CH340 드라이버 (빌드/설치 스크립트) |
| `setup/ENVIRONMENT_SETUP.md` | 이 로봇에 한 sudo/apt/시스템 설치 전체 기록 (새 Jetson 재현용) |
| `troubleshooting/` | 오류 원인과 해결 기록 |
| `checklist/` | 전체 체크리스트와 진행률 |
| `maps/` | 저장한 지도 (`.pgm`/`.yaml`만 추적) |
| `AGENTS.md` | AI 에이전트용 프로젝트 지침 겸 확정된 사실 모음 (`CLAUDE.md`는 이를 import) |

## 시작하기

새 Jetson에 재현하려면 먼저 [setup/ENVIRONMENT_SETUP.md](setup/ENVIRONMENT_SETUP.md)의 순서대로 apt 패키지, ch341 모듈, udev 규칙을 설치한다.

### 이 저장소에 없는 것

`.gitignore`로 제외했으므로 따로 준비해야 한다.

- **`src/OrbbecSDK_ROS2/`**: 자체 git 이력이 있는 vendor 소스. `main` 브랜치(SDK v1)를 받는다.
  apt의 `ros-jazzy-orbbec-camera`(SDK v2)는 DaBai DCW를 못 찾는 업스트림 버그가 있어 소스를 오버레이한다 ([troubleshooting/013](troubleshooting/013-orbbec-sdk-v2-no-serial-bug.md)).
  ```bash
  git clone -b main https://github.com/orbbec/OrbbecSDK_ROS2.git src/OrbbecSDK_ROS2
  ```
- **`firmware_source/`**: Hiwonder 펌웨어(`.hex` ZIP, 칩에서 덤프한 `.bin`, `decompile/` Ghidra 산출물)와 프로토콜 PDF는 재배포 권한이 불분명해
  2026-10-06부터 `.gitignore`로 제외하고 **로컬에만 둔다**. 이 저장소에는 직접 작성한 `PINMAP.md`, `BOARD_CONNECTORS.md`만 공개한다. 소스는 애초에 없다.
  (과거 커밋 이력에는 덤프가 남아 있다 — 이력 삭제 여부는 미결정, `checklist/README.md` 참고.)
- **`maps/*.posegraph`, `maps/*.data`**: slam_toolbox 직렬화 지도 (용량이 커서 제외).
- `build/ install/ log/ Log/`: 빌드 산출물과 로그.

### 빌드

**반드시 워크스페이스 루트에서** 빌드한다 (`src/`에서 하면 `src/build` 등이 생긴다: [troubleshooting/005](troubleshooting/005-colcon-build-inside-src.md)).

```bash
cd ~/jetrover_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select jetrover_base jetrover_description jetrover_bringup jetrover_navigation jetrover_perception
```

Orbbec 드라이버 같은 무거운 네이티브 빌드는 이 Jetson이 GNOME 데스크톱과 같이 돌고 RAM이 7.3 GiB뿐이라 병렬도를 낮춰야 한다.
안 그러면 메모리 부족으로 시스템이 멈추고 SSH가 끊긴다 ([troubleshooting/014](troubleshooting/014-oom-during-build.md)).

```bash
MAKEFLAGS=-j2 colcon build --parallel-workers 1 --packages-select orbbec_camera_msgs orbbec_camera orbbec_description
free -h   # 빌드 중 1~2분마다 확인
```

### 실행

```bash
source ~/jetrover_ws/install/setup.bash

ros2 launch jetrover_bringup robot.launch.py        # 베이스 + URDF + EKF + LiDAR
ros2 launch jetrover_navigation slam.launch.py      # SLAM (slam_toolbox 필요)
ros2 launch jetrover_perception camera.launch.py    # RGB-D 카메라
ros2 launch jetrover_perception web_video.launch.py # 카메라를 브라우저로 (포트 8080)
```

VS Code SSH 환경에서 화면을 보는 방법은 [tools/viz/README.md](tools/viz/README.md).
`web_video_server`는 원본과 같은 프레임레이트로 스트림하지만 SSH 터널 구간의 대역폭 때문에 느려 보일 수 있다.
그럴 땐 `&width=320&height=240&quality=40` 쿼리로 줄인다.

### 검사

```bash
colcon test --packages-select jetrover_base   # flake8, uncrustify 등
```

## 알려진 문제: STM32 hang

STM32 펌웨어가 불규칙하게 멈춘다 (2026-09-20~23 사이 9회 기록). IMU/배터리 송신과 모든 명령이 멈추지만 USB 장치는 그대로 살아 있다.
**원인은 미확정**이다. 배터리 전압(9.5 V~완충 12 V 모두에서 발생)이나 LiDAR와는 무관해 보이고, 주행 후 idle 상태가 이어질 때 자주 났다.

- **복구는 보드의 RST 버튼을 직접 누르면 된다** (전원을 껐다 켤 필요 없음).
- 소프트웨어(DTR/RTS)로 자동 복구하는 방법은 없다. `DTR=0 & RTS=1`(ISP 포트)은 오히려 같은 정지 상태를 만들고 정상 앱으로 돌아오지 않는다. 이 조합을 실수로 걸지 않도록 주의.
- STM32에는 호스트 명령 timeout이 없어서 호스트가 죽으면 바퀴가 마지막 속도로 계속 돈다. `base_node`의 watchdog은 best-effort일 뿐이다.

전체 조사 기록: [troubleshooting/001-stm32-firmware-hang.md](troubleshooting/001-stm32-firmware-hang.md), [tools/stm32_diagnostics/NOTES.md](tools/stm32_diagnostics/NOTES.md).

## 안전

- 모터가 도는 시험은 **바퀴를 띄우고, 전원 스위치 옆에서, 충전된 배터리로** 한다. 바닥 주행은 0.05 m/s부터 짧게.
- 배터리가 10 V 미만이면 충전한다.
- 시험이 끝나면 `pgrep -x base_node` 등으로 남은 프로세스가 없는지 확인한다 ([troubleshooting/004](troubleshooting/004-leftover-processes.md)).

## 문서 규칙

작업이 끝날 때마다 `checklist/`를 갱신하고, 오류는 `troubleshooting/`에 `NNN-제목.md`로 남기고, 시스템 설치는 `setup/ENVIRONMENT_SETUP.md`에 기록한다.
자세한 지침과 확정된 사실은 [AGENTS.md](AGENTS.md).
