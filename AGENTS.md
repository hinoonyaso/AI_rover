# AGENTS.md — JetRover 프로젝트 지침

이 문서는 JetRover 프로젝트를 이어서 작업하는 AI 에이전트(Claude Code, Codex)를 위한 지침이다.
**이 파일이 유일한 원본이다.** `CLAUDE.md`는 `@AGENTS.md`로 이 파일을 불러오기만 하므로(Claude Code는 `AGENTS.md`를 직접 읽지 않는다) 지침은 여기서만 고친다.

## 작업 시작 규칙
1. 이 파일을 읽는다.
2. `checklist/PROJECT_CHECKLIST.md`에서 현재 진행 상태를 확인한다.
3. 관련된 오류가 있을 법하면 `troubleshooting/README.md` 목록을 보고 해당 문서를 읽는다.
4. 작업 대상 패키지의 README/config/launch를 먼저 확인한다.
5. 새로 만들기 전에 이미 구현된 기능이 있는지 코드를 검색한다.
6. 아래 "확정된 사실"과 충돌하는 변경이 필요하면 먼저 사용자에게 알린다.
7. **새 기능(체크리스트의 새 섹션, 또는 기존 섹션의 큰 항목)에 처음 착수할 때는 바로 코딩하지 말고
   아래 "새 기능 작업 방식(3-File System)"을 따른다.**

## 새 기능 작업 방식 (3-File System: PRD → Task → 실행)

Ryan Carson의 3-File System(요구사항 → 작업 분해 → 실행 규칙을 파일로 고정)을 이 프로젝트 구조에
맞게 쓴다. 원본은 `create-prd.md`/`generate-tasks.md`/`process-task-list.md` 세 규칙 파일과
`tasks/prd-*.md`/`tasks/tasks-*.md`를 따로 두지만, 이 프로젝트는 이미 전체 작업을
`checklist/PROJECT_CHECKLIST.md` 하나로 추적하고 있으므로 **Task 파일을 따로 만들지 않고
그 체크리스트를 Task 파일로 겸용**한다(두 곳에서 따로 진행 상황을 관리하면 어긋난다 — 실제로
이번 세션에서 지도 저장 상태가 `troubleshooting/`엔 성공, `checklist/`엔 실패로 어긋나 있던 걸
겪었다). 3개 역할은 이렇게 대응한다.

| 원본 역할 | 이 프로젝트에서 |
|---|---|
| PRD (무엇을 만드는가) | `prd/<슬러그>.md` — 새로 씀. 틀은 `prd/README.md` |
| Task 목록 (어떤 순서로) | `checklist/PROJECT_CHECKLIST.md`의 해당 섹션 — PRD를 parent task + sub-task로 쪼개 기존 섹션을 확장 |
| **TEST_PLAN (어떻게 검증하는가)** | `prd/<슬러그>-test-plan.md` — 로봇 프로젝트는 웹 개발보다 하드웨어/ROS2 통합 시험 비중이 커서 원본 3-File System에 없는 걸 추가함. parent task마다 "테스트 레벨과 완료 기준"(아래)의 L0~L5 중 어느 레벨까지 필요한지, 통과 기준이 뭔지 적는다 |
| 실행 규칙 (어떻게) | 이 섹션(아래) |

**적용 대상**: 새 checklist 섹션 착수, 또는 기존 섹션의 규모 큰 항목(예: Voice AI 전체, MoveIt2 통합).
**적용 안 함**: 조사/디버깅(예: STM32 hang 원인 찾기), 한두 줄 수정, 대화로 자연스럽게 풀리는 작업.

### 0) 개발 순서 (고정, 임의로 안 바꿈)
`Base/TF → SLAM/Nav2 → RGB-D/YOLO → 3D XYZ → MoveIt2 → Voice → Mission BT → Battery/Safety → 전체 통합`.
**음성/LLM부터 먼저 만들지 않는다** — 재미는 있지만 로봇 프로젝트의 핵심(자율주행·인식·조작 통합)이
뒤로 밀린다. 이 순서와 다른 순서로 진행해달라는 요청이 오면, 순서를 바꾸는 이유를 먼저 확인한다.
전체 배경은 `prd/jetinspect-m.md` 13절.
**2026-10-06 보정(사용자 승인)**: 순서는 그대로이고 2단계를 `Nav2 baseline → 엔코더 odom → Before/After 재시험 → DWB vs MPPI`로 세분화했다.
`ros2_control` 팔 PRD는 그 뒤에 쓴다. 단계별 게이트는 `docs/ROADMAP.md`.

### 1) PRD
범위가 애매하면 코딩 전에 **먼저 사용자에게 명확화 질문**을 한다(목표, 범위, 비범위, 제약, 완료 기준).
답을 듣고 `prd/<슬러그>.md`를 쓴다.

### 2) Task
승인된 PRD를 `checklist/PROJECT_CHECKLIST.md`의 해당 섹션에 parent task + sub-task로 옮긴다.
막연한 문장이 아니라 "지금 할 일이 정확히 뭔지" 하나씩 보이게 쪼갠다(원본 예시의 "1. Audio Input →
1.1 ALSA device 확인 → 1.2 ..." 수준).

### 3) 실행
1. **한 번에 sub-task 하나만** 한다. 시작 전에 PRD와 그 sub-task, 관련 코드를 확인한다.
2. 끝나면 build/test(해당하면 `colcon test`, 호스트 유닛테스트 등)를 돌리고, 실패하면 고친다.
3. 통과하면 그 sub-task만 `[x]`로 바꾸고 새로 안 사실이 있으면 옆에 적는다. **끝내지 못한 걸 `[x]`로
   표시하지 않는다.**
4. 하나 끝낼 때마다 무엇을 했는지 간단히 보고하고, 다음 sub-task로 넘어가기 전에 사용자의 확인을
   기다린다 — 단, 사용자가 "쭉 진행해"처럼 명시적으로 허락하면 그 지시를 따른다. 안전 규칙 대상
   (모터, flash 등)이거나 방향이 갈릴 수 있는 지점은 허락을 받았어도 다시 한번 멈춘다.
5. 작업 중 발견한 새 문제는 그 자리에서 고치지 말고 Task 목록(체크리스트)에 sub-task로 추가한다.
6. 지금 sub-task와 무관한 리팩토링을 하지 않는다. 기존 동작을 깨뜨리지 않는다.
7. parent task의 sub-task가 전부 끝나면 그 사실을 명확히 알린다.

## 프로젝트
- 로봇: Hiwonder JetRover (Mecanum). 호스트 Jetson Orin Nano 8GB + ROS2 Jazzy. 저수준은 STM32F407(RRC 보드)이 담당한다.
- **프로젝트명: JetInspect-M** — 음성 지시를 받아 자율주행하며 설비를 점검(게이지/Stack Light/Valve/안전통로)하고,
  이상 발견 시 음성·화면으로 보고하거나 로봇팔로 현장 조치(부품 회수, 버튼 조작)하는 Edge AI 모바일 매니퓰레이터.
  단순 SLAM/Nav2 데모가 아니라 JetRover의 센서·액추에이터·배터리·Edge 컴퓨팅을 하나의 End-to-End 임무로 통합하는 것이 핵심.
  전체 기획(배경/아키텍처/시나리오/KPI/산출물)은 `prd/jetinspect-m.md`, 파이프라인별 기술 스펙(음성/Nav/Perception/
  Manipulation 등 22개, 전부 "계획" 신뢰수준)은 `prd/jetinspect-m-pipelines.md`.
- 목표: 자율주행(SLAM/Nav2) → 인식 → 로봇팔 조작 → 미션 BT → 웹 관제/LLM/음성까지의 전체 통합. 전체 계획과 진행 상황은 `checklist/PROJECT_CHECKLIST.md`.
- 사용자와는 **한국어**로 대화한다. 코드 주석은 기존 파일의 영어 주석을 유지하고 **한글 주석을 함께** 단다(영어를 지우고 한글로 바꾸지 않는다; `mySkills/skills/coding`의 규칙). 커밋 메시지는 기존 스타일을 따른다.

```
[계획] React / HMI / Voice → FastAPI → Mission Manager (BehaviorTree.CPP)
[계획]      ┌── Nav2 (+SLAM/AMCL) ── LiDAR
            ├── Perception (RGB-D, YOLO)
            └── MoveIt2 ── Arm
[구현] EKF (robot_localization) ← wheel_twist + imu/data_raw
[구현] jetrover_base (base_node) ── RRC, 1 Mbps ── STM32F407 ── 모터 / IMU / 팔 bus servo 위치(읽기)
```

## 폴더
| 경로 | 내용 |
|---|---|
| `src/jetrover_base/` | 베이스 드라이버 패키지 (`base_node`, RRC 프로토콜, 시리얼, 크래시 가드, launch, 설정) |
| `src/jetrover_description/` | URDF(xacro)와 `robot_state_publisher` launch. **2026-10-03부터 Hiwonder 공식 메쉬 사용** (`~/AI_secretary_robot`의 `jetrover_arm_moveit`에서 가져옴, IMU 조인트 회전은 이중변환 방지로 0으로 되돌림 — `src/jetrover_description/README.md`). 팔/그리퍼/카메라까지 TF에 포함됨 |
| `src/jetrover_bringup/` | 전체 실행 launch(`robot.launch.py`, `lidar.launch.py`, `rviz.launch.py`), LiDAR 설정, RViz 설정 |
| `src/jetrover_navigation/` | SLAM Toolbox 설정/launch (이후 AMCL, Nav2) |
| `tools/viz/` | `snapshot.py`: 스캔/지도/TF를 위에서 본 PNG로 저장 (사용자는 VS Code SSH라 RViz 화면을 못 본다) |
| `src/jetrover_perception/` | 카메라(Orbbec DaBai DCW) launch/설정. 이후 YOLO/Depth 인식 |
| `src/OrbbecSDK_ROS2/` | Orbbec 카메라 드라이버 소스(vendor, `main` 브랜치=SDK v1). 같은 이름(`orbbec_camera`)으로 apt 버전을 오버레이한다 |
| `drivers/ch341/` | Jetson 커널에 없는 CH340 드라이버 (빌드/설치 스크립트) |
| `setup/` | `ENVIRONMENT_SETUP.md`: 이 로봇에 한 sudo/apt/시스템 설치 전체 기록 (새 Jetson 재현용) |
| `checklist/` | 전체 체크리스트와 진행률 (3-File System의 Task 파일 역할도 겸함) |
| `troubleshooting/` | 오류 원인과 해결 기록 |
| `docs/` | 로드맵(`ROADMAP.md`), 아키텍처, 설계 노트, 사례 정리, 벤치마크 결과/튜닝 이력. 인덱스는 `docs/README.md` |
| `prd/` | 새 기능 착수 전 PRD (3-File System 1번째 파일). 언제/어떻게 쓰는지는 `prd/README.md`. `jetinspect-m.md`(+`-pipelines.md`)가 프로젝트 전체 기획서 |
| `firmware/rrc_m4/` | STM32 자체 펌웨어 재작성 프로젝트(계획: `~/.claude/plans/enchanted-chasing-sky.md`). `lib/{protocol,core,comm}`(호스트 단위 시험) + `app/`(HAL+FreeRTOS, RRC/micro-ROS 두 빌드). **flash 전**, 개요는 `firmware/rrc_m4/README.md` |
| `src/jetrover_microros/` | micro-ROS 펌웨어용 호스트 패키지(브리지 노드 + agent launch). `jetrover_base`와 같은 시리얼 포트를 쓰므로 동시에 못 띄움 |
| `tools/` | 시험/진단 스크립트: `parse_stm32.py`, `sniff_stm32.py`, `imu_calibration/`, `stm32_diagnostics/`(NOTES.md에 hang 조사 전체 기록) |
| `firmware_source/` | Hiwonder 자료(펌웨어 `.hex` ZIP, 프로토콜 PDF, 실제 칩에서 덤프한 백업 `.bin`, `decompile/`) — **2026-10-06부터 git 추적 제외, 로컬에만 존재**(재배포 권한 불분명; 추적되는 건 `PINMAP.md`/`BOARD_CONNECTORS.md`뿐). 소스는 없음. `BOARD_CONNECTORS.md`에 커넥터/센서/액추에이터 대응표, `PINMAP.md`에 MCU 핀 대응(확정/추정 구분), `decompile/`에 Ghidra 결과 |

새 기능을 `jetrover_base`에 무분별하게 넣지 않는다. 기능 영역이 다르면 별도 ROS2 패키지를 만든다
(예: LiDAR/Nav2 → `jetrover_navigation`, YOLO/Depth → `jetrover_perception`, MoveIt → `jetrover_manipulation`,
BT → `jetrover_mission`, URDF → `jetrover_description`). 이름과 구성은 계획이며 만들 때 사용자와 정한다.

**참고 자료(이 워크스페이스 밖)**: `~/AI_secretary_robot`에 사용자의 다른 로컬 프로젝트가 있고,
Hiwonder 공식 `jetrover_arm_moveit`(URDF/메쉬/MoveIt2 설정/SRDF/TRAC-IK), `ros_robot_controller_msgs`,
음성 파이프라인(wake/VAD/STT/LLM/TTS, C++), nav2/slam config 등이 통째로 들어있다. PRD(`prd/jetinspect-m*.md`)의
MoveIt2/Voice/Navigation 단계에 착수하기 전에 **먼저 여기 비슷한 게 있는지 확인**한다(이미 URDF는
2026-10-03에 여기서 가져왔다). 이 프로젝트(`jetrover_ws`)의 직접적인 부분이 아니므로 체크리스트/PRD에서
가져다 쓸 때마다 출처를 남긴다.

## 빌드와 실행
- 빌드는 **반드시 `cd ~/jetrover_ws`에서** `colcon build --packages-select jetrover_base`. (`src/`에서 빌드하면 `src/build|install|log`가 생긴다: troubleshooting/005)
- 실행: `source ~/jetrover_ws/install/setup.bash && ros2 launch jetrover_base base.launch.py` (`base_node` + URDF `robot_state_publisher` + robot_localization EKF).
- 검사: `colcon test --packages-select jetrover_base` (flake8, uncrustify 등이 통과해야 한다).

## 테스트 레벨과 완료 기준
| 레벨 | 내용 | 예 |
|---|---|---|
| L0 | build, lint, unit test | `colcon build`, `colcon test` |
| L1 | 하드웨어 없이 가상 시리얼로 검증 | `tools/stm32_diagnostics/ekf_pipeline_test.py`, `odom_raw_test.py`, `crash_guard_test.py` |
| L2 | 하드웨어 연결, **모터 비활성** | IMU/STM32 통신, `imu_soak.py`, `imu_calibration/` |
| L3 | **바퀴를 띄운** 모터 시험 | `motor_load_test.py` (사용자가 전원 스위치 옆에) |
| L4 | 바닥 주행 | 0.05 m/s부터, 짧은 거리, 주변 공간 확보 |
| L5 | 통합 자율 시험 | SLAM/Nav2/Perception/Mission |

사용자가 "L2까지만"처럼 레벨을 지정하면 그 이상은 하지 않는다.
체크리스트 항목을 `[x]`로 바꾸려면 구현, build 성공, `colcon test` 통과, 재현 가능한 config/launch, 수치와 결과 문서화가 필요하고,
하드웨어가 관련된 기능은 **실제 로봇에서 검증**돼야 한다. 코드만 작성했거나 L1까지만 확인했으면 `[~]`로 둔다.

## 확정된 사실 (다시 조사하지 않는다)
- 링크: CH9102 USB-UART(`/dev/serial/by-id/usb-1a86_USB_Single_Serial_596F003889-if00`), STM32 UART2, **1,000,000 baud**.
- 프레임: `AA 55 FUNC LEN DATA CRC8-MAXIM` (CRC는 FUNC+LEN+DATA). FUNC 0 배터리(`04`+u16 mV), 3 모터, 5 버스 서보(관절1~5+그리퍼10, read-position subcommand `05`: 요청 `[05,id]`→응답 `[id,05,success,pulse i16LE]`, pulse 0~1000↔0~240°), 7 IMU(가속도 g, 자이로 deg/s, float32×6), 8 게임패드. `base_node`가 FUNC5를 5Hz round-robin으로 폴링해서 `/joint_states`로 publish한다(2026-10-03, 쓰기/모터 제어는 아직 없음 — `checklist` 14번).
- **모터 ID는 0~3이다** (`DATA = 01, N, N×(id u8, rps f32)`).
  - ID 0 왼쪽 앞, ID 1 왼쪽 뒤, ID 2 오른쪽 앞, ID 3 오른쪽 뒤.
  - 오른쪽 모터(ID 2, 3)는 전진 방향의 rps 부호가 **음수**이다.
  - Hiwonder 공식 PDF의 일부 예제는 모터 번호를 1부터 적지만 실제 펌웨어는 0부터다 (바퀴 시험으로 확인).
  - 코드의 `MotorCommand::id`는 보드 포트 번호 1~4(사람이 부르는 번호)이고, 패킷을 만들 때 `id-1`로 바꾼다.
- **IMU 축과 프레임**
  - STM32 raw 센서 축은 X=오른쪽, Y=뒤, Z=아래이다.
  - `base_node`가 이를 REP-103 축(x 앞, y 왼쪽, z 위)으로 변환(x=−y, y=−x, z=−z)한 뒤 `/imu/data_raw`로 발행한다. `frame_id = imu_link`.
  - 따라서 URDF의 `base_link → imu_link`(`imu_joint`) **회전은 0**이어야 한다. 데이터를 TF로 다시 회전하지 않는다 (축 변환 이중 적용 금지).
    (Hiwonder URDF의 `imu_joint` rpy=(π,0,−π/2)는 raw 센서 축 X=오른쪽, Y=뒤, Z=아래를 뜻하며 실측과 일치한다.)
  - IMU/LiDAR/팔 기준의 translation은 Hiwonder URDF 값이다 (직접 실측한 것이 아님).
  - 자이로 bias는 `config/base.yaml`(변환된 축 기준, rad/s).
- **TF 트리**: `odom → base_footprint`(EKF) `→ base_link → {imu_link, lidar_link, link1..5(팔)+gripper_link(그리퍼), 바퀴}`(URDF, 2026-10-03부터 실제 메쉬+팔 전체 포함, `src/jetrover_description/README.md`). `base_node`의 `odom_raw`/`wheel_twist` 프레임도 `base_footprint`. 깊이 카메라(`camera_connect_link`→`depth_cam_link`→`depth_cam_depth_frame`/`depth_cam_color_optical_frame` 등)는 로봇팔 끝(`link4`)에 붙어 있어 팔 자세에 따라 위치가 바뀐다 — **실제 카메라 드라이버(`orbbec_camera`)의 frame_id와 URDF 프레임 이름이 정확히 일치함을 확인함(2026-10-04)**: `base_link→link4→camera_connect_link→depth_cam_link→depth_cam_color_optical_frame` 전체가 `lookup_transform`으로 연결됨.
- **LiDAR**: RPLIDAR **A1M8**(fw 1.29, 사용자 확인 + GET_INFO). 커널이 `ch341`을 빼고 빌드돼서 `drivers/ch341/`의 모듈을 설치해 썼다(`sudo ./install.sh`, 재부팅 후 자동 로드, 커널 업데이트 시 재빌드: troubleshooting/012). **`ttyUSB` 번호는 재부팅마다 바뀌므로** 포트는 by-path(`/dev/serial/by-path/platform-3610000.usb-usb-0:2.1.4:1.0-port0`, LiDAR를 같은 USB 포트에 꽂아 둘 것)로 지정한다. `/scan`은 약 14 Hz(실제 회전 속도), 프레임은 `lidar_frame`(URDF에서 `lidar_link` 기준 yaw 180°)이고 실제 스캔으로 방향을 검증했다. **로봇 뒤쪽 약 160°는 로봇팔에 가려 반환이 없다.** 다른 CH340(`ttyUSB` 나머지 하나)은 정체 미상이며 아무것도 보내지 않는다.
- 실행: `ros2 launch jetrover_bringup robot.launch.py`(베이스 + URDF + EKF + LiDAR), RViz는 `ros2 launch jetrover_bringup rviz.launch.py`, SLAM은 `ros2 launch jetrover_navigation slam.launch.py`(`slam_toolbox` 설치 필요).
- STM32는 **엔코더/바퀴 속도를 호스트로 보내지 않는다** (캡처, SDK, 공식 PDF로 확인). 그래서 odom은 명령 속도를 적분하는 open-loop이고, EKF에는 `wheel_twist`(vx, vy)와 자이로 yaw rate만 넣는다. open-loop 위치는 EKF에 넣지 않는다.
- STM32에는 **호스트 명령 timeout이 없다.** 호스트가 죽으면 바퀴가 마지막 속도로 계속 돈다. 정지는 host 쪽 watchdog(`cmd_vel_timeout` 0.5초), 종료 시 stop, 크래시 시 stop 프레임이 담당한다.
  - host의 stop 수단은 **best-effort**이다. SIGKILL, kernel panic, Jetson 전원 손실, USB 단절, STM32 hang에서는 정지 패킷 전송을 보장하지 못한다.
- **STM32 hang**: 9회 발생했다 — **전부 2026-09-23까지, 2026-09-27 펌웨어 재플래시 이전이다.** 재플래시(기존 빌드와 15% 다른 vendor `.hex`로 교체, 1번 섹션 "자체 STM32 펌웨어 재작성" 참고) 이후 2026-10-04까지 hang 재발 없음 — **호전된 것으로 보이지만 원인 규명은 아니다**(`troubleshooting/001` "2026-10-04 업데이트" 참고, 표본 늘었을 뿐 반증 실험은 안 함). **보드의 RST 버튼을 누르면 hang 상태에서도 즉시 복구된다**(2026-09-23 확인, 아래 "전원을 껐다 켜야만"은 그 전 기록). DTR/RTS 소프트웨어 리셋은 4×4 조합까지 시험했지만 없고, ISP 포트(`/dev/ttyACM1`)에서 `DTR=0 & RTS=1`은 오히려 hang을 만든다. 8·9차는 이 시험 중 발생. 아래는 7차까지의 기록) (7차는 **완충(~12 V) 상태**에서 주행 직후 idle 몇 분 만에 발생 — 저전압 단독 가설은 약해졌다. 6차는 주행 중 배터리 **9.47 V 실측**에서 발생. 4, 5차는 로봇이 정지한 상태에서 전원 재시작 후 약 20~50분에 발생. LiDAR는 원인이 아닌 것으로 확인. 3차는 바닥 6초 주행 직후. 충전 직후 11.5 V로 시작했지만 **hang 시점 전압은 미측정**이고 재부팅 후 무부하 전압이 10.5 V였으므로, 저전압 가능성은 배제되지 않았다). IMU/배터리 송신과 모든 명령이 멈추고 USB는 살아 있으며, **로봇 전원을 껐다 켜야만** 복구됐다. **원인은 미확정**이다.
  - 바이너리 분석상 IWDG가 켜져 있고(prescaler 32, reload 19, LSI 32 kHz 가정 시 약 20 ms), `app_task`가 약 10 ms마다 refresh하는 경로가 확인됐다.
  - 따라서 `app_task`가 살아 있는 채로 다른 태스크만 데드락되면 watchdog 리셋이 일어나지 않을 **수 있다**. 이것이 세 hang의 실제 원인이었는지는 **미확정**이다.
  - 자세한 내용은 `troubleshooting/001-stm32-firmware-hang.md`, `tools/stm32_diagnostics/NOTES.md`.

## 안전 규칙 (반드시 지킨다)
1. 모터가 돌아가는 시험은 **바퀴를 띄우고**, 사용자가 **전원 스위치 옆에** 있고, **배터리가 충전된 상태**에서만 한다. 바닥 주행은 0.05 m/s로 짧게부터.
2. 모터를 움직이는 명령이나 물리적으로 로봇을 움직이는 시험은 실행 전에 사용자에게 알리고, 끝나면 반드시 정지 명령을 보낸다 (`finally`).
3. `sudo`가 필요한 작업(apt 설치, `dmesg`, `lsof`)은 비밀번호가 없으므로 사용자에게 요청한다.
4. 배터리 10 V 미만이면 충전을 요청한다. 시험 중 STM32가 조용해지면(`STM32 silent` 로그) 바로 알린다.
5. 시험용 프로세스는 끝나면 `pgrep -x base_node` 등으로 남은 것이 없는지 확인한다 (troubleshooting/004).

## 사용자 승인 없이 하면 안 되는 작업
먼저 무엇을 왜 하는지 설명하고 승인을 받은 뒤에 한다.
- STM32 펌웨어 flash, 기존 `.hex` 덮어쓰기 (원본을 백업하기 전에는 하지 않는다. 다른 로봇(ROSOrin)용 `.hex`는 올리지 않는다)
- 실제 모터/로봇팔을 움직이는 시험
- 파일이나 폴더 삭제: `rm -rf`는 대상을 먼저 확인한다. 워크스페이스 루트의 `build/ install/ log/`는 다시 만들 수 있지만,
  `src/` 아래의 것(소스 포함, `src/build|install|log`도 포함)은 승인 후에만 지운다.
- 저장된 map, 캘리브레이션 값, config 덮어쓰기 (`gyro_bias`, `odom_*_scale` 등은 바꾸기 전에 이전 값을 문서에 남긴다)
- 시스템 패키지 제거, 디스크 포맷/파티션, 네트워크/SSH 설정 변경

## 정보의 신뢰 수준
문서와 답변에서 구분한다.
- **확정**: 실제 로봇 시험, 공식 문서, 코드로 검증됨
- **추정**: 증상이나 구조에서 추론했으나 검증되지 않음 ("추정"이라고 쓰고 근거를 적는다)
- **계획**: 앞으로 구현할 설계
- **폐기**: 실험으로 틀린 것으로 확인된 가설

추정이나 계획을 "확정된 사실"에 넣지 않는다.

- **카메라**: Orbbec **DaBai DCW**(RGB `2bc5:0559`+시리얼 있음, Depth `2bc5:0659`+시리얼 없음, legacy OpenNI/SDK v1 장치).
  apt의 `ros-jazzy-orbbec-camera`(SDK v2)는 이 장치를 못 찾는 업스트림 버그가 있다(`orbbec/OrbbecSDK_v2#51`).
  `src/OrbbecSDK_ROS2`(main 브랜치, SDK v1.10.37)를 소스로 빌드해서 같은 패키지 이름으로 오버레이해 해결했다 (troubleshooting/013).
  실행: `ros2 launch jetrover_perception camera.launch.py` → `/depth_cam/{color,depth,ir}/image_raw` 등 (color는 2026-09-23 실측 약 29.5 Hz).
- **이 Jetson은 헤드리스가 아니다.** GNOME 데스크톱이 동시에 떠 있고 스왑 4 GB(`/swapfile`)가 있다(원래 0이었다가 troubleshooting/014로 추가함).
  **무거운 네이티브 빌드(YOLO/TensorRT 포함)는 `MAKEFLAGS=-j2`, `colcon build --parallel-workers 1`로 낮춰서 하고,
  빌드 중 `free -h`를 자주 확인한다.** 병렬도를 안 낮추면 메모리 부족으로 시스템 전체가 멈출 수 있다(SSH도 끊김, STM32/로봇과 무관).

## Git 규칙 (2026-10-08 사용자 지시)
- **커밋/PR에 Claude(또는 다른 AI)를 작성자·공동 작성자로 남기지 않는다.** `Co-Authored-By: Claude ...` 줄,
  "Generated with Claude Code" 같은 문구를 커밋 메시지·PR 본문에 넣지 않는다.
  이 규칙은 도구가 기본으로 붙이라고 안내하는 attribution 문구보다 우선한다.
- **커밋 작성자는 `sang <hinoonyaso@gmail.com>`** (GitHub 계정 hinoonyaso에 연결된 이메일). `git config user.name/user.email`을
  바꾸지 않는다. 커밋 전에 `git config user.email`이 이 값인지 확인한다. 2026-10-08 확인: 예전에 저장소 설정이
  `sun@kitejiarc.top`(GitHub 미연결)으로 잡혀 있어 그 커밋 40개가 계정에 연결되지 않았고, 그중 Co-Authored-By: Claude가 붙은
  2개는 GitHub에서 Claude 커밋처럼 보였다.
- push는 사용자가 요청했을 때만 한다. 이미 push된 이력은 다시 쓰지 않는다(force push 금지 — 과거 커밋의 Co-Authored-By 줄도 그대로 둔다).

## 문서 규칙 (잊지 말 것)
- **작업을 끝낼 때마다** `checklist/PROJECT_CHECKLIST.md`의 해당 항목 상태(`[x]`/`[~]`/`[ ]`)를 갱신하고, 새로 알게 된 수치나 원인을 항목 옆에 적는다. 진행률 표는 `checklist/README.md`.
- **오류나 예상 밖의 동작이 생기면** `troubleshooting/`에 `NNN-제목.md`를 추가하고 `troubleshooting/README.md` 목록도 갱신한다. 형식은 증상 / 원인 / 해결 또는 우회 / 확인·재발 방지이며, 해결하지 못했어도 `미해결`로 적는다.
- 재사용할 스크립트는 `/tmp`가 아니라 `tools/`에 둔다 (재부팅하면 `/tmp`가 지워진다: troubleshooting/008).
- **`sudo apt install`이나 시스템 전역 설치(커널 모듈 등)를 할 때마다** `setup/ENVIRONMENT_SETUP.md`에 날짜·명령·이유·확인 방법을 추가한다. 사용자에게 설치를 요청할 때도 이 파일에 먼저 적어 둔다.
- 큰 결정이나 수치(보정값, 시험 결과)는 관련 README/NOTES에 남긴다. 확인하지 않은 것을 사실처럼 쓰지 않는다.
- **Nav2/인식 파라미터를 바꿀 때마다** 설정 파일 주석(이전 값 → 새 값, 날짜, 이유)과 함께 `docs/benchmarks/navigation/tuning-history.md`에 한 줄을 추가한다. 시도했다가 되돌린 값도 적는다(2026-10-09: 사흘 치 변경이 이 문서에서 빠져 있었다).
- **새 기능에 처음 착수할 때는** 위 "새 기능 작업 방식(3-File System)"대로 `prd/`에 PRD부터 쓴다.
