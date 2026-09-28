# JetInspect-M 파이프라인 상세 스펙

> **신뢰 수준: 계획.** `prd/jetinspect-m.md`(PRD 본문)의 부속 기술 설계 문서다. 구체적인 모델명/버전/
> 무료 티어 조건/라이선스는 사용자가 조사해서 작성한 원문을 그대로 옮긴 것이며 **검증되지 않았다**.
> 실제로 설치/시험해서 확인되면 관련 `checklist/PROJECT_CHECKLIST.md` 항목과 이 문서를 함께 갱신한다.
> 기준: Jetson Orin Nano 8GB, Ubuntu 24.04 + ROS2 Jazzy, 초기 구현은 Cloud 무료/무료티어 우선,
> 최종 구현은 Local/Edge 우선, JetRover 전체 하드웨어 활용, Sensor→Perception→Decision→Planning→
> Control→Robot 전체 연결이 핵심.

## 전체 시스템 파이프라인
```
Human/User → Voice Command → [1. Audio Pipeline] → JSON Mission → [2. Mission Manager] → Behavior Tree
    ├── [3. Navigation]    LiDAR/IMU/Odom
    ├── [4. Perception]    RGB-D Camera → Detection/Depth
    └── [5. Manipulation]  Robot Arm
    └── TF2로 통합 → [6. Inspection Logic] → 정상/이상/대응
        → Voice/Display/Manipulation Action
        → [7. Power/Safety] Battery/Fault → Return Home
```

## 1. 음성 파이프라인
```
6CH Mic Array → ALSA/PortAudio → WebRTC AEC3 → GCC-PHAT(DOA 추정) → Delay-and-Sum Beamforming
  → RNNoise → 48kHz→16kHz Mono → Silero VAD(silero_vad.onnx) → Wake Word → STT
  → LLM/Intent Parser → Structured JSON → ROS2 Mission Manager → Nav2/MoveIt2/Robot Control
  → Response Text → TTS → Speaker (→ AEC3 Reference로 피드백)
```
- STT: Cloud=Azure AI Speech STT(ko-KR) / Local=`moonshine-ai/moonshine-base-ko`
- LLM: Cloud=`gemini-3.7-flash` / Local=`qwen3.5:2b`
- TTS: Cloud=Azure `ko-KR-SunHiNeural` / Local=Piper `ko_KR-kss-medium.onnx`
- Azure F0 무료 티어(원문 기준, 미검증): 실시간 STT 월 5시간, Neural TTS 월 50만 문자. Gemini 3.7 Flash도 Free Tier 있음.

Jetson Local 모델 표:

| 단계 | 모델/기술 |
|---|---|
| AEC | WebRTC AEC3 |
| DOA | GCC-PHAT |
| Beamforming | Delay-and-Sum |
| Noise suppression | RNNoise |
| VAD | Silero VAD ONNX |
| STT | moonshine-ai/moonshine-base-ko |
| LLM | qwen3.5:2b |
| TTS | ko_KR-kss-medium.onnx |

- Moonshine Korean Base ≈ 61M 파라미터, Jetson에서 돌리기 충분히 작음. **Moonshine Community
  License**라 상용화 시 라이선스 재확인 필요(원문 표기, 미검증).
- `qwen3.5:2b`(Ollama 기준) ≈ 2.7GB, 2.27B 파라미터. Jetson Orin Nano 8GB에서 실행은 가능하나
  다른 Vision/ROS 노드와 동시 실행 시 메모리 여유 확보 필요.

## 2. Mission / Behavior Pipeline
전체 시스템의 중심. **LLM이 로봇을 직접 제어하지 않는다.**
```
Voice → STT → LLM → JSON Mission → Mission Validator → Behavior Tree → ROS2 Actions
  ├── Nav2
  ├── Perception
  ├── MoveIt2
  └── TTS
```
JSON 예:
```json
{"action": "inspect", "zone": "A", "tasks": ["gauge", "stack_light", "valve", "foreign_object"]}
```
기술: BehaviorTree.CPP + Nav2 BT Navigator + ROS2 Action. Nav2 자체가 Behavior Tree 기반으로
NavigateToPose/recovery/docking/follow target 등을 조합하도록 설계되어 있음(원문 인용).

BT 구조:
```
MissionStart → BatteryCheck → NavigateToInspectionZone → Inspection(Gauge/LED/Valve)
  → ForeignObjectDetection → NeedManipulation?
      ├─ No → Continue
      └─ Yes → AlignRobot → PickObject
  → ReportResult → BatteryCheck → ReturnToBase
```
핵심 노드:
- Condition: `BatteryOK`, `TargetDetected`, `ManipulationRequired`, `MissionCancelled`
- Action: `NavigateToPose`, `InspectEquipment`, `DetectForeignObject`, `PickObject`, `SpeakResult`, `ReturnHome`
- Recovery: `ClearCostmap`, `Spin`, `BackUp`, `RetryDetection`, `AbortMission`

## 3. Localization / Navigation 파이프라인
```
LiDAR → /scan → SLAM Toolbox → /map → map→odom → Nav2 Costmap
IMU → /imu/data_raw ┐
                     ├→ robot_localization EKF → /odometry/filtered → odom→base_link
Wheel Odom → /odom_raw ┘
```
TF Tree: `map → odom → base_link → laser_link → camera_link → arm_base_link`
(이 프로젝트의 실제 TF Tree와 프레임 이름은 `AGENTS.md` "확정된 사실"과 `checklist` 4번 섹션 기준으로
맞춘다 — 예: `base_footprint`가 EKF 프레임, `lidar_frame`이 실제 스캔 frame_id 등, 이름이 다를 수 있음.)

| 역할 | 기술 |
|---|---|
| LiDAR SLAM | slam_toolbox |
| Localization | AMCL |
| Sensor Fusion | robot_localization/ekf_node |
| Global Planner | Nav2 Smac Planner 또는 NavFn |
| Local Controller | MPPI 또는 DWB |
| Collision Safety | Nav2 Collision Monitor |
| Recovery | Nav2 Behavior Server |

추천 Controller: 초기=DWB, 최종=MPPI Controller(Mecanum 기반 local trajectory 튜닝이 더 유연).

## 4. Wheel Odom / IMU 파이프라인
**현재 문제**: 공식 제품 설명은 magnetic encoder motor를 명시하지만, 현재 STM32 프로토콜에서는
encoder feedback이 ROS까지 올라오지 않는다(이 프로젝트에서 이미 확정된 사실, `AGENTS.md` 참고).

초기 구조: `/cmd_vel → STM32 → Motor`, `cmd_vel → Open-loop Odom`.

최종 목표(펌웨어 수정 후 — `checklist` "encoder feedback packet", `firmware/rrc_m4/` 프로젝트와 연결):
```
Encoder FL/FR/RL/RR → Wheel RPM → Mecanum Kinematics → vx,vy,wz → nav_msgs/Odometry
  → robot_localization EKF
```
EKF 입력: Wheel Odom(vx,vy) + IMU(angular_velocity.z) → `/odometry/filtered`.
초기엔 이미 검증된 대로 Open-loop vx/vy + IMU wz로 시작해도 된다.

## 5. RGB-D Camera Pipeline
Orbbec 공식 ROS2 Wrapper v2가 ROS2 Jazzy + NVIDIA Jetson ARM64를 지원(원문, 미검증 — 이 프로젝트는
현재 SDK v1 소스 빌드로 카메라를 쓰고 있음, `AGENTS.md`/`troubleshooting/013` 참고. v2로 옮길지는
별도 결정 사항).
```
Orbbec RGB-D Camera
  ├─ RGB → YOLO → BBox
  └─ Depth → Depth Map
        └─ Pixel Center(u,v) + depth → Camera Intrinsics → X,Y,Z → camera_link → TF2 → base_link/map
```

## 6. Object Detection Pipeline
추천 모델(초기/최종 공통): **YOLO11n**, TensorRT FP16 변환.
```
yolo11n.pt → ONNX → TensorRT FP16 → yolo11n.engine
```
Ultralytics는 Jetson에서 TensorRT를 권장 배포 방식으로 안내(원문). YOLO11n은 2.6M 파라미터 경량 모델.

클래스(너무 많이 넣지 않는다): `gauge, stack_light, valve, button, bolt, nut, tool, person`

## 7. Gauge Inspection Pipeline
Deep Learning을 끝까지 쓰지 않는 게 오히려 좋다.
```
Camera → YOLO11n(Gauge Detection) → Crop ROI → Perspective Correction → Gray/CLAHE
  → Circle Detection → Needle Detection → Angle → Value Mapping
```
모델: YOLO11n TensorRT(게이지 위치만 검출). 이후는 classical CV(OpenCV HoughCircles, HoughLinesP,
Contours). 예: Scale 0bar=220°, 5bar=-40°, needle=90° → pressure≈2.5bar. 결과가 explainable하고
데이터셋도 적게 필요해서 이 방식을 추천(원문).

## 8. Stack Light Pipeline
```
RGB → YOLO11n(stack_light detection) → ROI → HSV → Color Threshold → GREEN/YELLOW/RED
```
출력 예: `{"equipment":"machine_02","stack_light":"RED","status":"fault"}`
색상이 조명에 불안정하면 `YOLO11n-cls`를 보조 classifier로 붙인다. YOLO11은 Detection 외
Classification/Pose/Segmentation도 지원(원문).

## 9. Valve State Pipeline
초기(Classification이 가장 단순):
```
Camera → YOLO11n(Valve Detection) → Crop → YOLO11n-cls → OPEN/CLOSED
```
모델: `yolo11n.pt` + `yolo11n-cls.pt`. 나중에 방향까지 정확히 구하려면 `YOLO11n-pose`로 handle
endpoints를 keypoint로 학습: `Point A, Point B → Valve handle angle → OPEN/CLOSED`.

## 10. OCR Pipeline
설비 번호, 경고문, Label 등을 읽는다.
```
Camera → Text Detection → Perspective Correction → OCR → Text
```
Local: **PaddleOCR PP-OCRv5 Mobile** 계열 추천이나, PP-OCRv5는 중국어/영어/일본어 중심이고
공식 문서 주요 지원 범위에 한국어가 명시되어 있지 않음(원문, 미검증). 한국어 설비 라벨이 많다면
**RapidOCR + PP-OCRv3 Korean recognition**(사용자가 이미 써본 조합)이 초기 구현엔 더 안전.

## 11. Depth → 3D XYZ Pipeline
```
YOLO BBox → center pixel (u,v) → Depth Image → Z
  → X = (u-cx)*Z/fx,  Y = (v-cy)*Z/fy,  Z = depth
  → PointStamped(frame_id=camera_link) → TF2 → base_link
```
결과 예: `camera_link (0.12, -0.08, 0.54) → base_link (0.63, 0.18, 0.04)`. 이 좌표가 MoveIt2로 넘어간다.

## 12. Grasp Pipeline
```
Detection → Depth → 3D XYZ → TF2 → Object Pose → Pre-Grasp Pose → MoveIt2
  → Gripper Open → Approach → Gripper Close → Lift → Place
```
초기엔 복잡한 Deep Grasp model 없이 **Top-down grasp**부터: `grasp position = object XYZ`,
`grasp orientation = fixed downward quaternion`. 예: `bolt XYZ → pregrasp=Z+8cm → approach → close → lift`.
이 방식부터 성공률을 확보하는 게 맞다(원문).

## 13. MoveIt2 Pipeline
```
Object Pose → PoseStamped → MoveGroup → IK → Collision Checking → OMPL → Trajectory
  → Arm Controller → Servo Motors
```
기술: MoveIt2 + OMPL + RRTConnect. OMPL이 MoveIt2의 기본 motion planning backend로 많이 쓰이고
collision checking도 기본 수행(원문). 추천 Planner(초기): RRTConnect — 빠르고 설정 쉽고 6DoF arm에 충분.

## 14. Robot Alignment Pipeline
Manipulation 전에 모바일 베이스를 정확히 맞춘다. Mecanum 장점을 여기서 쓴다.
```
Target Detection → Depth XYZ → Desired Manipulation Pose → Error(x,y,yaw)
  → Mecanum Fine Alignment(±2~3cm) → Arm Planning
```
로봇팔 혼자 도달하려 하지 않고 `Navigation → Base Fine Alignment → Manipulation`으로 나눈다.

## 15. Human Detection / Audio-Visual HRI Pipeline
```
"제트로버" → Mic Array → DOA(θ=+70°) → Robot Rotate +70° → RGB → YOLO11n person → Depth
  → Person XYZ → Face Person → STT Conversation
```
사람을 따라가게 하려면: `Person Detection → Depth → map pose → GoalUpdater → Nav2 Follow Dynamic Point`.
Nav2에는 moving target pose를 계속 갱신하며 따라가는 **Follow Dynamic Point BT**가 공식 제공(원문).

## 16. Safety Pipeline
AI보다 확정적인 rule-based가 맞다.
```
LiDAR + Depth + Nav2 Costmap + Velocity → Safety Manager
```
조건: 장애물<1.0m→Slow, 장애물<0.5m→Stop, 위험구역 내 사람→Stop, 팔 이동 중→섀시 lock,
주행 중→팔 stow. Nav2에는 costmap과 별도로 실시간 collision checking을 수행하는
**Collision Monitor**가 있음(원문).

## 17. Battery / Power Pipeline
```
STM32 → Battery Voltage → /battery_state(sensor_msgs/BatteryState) → Power Manager
```
결정: Normal→Mission 허용 / Warning→신규 긴 Mission 금지 / Low→Mission 종료+Return Home /
Critical→Robot Stop+TTS+Buzzer.

최종 확장: `Battery Low → Nav2 → Docking Server → Dock Detection → Dock`. Nav2 Jazzy의 Docking
Server는 배터리 부족/미션 종료 후 docking task로 호출하도록 설계되어 있고 BatteryState도 활용
가능(원문). **JetRover에 자동 충전 접점이 기본으로 없다면 처음엔 Return-to-Base까지만 구현한다.**

## 18. Dashboard Pipeline
```
ROS2 Nodes → Bridge Node → FastAPI → WebSocket → React
```
Web UI에 필요한 것만: Robot State, Battery, Current Mission, Map Position, Camera, Inspection
Result, Fault, Mission History.

## 19. Jetson Orin Nano 8GB 모델 구성
**8GB에서 모든 모델을 동시에 GPU에 올리면 안 된다.**

| 기능 | 모델 | 실행 |
|---|---|---|
| Detection | YOLO11n TensorRT FP16 | GPU |
| Classification | YOLO11n-cls TensorRT FP16 | GPU |
| Depth | Orbbec Hardware Depth | Camera(모델 아님) |
| OCR | RapidOCR / PP-OCR Mobile | CPU/GPU |
| VAD | Silero VAD ONNX | CPU |
| STT | Moonshine Base Korean | CPU/GPU |
| LLM | qwen3.5:2b | GPU/shared RAM |
| TTS | Piper Korean | CPU |
| SLAM/Nav2 | ROS2 | CPU |
| MoveIt2 | ROS2 | CPU |

**핵심: Depth를 AI 모델로 돌리지 않는다.** Orbbec에서 실제 depth가 나오므로 Depth Anything/MiDaS/
YOLO depth 같은 모델은 필요 없다 — Jetson 자원 절약에 중요(원문).

## 20. Local Runtime 전략
모든 모델을 상시 실행하지 않는다.

- **Always On**: Nav2, SLAM/AMCL, EKF, TF, YOLO11n, VAD, Battery Monitor
- **On Demand**: STT, LLM, OCR, Valve Classifier, TTS, MoveIt2

예: `VAD speech detected → STT 실행 → LLM 실행 → 결과 생성 → LLM idle`,
`Inspection zone 도착 → OCR 실행 → 결과 → OCR idle`. 이래야 8GB 환경이 안정적이다(원문).

## 21. Cloud → Local 전환 구조
인터페이스를 통일해서 provider만 바꾼다.
```
stt/  azure_stt.py, moonshine_stt.py
llm/  gemini_llm.py, qwen_llm.py
tts/  azure_tts.py, piper_tts.py
```
설정 파일 예:
```yaml
# 초기 (Cloud MVP)
stt: {provider: azure}
llm: {provider: gemini}
tts: {provider: azure}
```
```yaml
# 최종 (Local Edge)
stt: {provider: moonshine}
llm: {provider: ollama}
tts: {provider: piper}
```

## 22. 최종 ROS2 데이터 흐름
```
Mic Array → /audio → voice_pipeline → /voice/intent → mission_manager → Behavior Tree
    ├── navigation    (LiDAR+IMU)
    ├── perception    (RGB-D → YOLO11n TRT → Depth)
    └── manipulation  (MoveIt2 → Arm)
    └─→ TF2 → mission_result → TTS(→Speaker) / Dashboard

Battery → power_manager → Mission Manager / Nav2
```

## 최종 추천 모델/기술 요약

| 파이프라인 | 최종 선택 |
|---|---|
| AEC | WebRTC AEC3 |
| DOA | GCC-PHAT |
| Beamforming | Delay-and-Sum → MVDR |
| Noise | RNNoise |
| VAD | Silero VAD ONNX |
| STT | Moonshine Base Korean |
| LLM | Qwen3.5 2B |
| TTS | Piper KSS Medium |
| Detection | YOLO11n TensorRT FP16 |
| Classification | YOLO11n-cls TensorRT FP16 |
| OCR | RapidOCR / PP-OCR Mobile |
| Depth | Orbbec Hardware Depth |
| SLAM | SLAM Toolbox |
| Localization | AMCL |
| Fusion | robot_localization EKF |
| Navigation | Nav2 |
| Controller | DWB → MPPI |
| Safety | Collision Monitor |
| Task Planning | BehaviorTree.CPP |
| Arm Planning | MoveIt2 + OMPL |
| Planner | RRTConnect |
| Backend | FastAPI |
| UI | React |
| Cloud STT/TTS | Azure Speech |
| Cloud LLM | Gemini 3.7 Flash |

이 구성이 Jetson Orin Nano 8GB에서 현실적으로 구현 가능하면서 ROS2+Navigation+Perception+
Manipulation+Edge AI+Audio AI+Embedded Control을 전부 포함하는 균형 잡힌 구성이라는 것이
원문의 결론이다. YOLO는 TensorRT로 배포하는 것이 Jetson에서 권장되는 방향(원문).
