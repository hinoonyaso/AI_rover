# PRD: JetInspect-M

> **신뢰 수준: 계획.** 이 문서 전체는 AGENTS.md의 신뢰 수준 구분("계획: 앞으로 구현할 설계")에 해당한다.
> 사용자가 작성한 기획서 원문을 그대로 옮긴 것이며, 안의 구체적인 모델명/무료 티어 조건/라이선스 설명은
> 검증되지 않은 채로 인용된 것들이다(원문에 `Hiwonder`, `Microsoft Azure`, `GitHub`, `Ollama` 등 출처
> 표기가 남아있어 그대로 둔다). 실제 구현 시점에 하나씩 확인해서 "확정된 사실"로 승격시킨다.
> 파이프라인 상세 스펙은 `prd/jetinspect-m-pipelines.md`.

## 1. 프로젝트 개요

- **프로젝트명**: JetInspect-M
- **주제**: JetRover 기반 Edge AI 멀티모달 자율 설비 점검 및 현장 대응 모바일 매니퓰레이터
- **한 줄 정의**: 작업자의 음성 지시를 받아 공장·실험실·설비실을 자율주행하며 설비 상태와 안전환경을 점검하고,
  이상 발견 시 음성·화면으로 보고하거나 로봇팔을 이용해 간단한 현장 조치를 수행하는 자율 로봇.
- **핵심 목표**: 음성 명령 → 임무 이해 → 자율주행 → 설비 탐색 → Vision/Depth 점검 → 이상 판단 →
  로봇팔 대응 → 결과 보고 → 배터리 상태 기반 복귀. 단순 SLAM/Nav2 데모가 아니라 JetRover의
  센서·액추에이터·배터리·Edge 컴퓨팅 자원을 하나의 End-to-End 임무에 통합하는 것이 핵심이다.

## 2. 문제 정의 및 필요성

산업 현장에서는 작업자가 설비를 순회하며 계기판, 표시등, 밸브, 바닥 이물질 등을 반복적으로 확인해야 한다.
접근이 불편하거나 반복적인 점검 업무를 모바일 로봇이 대신할 경우 작업자의 이동 부담을 줄이고 점검
데이터를 지속적으로 축적할 수 있다. 실제 현대자동차그룹의 Safety Inspection Robot도 생산현장을
자율주행하면서 게이지, 램프, LED, 밸브 상태와 바닥의 볼트·너트·이물질 등을 점검하는 구조다.
본 프로젝트는 이 산업 PoC를 소형 JetRover 환경으로 축소 구현한다.

## 3. 대상 환경

초기 PoC는 실제 공장이 아니라 미니 스마트팩토리 테스트베드로 구축한다(출발/복귀 지점, 설비 A/B/C,
장애물/작업자, 작업대, 안전통로로 구성된 간단한 레이아웃). 점검 대상은 처음엔 4개로 제한한다.

| 대상 | 판단 내용 |
|---|---|
| 아날로그 게이지 | 수치 판독 및 정상범위 여부 |
| Stack Light | Green/Yellow/Red 상태 |
| Valve | Open/Closed 상태 |
| 안전통로 | 장애물/이물질 존재 여부 |

추가로 바닥의 볼트나 경량 부품을 탐지하여 로봇팔로 회수한다.

## 4. 전체 시스템 아키텍처

```
작업자 → "A라인 점검해줘" → 6CH Mic Array
  → DOA → AEC → VAD → STT → Local LLM → Mission JSON
  → Mission Manager → Behavior Tree
      ├── Navigation   (LiDAR/IMU/Encoder·Odom → EKF/TF2 → SLAM/Nav2)   # Odom: 현재 open-loop(cmd_vel 적분), Encoder는 계획
      ├── Perception    (RGB-D → YOLO/OCR/Depth)
      └── Manipulation  (6DoF Arm + Gripper, TF2, MoveIt2)
      └─→ Inspection Logic → 정상/이상/대응(Pick·Push·Place) → Mission Result
              → TTS/LCD/Dashboard
  Battery Monitor → 정상/Low Battery → Return-to-Base
```

JetRover 자체도 LiDAR, 3D depth camera, 6DoF arm, far-field microphone array 등으로 SLAM/navigation,
3D grabbing, voice interaction을 수행하도록 구성된 플랫폼이라 프로젝트 방향과 하드웨어 목적이 맞는다.

## 5. JetRover 하드웨어 활용

부품을 장착만 해두지 않고 각 부품이 실제 임무에 관여하게 한다.

| 하드웨어 | 프로젝트 역할 |
|---|---|
| Jetson Orin Nano 8GB | ROS2, Nav2, Vision, TensorRT, STT/LLM/TTS |
| STM32F407 | 모터, IMU, 배터리, 저수준 실시간 제어 |
| LiDAR | SLAM, Localization, 장애물 감지 |
| IMU | EKF, yaw/angular velocity 보정 |
| Wheel Encoder | Wheel odometry 및 속도 추정 (**현재 STM32 프로토콜엔 없음 — `checklist` "encoder feedback packet" 항목, 펌웨어 재작성 프로젝트와 연결됨**) |
| Mecanum Motor ×4 | 전후좌우 이동 및 설비 앞 정밀 정렬 |
| RGB-D Camera | 객체인식, OCR, Depth, 3D 위치 추정 |
| 6CH Mic Array | 음원방향 추정, 음성 명령 |
| Speaker | TTS 결과 및 위험 알림 |
| 6DoF Robot Arm | 설비 근접 검사, 버튼 누르기, 물체 조작 |
| Gripper | 볼트/경량 부품 Pick & Place |
| Battery | 전압 기반 Mission 관리 및 복귀 판단 |
| Display | Mission/배터리/점검 결과 HMI |
| Buzzer/LED | Fault·위험·Mission 상태 표시 |
| Wi-Fi/Ethernet | Host RViz 및 Web Dashboard 통신 |

배터리는 단순 전원이 아니라 의사결정 입력값으로 쓴다:
Normal → Mission 수행 / Warning → 새 긴 Mission 제한 / Low → 현재 작업 종료 후 Return-to-Base /
Critical → 정지 + Buzzer + TTS + UI 경고.

## 6. 핵심 기능

### 6.1 음성 기반 임무 생성
`Microphone Array → DOA → AEC/Noise Reduction → VAD → STT → Local LLM → Structured Mission`.
출력 예: `{"mission":"inspection","zone":"A","tasks":["inspect_equipment","detect_foreign_object","collect_foreign_object"]}`.
**LLM은 모터를 직접 제어하지 않는다**: `LLM → Mission JSON → Behavior Tree → ROS2 Action → Nav2/MoveIt2`로 제한.

### 6.2 SLAM·자율주행
`LiDAR + Wheel Odom + IMU → robot_localization EKF → TF → SLAM Toolbox/AMCL → Nav2`.
지원 기능: Mapping, Localization, Waypoint Navigation, Dynamic obstacle avoidance, Recovery, Return-to-Base.
Host Ubuntu 24.04에서 RViz2로 Jetson의 ROS2 데이터를 원격 시각화한다.

### 6.3 AI 설비 점검
- Gauge: Detection → Perspective Correction → Needle Detection → Angle → Calibration → 물리값(예: Pressure = 2.37 bar)
- Stack Light: Detection → ROI → Color/State Classification (GREEN=Normal, RED=Fault)
- Valve: Detection → Handle Orientation → OPEN/CLOSED
- 안전통로: Detection/Segmentation → 통로 ROI → 장애물 존재 판단 → BLOCKED/CLEAR

## 7. RGB-D 기반 3D 인식
`RGB → Detection → BBox` + `Depth → Pixel Depth → Camera XYZ` → `camera_link → TF2 → base_link`
→ `XYZ → Grasp Pose → MoveIt2 → Robot Arm`.

## 8. 로봇팔 현장 대응 (MVP 2개로 제한)
- **A. 떨어진 부품 회수**: 볼트/부품 Detection → Depth → XYZ → Grasp Pose → Pick → Maintenance Box → Place
- **B. 버튼 조작**: Button Detection → Depth → XYZ → End-effector Pose → MoveIt2 → Push → Camera로 상태 재확인

## 9. 사람-로봇 상호작용
`"제트로버" → Mic Array → DOA(예: +70°) → Robot 회전 → Person Detection → Depth → 작업자 방향 정렬 →
"무엇을 도와드릴까요?"`. Audio+Vision+Depth+Robot Control을 하나의 기능에서 통합한다. Hiwonder도
JetRover의 6채널 마이크 어레이/스피커를 sound-source positioning, voice recognition/control,
voice navigation 용도로 제시한다.

## 10. 대표 시나리오 (End-to-End)
"제트로버" 호출 → DOA로 작업자 방향 회전 → "A라인 점검하고 떨어진 부품 있으면 회수해줘" →
STT+LLM으로 Mission 생성 → Battery Check → Nav2로 A라인 이동 → 설비1 게이지 정상(2.4 bar) →
설비2 Stack Light RED(이상 기록) → 설비3 Valve CLOSED(정상) → 안전통로 장애물 발견(위치 저장) →
바닥 볼트 탐지 → RGB-D로 XYZ 계산 → Mecanum으로 위치 정렬 → Arm+Gripper Pick →
Maintenance Box Place → "결과 알려줘" → TTS 보고 → Display/Web 상세 결과 → Battery Low →
Return-to-Base → Mission 종료.

## 11. 소프트웨어 구성

| 영역 | 기술 |
|---|---|
| OS | Ubuntu 24.04 |
| Robot Middleware | ROS2 Jazzy |
| Navigation | Nav2 |
| SLAM | SLAM Toolbox |
| Localization | AMCL |
| Sensor Fusion | robot_localization |
| Coordinate | TF2 |
| Manipulation | MoveIt2 |
| Vision | OpenCV |
| Detection | YOLO11 |
| Inference | TensorRT |
| Audio | GCC-PHAT / AEC / RNNoise |
| VAD | Silero VAD |
| STT | Local STT |
| LLM | Local LLM |
| TTS | Local TTS |
| Mission | BehaviorTree.CPP |
| Backend | FastAPI |
| UI | React |
| Communication | ROS2 DDS |

## 12. ROS2 노드 구성 (계획)
```
jetrover_bringup/    stm32_driver, lidar_driver, camera_driver, robot_state_publisher, battery_monitor
localization/        wheel_odom, imu_filter, ekf_node, slam/localization
navigation/          nav2, waypoint_manager, recovery_manager
perception/          object_detector, equipment_inspector, depth_localizer, foreign_object_detector
manipulation/        grasp_planner, moveit, arm_controller
audio/                doa_node, vad_node, stt_node, intent_node, tts_node
mission/              mission_manager
ui/                   api_server, dashboard
```
이 프로젝트의 기존 패키지 이름(`jetrover_base`, `jetrover_bringup`, `jetrover_navigation`,
`jetrover_perception`, `jetrover_description`)과 겹치는 부분은 **새 패키지를 만들지 말고 확장**한다
(AGENTS.md "폴더" 절의 기존 규칙). `manipulation`, `audio`, `mission`, `ui`는 새 패키지가 필요하다
(예: `jetrover_manipulation`, `jetrover_audio` 또는 `jetrover_voice`, `jetrover_mission`, `jetrover_ui`).

## 13. 개발 순서 (고정, 한 번에 전부 구현하지 않는다)

**`Base/TF → SLAM/Nav2 → RGB-D/YOLO → 3D XYZ → MoveIt2 → Voice → Mission BT → Battery/Safety → 전체 통합`**
순서를 반드시 지킨다. **음성/LLM부터 먼저 완성하지 않는다** — 재미는 있지만 로봇 프로젝트의 핵심인
자율주행·인식·조작 통합이 뒤로 밀린다. (이 순서는 `AGENTS.md` "새 기능 작업 방식" 0절에도 고정 규칙으로
있다.)

1. **Base/TF**: STM32 → Motor → IMU → Odom → TF → LiDAR (**상당 부분 이미 완료**, `checklist` 1~5번 섹션)
2. **SLAM/Nav2**: SLAM → Localization(AMCL) → Nav2 → Waypoint → Recovery (**SLAM/AMCL 소프트웨어 스택 착수함**, `checklist` 6~9번)
3. **RGB-D/YOLO**: Detection(YOLO11n) → Equipment Inspection(Gauge/StackLight/Valve/안전통로)
4. **3D XYZ**: Depth → Pixel→Camera XYZ → TF2 → base_link (Grasp Pose의 입력)
5. **MoveIt2**: Grasp Pose → MoveIt2 → Pick & Place (**서보 하드웨어만 확인됨**: 관절1~5+그리퍼10, `checklist` 14번)
6. **Voice**: DOA → VAD → STT → LLM → Mission → TTS (**오디오 하드웨어만 확인됨**, `checklist` 26번)
7. **Mission BT**: 위 5개 영역을 BehaviorTree.CPP로 묶는다 (2절 참고)
8. **Battery/Safety**: 배터리 기반 Mission 판단(5절), Safety Manager(`prd/jetinspect-m-pipelines.md` 16절)
9. **전체 통합**: End-to-End 시나리오(10절) 재현, 이어서 Dashboard(FastAPI/React/SQLite/RAG, 17절)

> **2026-10-06 보정**: 위 순서는 유지하되 2단계(SLAM/Nav2)를 "Nav2 baseline → 엔코더 odom → 같은 시험 재측정(Before/After) → DWB vs MPPI"로
> 세분화하고, MVP를 `Stack Light + Dropped Part` 두 가지로 줄인다(Gauge/OCR/Valve/버튼은 확장). 근거와 단계별 게이트는 `docs/ROADMAP.md`.
> 아키텍처의 "Encoder·Odom"은 **현재 cmd_vel 적분 open-loop**이며 엔코더 기반은 **계획**이다(`prd/encoder-odometry.md`).

## 14. 성능 평가 지표 (목표치, 실제 시험으로 최종 확정)
| KPI | 평가 | 목표 |
|---|---|---|
| Navigation 성공률 | 목표지점 30회 | ≥ 95% |
| Goal 위치오차 | cm | — |
| Localization 안정성 | pose drift | — |
| Equipment Detection | Precision/Recall/mAP | — |
| Gauge 판독 | MAE | — |
| Inspection 성공률 | 정상/이상 판정 | ≥ 90% |
| 3D 위치 오차 | cm | — |
| Pick 성공률 | 30회 | ≥ 85% |
| Voice Intent 정확도 | 명령 세트 테스트 | ≥ 90% |
| Mission 성공률 | End-to-End 20~30회 | ≥ 85% |
| Recovery 성공률 | 고의 장애 상황 | — |
| AI latency | ms | — |
| FPS | TensorRT FPS | — |
| Battery Mission 판단 | Low battery test | — |

## 15. 최종 산출물 (5개로 제한)
1. 실제 JetRover 통합 시스템
2. ROS2 패키지 GitHub Repository
3. Web Monitoring Dashboard
4. 정량 성능평가 Report
5. 3~5분 End-to-End Demo 영상

README 첫 화면 구조: `Problem → Architecture → Hardware → Perception → Navigation → Manipulation →
Voice/HRI → Results → Demo`.

## 16. 프로젝트 차별점
일반적인 JetRover 프로젝트는 SLAM/YOLO/음성제어/Robot Arm을 각각 따로 보여주는 경우가 많다.
이 프로젝트는 `Hear → Understand → Navigate → See → Reason → Manipulate → Report → Manage Power`로
하나의 자율 임무로 연결한다. 즉 Multimodal Perception + Autonomous Navigation + Mobile
Manipulation + HRI + Edge AI가 하나의 Robot System 안에서 동작하는 것이 핵심 차별점이다.

## 17. 로봇 관제 및 데이터 (FastAPI + React + SQLite + RAG)

미션 이력, 점검 결과, 배터리 로그를 계속 쌓아서 나중에 자연어로 질의할 수 있게 한다
(예: "이번 주 A라인에서 이상 몇 번 났어?"). **DB 전략(2026-09-28 확정): 초기 개발은 MySQL, 최종은
PostgreSQL + 별도 VectorDB로 이전**한다(계획, 미검증 — SQLite/pgvector 단일DB안은 폐기).

```
ROS2 Nodes → Bridge Node → FastAPI ─┬→ WebSocket → React Dashboard (실시간)
                                     └→ 관계형 DB(SQLAlchemy) → Mission/Inspection/Battery 로그
                                           │
                                           ▼
                              RAG (로그+문서 → Chunk → Embedding → VectorDB → Top-K → LLM)
                                           │
                                           ▼
                                  자연어 질의 응답 ("이번 주 이상 몇 번?")
```

- **Backend**: FastAPI (REST + WebSocket) — `prd/jetinspect-m-pipelines.md` 18절 Dashboard Pipeline과 동일 구조
- **Frontend**: React — Robot State/Battery/Mission/Map Position/Camera/Inspection Result/Fault/History
- **DB**: **초기 개발 = MySQL**(SQLAlchemy ORM, 빠른 개발/친숙함 우선) → **최종 = PostgreSQL로 이전**
  (Mission 이력, 점검 결과(게이지 판독값·Stack Light·Valve 상태), 배터리 로그, Fault 기록)
- **RAG**: 위 로그 + 점검 매뉴얼/설비 문서를 임베딩해서 자연어 질의. **최종 구성에서 별도 VectorDB**를
  쓴다(PostgreSQL의 `pgvector` 확장으로 같은 DB 안에 둘지, Qdrant/Milvus/Chroma 등 독립 VectorDB로
  분리할지는 **미정** — 조사 필요, 계획). 초기 MySQL 개발 단계에선 RAG를 아직 안 붙인다(개발 순서
  9단계 이후라 자연스럽게 뒤로 밀림)
- 개발 순서(13절)상 **9단계(전체 통합) 이후**에 착수한다 — Base/Nav/Perception/Manipulation/Voice가 먼저다

## 범위 (지금 이 PRD가 다루는 것)
- 위 22개 기능 영역 전체의 목표/아키텍처/시나리오/KPI 정의

## 비범위 (이 PRD에서 다루지 않는 것 — Task 분해 단계에서 정한다)
- 각 파이프라인의 상세 기술 스펙은 `prd/jetinspect-m-pipelines.md`
- 이걸 `checklist/PROJECT_CHECKLIST.md`의 parent/sub-task로 쪼개는 작업은 **아직 안 함** — 범위가 매우
  커서(사실상 checklist 8~31번 섹션 대부분과 겹침) 영역별로 나눠서 순서대로 진행 필요

## 제약
- AGENTS.md의 안전 규칙, 확정된 사실과 충돌하지 않아야 함(특히 STM32에 encoder feedback이 없다는 점,
  모터 시험 안전 규칙, STM32 hang 미해결 상태)
- Jetson Orin Nano 8GB 메모리 제약 — 모든 모델을 상시 GPU에 올리지 않는다 (`prd/jetinspect-m-pipelines.md` 19~20절)
- 초기 구현은 Cloud 무료/무료티어 우선, 최종 구현은 Local/Edge 우선 (`prd/jetinspect-m-pipelines.md` 21절)

## 완료 기준
AGENTS.md의 공통 완료 기준(빌드/테스트 통과, 재현 가능한 config, 실물 검증, 수치 문서화)을 각
파이프라인 단위로 적용한다. 전체 PRD의 완료는 15절의 5개 산출물이 모두 나온 시점.
