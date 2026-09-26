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
- [~] STM32 hang 진단 (**7회 발생**, 7차는 완충(~12 V) 상태에서 주행 직후 idle 몇 분 만에 발생 → 저전압 단독 가설 약화. 6차는 주행 중 배터리 9.47 V 실측, 4·5차는 모터 정지 상태에서 전원 재시작 후 약 20~50분, 전원 재시작으로만 복구, 원인 미확정. 3차는 바닥 6초 주행 직후. 충전 직후 11.5 V였으나 hang 시점 전압 미측정, 재부팅 후 무부하 10.5 V → 저전압 배제 못 함)
- [x] STM32 heartbeat monitor (1초 이상 packet 미수신 감지)
- [~] **완충(12.05 V, 2026-09-22) 확인. 완충 상태 주행 1회(한 바퀴)에서 hang 재현 안 됨** → 저전압 가설 강화(미확정, 1회 관측). 정지 상태 장시간(20~50분) 재시험은 아직
- [x] `/battery_state` 발행 (STM32 배터리 패킷 → `sensor_msgs/BatteryState`, 10 V 미만이면 경고) — hang 시점 전압을 남기기 위함
- [x] hang 진단 도구/기록 (`tools/stm32_diagnostics/`)
- [x] 펌웨어 `.hex` 정적 분석 (IWDG 약 20 ms, `app_task`가 먹이 → 다른 태스크만 막히면 못 잡을 수 있음)
- [ ] STM32 hang 근본 원인 규명
- [ ] MCU 자체 motor command timeout (현재 없음, 13초 확인)
- [ ] task-health 기반 watchdog
- [ ] UART DMA recovery
- [ ] encoder feedback packet (공식 프로토콜에 없음 → 펌웨어 개발 필요)
- [ ] 자체 STM32 firmware 개발 (소스 없음: Hiwonder에 요청 또는 SWD 디버깅). **재플래시 시도는 중단** — 받은 파일이 기존 분석 파일과 동일(효과 없음), ISP UART1 포트 미확인(두 번째 CH340은 게임패드 동글로 확인됨)
- 가장 중요한 미해결 문제는 STM32 firmware hang이다. host 측은 감지·정지 시도까지만 가능하고,
  STM32 자체가 먹통이면 정지 명령을 처리하지 못하므로 완전한 fail-safe가 아니다.

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
- [~] JetRover URDF: `src/jetrover_description/urdf/jetrover.urdf` (일반 URDF, xacro 미설치). Hiwonder 공식 치수 사용, 형상은 임시 도형, 팔 링크/카메라/실측 footprint는 아직
- [x] base_footprint (EKF 프레임 = `odom → base_footprint`), [x] base_link (URDF `base_joint`, z 0.116)
- [x] IMU frame 개념 확정
- [x] imu_link (URDF `imu_joint`, 회전 없음, translation은 Hiwonder 값)
- [~] lidar_link (URDF, Hiwonder 값 앞 9.0 cm / 위 4.05 cm). LiDAR 장착 위치 실측과 모델 확인은 아직
- [ ] camera_link, RGB optical frame, Depth optical frame
- [~] arm_base_link (URDF, Hiwonder 값). Robot arm URDF 통합은 아직
- [x] robot_state_publisher (`jetrover_description/launch/description.launch.py`, `base.launch.py`에 포함)
- [ ] RViz RobotModel 검증
- [~] TF tree 검증: 실제 로봇에서 `odom→lidar_link`, `odom→imu_link` 체인 확인. RViz RobotModel과 view_frames는 아직

## 5. LiDAR (RPLIDAR A1, 사용자 확인)
- [x] USB/serial 인식 — `drivers/ch341/`의 모듈을 설치해서 `/dev/ttyUSB*` 생성, **재부팅 후에도 자동 로드 확인**. `ttyUSB0/1` 번호는 재부팅마다 바뀌므로 by-path(`...usb-0:2.1.4:1.0-port0`)로 지정 (GET_INFO로 A1M8 fw 1.29 확인, 헬스 Good)
- [x] Jazzy driver: `ros-jazzy-rplidar-ros` 설치됨 (A1은 115200 baud 예상, 실제 시험은 포트가 생긴 뒤)
- [x] /scan (`jetrover_bringup/launch/lidar.launch.py`), frame_id `lidar_frame` (URDF에서 `lidar_link` 기준 yaw 180°)
- [x] scan frequency 약 14 Hz = **실제 회전 속도**(time_increment×720 = 74.7 ms와 일치; 이 어댑터가 A1 모터를 최대 속도로 돌리는 것으로 추정, 드라이버에 속도 파라미터 없음). 각도 해상도 약 0.64°, 720 bin(0.5°), 범위 0.15~12 m
- [x] 유효 포인트 50%의 원인: **스캔 −72°~+90°(로봇 기준 뒤쪽 약 160°)가 로봇팔 기둥/몸체에 가려짐**. 나머지 구간은 빈틈 거의 없음 → SLAM은 앞쪽 약 200°만 본다. 범위 정확도 검증은 아직
- [~] RViz(사용자 환경은 VS Code SSH라 화면 없음 → `tools/viz/snapshot.py`로 PNG 저장해서 확인, 실시간은 Foxglove 권장): `jetrover_bringup/rviz/jetrover.rviz`(Grid, RobotModel, TF, LaserScan, Odometry; 고정 프레임 odom)와 `rviz.launch.py`. 로봇 화면(:0)에서 12초 시작해 설정 오류 없음 확인, 실제 화면 확인은 사용자 몫
- [x] base_link → lidar_link → lidar_frame TF (URDF, 실제 스캔으로 방향 검증: 정면 물체 +9°(배치 오차 추정), 왼쪽 물체 +90°/+89° → 좌우 반전 없음, 재부팅 후 재확인)
- [ ] 로봇 회전하면서 scan 정합 확인
- [ ] 장시간 USB 안정성 시험
- 완료 기준: RViz에서 RobotModel + /scan + /odom + TF 모두 정상

## 6. SLAM (SLAM Toolbox: 2D scan matching + pose graph + loop closure)
- [x] slam_toolbox 설치 (사용자 sudo로 설치 완료). 설정/launch: `jetrover_navigation`
- [x] async mode 결정 (online async, `config/slam_toolbox_online_async.yaml`: base_footprint, 12 m, 작은 움직임에도 갱신)
- [x] /scan, /odom 연결: 정지 상태에서 `slam_toolbox` active, `/map` 발행(0.05 m), `map→base_footprint` TF 정상, 경고 없음
- [x] map 생성: **키보드 조종 한 바퀴 완주, hang 없이 사각형 방 지도 완성** (`tools/viz/out/lap1_final.png`), 로봇이 출발 지점으로 복귀
- [ ] loop closure
- [~] map 저장: `slam_toolbox serialize_map`으로 `~/jetrover_ws/maps/lap1_20260922.{posegraph,data}` 저장 성공. `nav2_map_server` 미설치라 표준 `.pgm/.yaml`(`save_map`)은 실패 — 필요시 `sudo apt install ros-jazzy-nav2-map-server`. map 재로드는 아직
- [ ] 긴 복도 테스트, 반복 주행 map distortion 확인
- [ ] 성능 기록: loop closure error, 벽 직선성, 재방문 위치 오차, CPU/RAM

## 7. Localization (map_server + AMCL, Mecanum이므로 OmniMotionModel 검토)
- [ ] Map Server
- [ ] AMCL
- [ ] Omni motion model
- [ ] Initial Pose
- [ ] /amcl_pose
- [ ] map → odom
- [ ] kidnap/relocalization test
- [ ] localization error 측정

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
- [ ] Arm driver
- [ ] URDF, SRDF, joint limits
- [ ] IK
- [ ] MoveIt Setup Assistant
- [ ] PlanningScene, Collision model
- [ ] RRTConnect, Pose goal
- [ ] 실제 arm trajectory
- [ ] Gripper

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

## 21. Database (PostgreSQL + SQLAlchemy, RAG용 pgvector)
- [ ] missions, robot_events, detections, system_metrics, alerts
- [ ] locations, documents, document_chunks

## 22. Semantic Map (desk, charger, door, delivery_station, storage)
- [ ] 장소 이름, x, y, yaw, type, description
- 목표: "책상으로 가" → LLM → desk → DB(x,y,yaw) → Nav2

## 23. LLM / VLM
- LLM: [ ] 자연어 명령 분석 · [ ] Structured JSON · [ ] Mission 생성 · [ ] Tool calling · [ ] BT에 parameter 전달
- VLM: [ ] Scene understanding · [ ] Target disambiguation · [ ] 이미지 질의응답 · [ ] object semantic 판단
- 원칙: VLM → What?, YOLO + Depth → Where?

## 24. RAG (Document → Chunk → Embedding → pgvector → Top-K → LLM)
자료: JetRover manual, STM32 protocol, STM32 hang NOTES, Nav2 config, MoveIt setup, Camera/LiDAR manual, Troubleshooting, Calibration 기록
- [ ] Document loader, Chunker, Embedding
- [ ] pgvector, Metadata, Retrieval
- [ ] Reranking 필요 여부 검토
- [ ] RAG API
- [ ] 관제 UI Chat

## 25. Robot Memory
- [ ] Mission memory, Detection memory, Object-location memory
- [ ] Error history, Robot event history
- [ ] 자연어 검색

## 26. Voice AI (Mic → VAD → STT → LLM/Intent → BT → Robot → TTS)
- [ ] Microphone, VAD, STT, Intent Router, LLM, TTS, Speaker
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
