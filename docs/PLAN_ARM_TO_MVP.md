# 실행 계획: 로봇팔 → MVP 데모 (ROADMAP 5~13단계 구체화)

작성 2026-10-08. 신뢰 수준: **계획**(아래 수치·추정은 실측 전). 상위 문서: [ROADMAP.md](ROADMAP.md).
각 단계에 **착수할 때** AGENTS.md 3-File System대로 `prd/<슬러그>.md` + `-test-plan.md`를 쓰고 체크리스트로 쪼갠다.
이 문서는 그 PRD들의 뼈대(무엇을, 어떤 순서로, 무엇으로 통과를 판정하는지)다.

## 0. 목표와 범위
MVP 데모 한 줄(ROADMAP): **음성 임무 → 점검 위치로 자율주행 → 설비 1종 판정 → 떨어진 부품 1종 Pick & Place → 결과 보고**.
- 점검 대상: **Stack Light 1종**. 조작 대상: **떨어진 부품 1종**(처음엔 색 블록, 나중에 실제 부품).
- 하지 않는 것(MVP 이후): Gauge/OCR/Valve/버튼 조작, 6D pose·grasp network, RAG, 풀 대시보드/DB, Visual Servoing.

## 1. 출발점 (2026-10-08 현재 사실)
| 영역 | 있는 것 | 없는/약한 것 |
|---|---|---|
| 팔 구동 | `base_node` FUNC5 읽기(5 Hz round-robin, 12 Hz 가능)/쓰기, `arm/command`·`arm/command_timed`, 토크, 홈 이동, 안전 클램프 | 관절 피드백이 느림(관절당 ~0.2~1.2 s), 서보 백래시 |
| MoveIt2 | `jetrover_manipulation`: SRDF/충돌 매트릭스, pick_ik, OMPL, `trajectory_bridge.py`(FollowJointTrajectory → base_node), 실기 소각도 왕복 4/4 | 큰 이동·위치 목표·그리퍼 컨트롤러 실기 미검증 |
| 카메라 | DaBai DCW RGB-D, registration 확인, 팔 끝(link4) 장착 = **eye-in-hand** | 장착 위치는 벤더 URDF 값(실측 아님), 손-눈 보정 없음 |
| 인식 | depth 장애물(기준 영상 차분), sparse cloud | 물체 검출/3D 위치 추정 없음 |
| 주행 | Nav2(DWB+RotationShim), AMCL 자동 초기화 | odom open-loop(엔코더 단계 2~3 대기), 회피 정량 미측정 |
| 음성 | 마이크 어레이(card 0)·스피커(card 1) 확인 | 엔진 미설치. 참고: `~/AI_secretary_robot/src/ai/*`(wake/VAD/STT/intent/LLM/TTS C++, Humble) |
| 시스템 | 진단 일부(배터리, STM32 heartbeat) | CPU 여유 부족(Nav2+카메라만으로 load 5~11), 자동 기동/로그 없음 |

## 2. 전체 흐름과 의존성
```
[1단계 Nav2 baseline] ─▶ [2~3 엔코더 odom] ─▶ [4 DWB vs MPPI]
                                                   │ (주행 정확도는 11단계 접근에 필요)
[5 팔 제어 경로 확정] ─▶ [6 MoveIt 관절/자세 이동] ─▶ [7 RGB-D→XYZ→TF + 손-눈 검증] ─▶ [8 색 블록 Pick&Place(정지 상태)]
                                                   ─▶ [9 YOLO/TensorRT] ─▶ [10 Stack Light 판정]
[8]+[10]+[주행] ─▶ [11 Mission BT(CLI)] ─▶ [12 Voice] ─▶ [13 최소 관제 화면] ─▶ MVP 데모 + KPI 시험
공통(단계마다): 안전/배터리 · CPU/메모리 예산 · rosbag/진단
```
5~8은 주행(1~4)과 **독립적으로 로봇을 세워 둔 채** 진행할 수 있다. 11단계부터 둘이 합쳐진다.
(ROADMAP은 "팔 PRD는 3·4단계 이후"다. 엔코더 장비 대기 중 5~7 병행은 7절의 **제안**이며 사용자 승인 전에는 ROADMAP 순서를 따른다.)

## 3. 단계별 계획

### 5단계 — 팔 제어 경로 확정 (설계 + L2)
**목표**: MoveIt이 팔을 움직이는 경로를 하나로 확정한다.
**결정할 것(PRD에서)**:
- A) **현행 유지**: `trajectory_bridge.py` → `base_node arm/command_timed`. 이미 실기 통과, 시리얼을 base_node 하나가 소유하는 구조와 맞음.
- B) **ros2_control**: `hardware_interface` + `joint_trajectory_controller`. 표준이지만 RRC 시리얼을 base_node와 나눠 써야 해서
  base_node를 `rrc_transport`/`base_drive`/`arm`으로 먼저 분리해야 한다(ROADMAP "하지 않는 것"과 연결).
- **추천: MVP는 A**, B는 MVP 이후 PoC 브랜치. 판단 근거를 PRD에 남긴다.
**작업**:
1. 관절 피드백 속도: `arm_poll_hz` 12 Hz 고정 시 시리얼 부하/IMU 손실 측정(L2), 문제 없으면 기본값으로.
2. 그리퍼 경로: `gripper_controller`를 브리지에 연결(열림/닫힘 2개 자세, 파지 확인용 그리퍼 위치 읽기).
3. 브리지 안전장치 재점검: 관절 한계·스텝 제한·추종 지연·취소 시 hold — 단위시험 유지.
**게이트**: RViz/스크립트 목표 10회 연속 성공(관절 오차 ≤ 0.05 rad), 그리퍼 열고닫기 10/10, 시리얼 오류/IMU 끊김 0.

### 6단계 — MoveIt2 관절/자세 이동 (L2~L3, 팔만)
**목표**: 인식 없이, 이름 붙인 자세와 위치 목표로 팔을 안정적으로 움직인다.
**작업**:
1. 이름 자세(SRDF): `home`(주행), `look_down`(바닥/작업면 관찰), `look_forward`(Stack Light 관찰), `pregrasp_ready`, `stow`.
   `home`은 1단계 1-2(홈 자세 재설계) 결과를 쓴다.
2. PlanningScene: 차체·LiDAR·카메라 박스, 바닥 평면(z=0) 충돌 객체 추가 → 팔이 차체/바닥을 치는 경로 금지.
3. 5자유도 한계 정리: 위치+손 방향 중 **top-down(손끝 아래 방향) 파지 자세**가 도달 가능한 작업 영역 지도 작성
   (x, y 격자 × 높이에서 IK 성공 여부 → 표/그림). pick_ik 가중치 또는 top-down 전용 해석적 IK 중 선택.
4. 속도/가속 스케일 기본값(0.3) 유지, 배터리 ≥ 10.5 V에서만.
**게이트**: 이름 자세 간 이동 20/20, 작업 영역 내 위치 목표 20회 중 ≥ 18 성공·위치 오차 ≤ 1.5 cm(TF 기준), 충돌 0.
**산출물**: 작업 영역 지도(`docs/benchmarks/manipulation/workspace.md`).

### 7단계 — RGB-D → XYZ → TF + 손-눈 검증 (L2)
**목표**: 화면 속 점 하나를 로봇 기준 좌표로 정확히 바꾼다(8·10단계의 기반).
**작업**:
1. `jetrover_perception`에 `pixel_to_base` 유틸: (u,v) 주변 ROI depth **중앙값**(무효 0 제외) → 역투영 → TF(이미지 시각의 관절 상태).
2. **eye-in-hand 주의**: 카메라가 팔에 있으므로 관찰 자세에서 **팔이 정지한 뒤** 프레임을 쓴다(관절 피드백이 느려 움직이는 중 TF가 틀림).
   관찰 → 정지 대기(관절 변화 < 0.01 rad, 0.5 s) → 캡처 순서를 함수로 고정.
3. 정답 기준: AprilTag(apriltag_ros, 인쇄 태그) 또는 줄자로 놓은 물체 9곳(3×3 격자, 0.25~0.40 m 앞).
4. 오차가 크면(> 2 cm) 손-눈 보정: 카메라 장착 변환(`camera_connect_link`)을 측정값으로 보정(easy_handeye2 또는 태그 기반 최소제곱).
5. 장기 과제 연결: 기준 depth 차분 대신 TF/URDF self-filter + 바닥 제거(처음 외부 분석 제안) — 이 단계의 역투영 코드를 재사용.
**게이트**: 9곳 × 5회, 평균 오차 ≤ 1.5 cm, 반복 표준편차 ≤ 0.5 cm.
**산출물**: 오차 표 + 보정 전/후 비교(포트폴리오 Before/After 후보).

### 8단계 — 색 블록 Pick & Place, 로봇 정지 상태 (L3)
**목표**: 바닥(또는 낮은 받침) 위 색 블록 1개를 집어 정해진 곳에 놓는다. YOLO 없이 색으로 검출해 조작 파이프라인만 검증한다.
**작업**:
1. 검출: HSV 마스크 → 가장 큰 덩어리 → 중심(u,v) + `minAreaRect` 각도 → 7단계로 base 좌표 + yaw.
2. 파지 계획: top-down. `pregrasp`(블록 위 +8 cm) → 하강 → 그리퍼 닫기 → 들기(+10 cm) → 놓을 위치 → 열기 → `home`.
   5자유도라 손목 yaw = 블록 yaw(90° 대칭 활용).
3. 파지 확인: 그리퍼 서보 위치가 "완전히 닫힘"보다 덜 닫혔으면 잡음 + 들어 올린 뒤 관찰 자세에서 블록이 사라졌는지 확인.
4. 실패 처리: 미검출 → 관찰 자세 바꿔 재시도 1회 / 파지 실패 → 재계획 1회 → 포기 후 `home`.
5. 시험 도구: `tools/manipulation/pick_trial.py`(1회 실행 + 결과 CSV, straight_trial.py와 같은 형식).
**게이트**: 30회 ≥ 85%(PRD KPI), 1회 ≤ 40 s, 차체/바닥 충돌 0.
**하드웨어 준비**: 색 블록(2.5~3 cm, 그리퍼 개폐 폭 안), 무광 바닥 또는 받침판.

### 9단계 — YOLO/TensorRT (Jetson)
**목표**: Stack Light와 대상 부품을 실시간 검출한다.
**작업**:
1. 데이터: 로봇 카메라로 직접 수집(각 클래스 300~500장, 거리/각도/조명 다양), CVAT/Roboflow로 라벨링. 클래스 2~3개(`stack_light`, `part`).
2. 학습: host PC에서 YOLO nano급(v8n/11n) → ONNX → Jetson에서 `trtexec` FP16 엔진.
   **빌드는 `MAKEFLAGS=-j2`, 메모리 감시**(AGENTS: 메모리 부족으로 시스템 정지 이력).
3. ROS 노드: `/detections`(vision_msgs/Detection2DArray), 입력 축소(640×360 그대로), 필요할 때만 켜는 lifecycle 노드.
4. **CPU/GPU 예산 측정**: Nav2 + 카메라 + YOLO + MoveIt 동시 실행 시 CPU load, RAM, 온도, 컨트롤러 주기(10 Hz 유지되는지).
   부족하면: 주행 중 YOLO 끄기, sparse cloud 주기 낮추기, colorizer 등 시험 노드 금지.
**게이트**: 검증 셋 mAP50 ≥ 0.8, ≥ 15 FPS, 지연 ≤ 70 ms, 동시 실행 시 DWB 10 Hz 유지·RAM 여유 ≥ 1 GB.

### 10단계 — Stack Light 판정
**목표**: 신호등의 색별 점등 상태(꺼짐/켜짐/깜빡임)를 판정한다.
**작업**:
1. 검출 bbox → 세로로 색 구간 분할 → 구간별 HSV 밝기(V)·채도 → 켜짐 판정(자동 노출 고정 필요 여부 확인).
2. 깜빡임: 2~3 s 창에서 밝기 시계열의 on/off 전환 횟수.
3. 결과 메시지(`InspectionResult`: 대상, 상태, 신뢰도, 근거 이미지 경로).
**게이트**: 상태 조합 × 거리 2종 × 조명 2종, 50회 ≥ 90%(PRD KPI).
**하드웨어 준비**: 저렴한 USB/12 V 타워 램프(색 3단, 깜빡임 가능) — 구매 필요.

### 11단계 — Mission BT (CLI로 end-to-end)
**목표**: 음성 없이 명령 한 줄로 전체 임무를 수행한다.
**작업**:
1. 장소 지도(semantic map) YAML: `inspection_point`, `drop_zone`, `pick_area`, `home` 각각 (x, y, yaw) — DB는 나중.
2. BehaviorTree.CPP v4(Nav2와 같은 버전) 노드: `CheckReady`(배터리·센서·팔 홈·위치 추정 신뢰도) → `NavigateTo` →
   `ArmPose(look_forward)` → `InspectStackLight` → `NavigateTo(pick_area)` → `DetectPart` → `Pick` → `Place` → `ArmPose(home)` → `Report`.
3. 각 기능은 action server로 감싼다(BT는 호출만): `/inspect`, `/pick_place`, Nav2 `/navigate_to_pose`.
4. 복구: 검출 실패 → 자리 조정 후 재시도 / 주행 실패 → 재계획 1회 / 반복 실패 → 중단 + `home` + 보고. 비상정지·취소는 어디서든 즉시.
5. 접근 정밀도: Nav2로 근처(±10 cm)까지, 마지막은 카메라 재검출로 보정(open-loop odom 오차 흡수; 엔코더 단계 결과에 따라 조정).
6. 실행: `ros2 action send_goal /mission ...` 또는 `tools/mission/run.py`.
**게이트**: 연속 10회 중 ≥ 8 성공 → KPI 시험 20~30회 ≥ 85%(PRD).

### 12단계 — Voice
**목표**: 한국어 음성으로 임무를 시작·취소한다.
**작업**:
1. `~/AI_secretary_robot/src/ai/*`(wake/VAD/STT/intent/TTS, C++/Humble)를 Jazzy로 이식할지, 경량 대안(Vosk/whisper.cpp + 규칙 기반 intent)을 쓸지 PRD에서 비교.
2. 명령 세트 고정(약 10개): "점검 시작", "부품 치워", "취소", "정지", "홈으로", "상태 알려줘" 등. **STOP/CANCEL/HOME은 LLM 없이 키워드로 즉시 처리.**
3. 결과 보고 TTS("빨간 램프 깜빡임, 부품 회수 완료").
4. LLM은 MVP에서 선택 사항(바꿔 말하기 대응). 넣는다면 출력은 고정 JSON 스키마만 허용.
**게이트**: 명령 50회(화자 2명, 1~2 m) intent ≥ 90%, "정지" 인식→정지 ≤ 1 s, 오인식으로 임무 시작 0.

### 13단계 — 최소 관제 화면
**목표**: 상태 확인과 비상 조작에 필요한 것만.
**작업**: FastAPI 1개 + 정적 웹 페이지 1장 — 배터리, 위치/지도 스냅샷, 현재 임무/BT 노드, 카메라, 최근 판정 결과, **정지/취소 버튼**.
React/DB/RAG는 MVP 이후. 로봇 화면(HMI)은 같은 페이지를 kiosk로.
**게이트**: 같은 네트워크 PC/폰에서 상태 1 Hz 갱신, 정지 버튼 → 정지 ≤ 1 s.

## 4. 단계 공통 작업 (각 단계 게이트에 포함)
- **안전/배터리**: 팔·주행 시험은 배터리 ≥ 10.5 V(팔은 저전압에서 처짐), 임무 시작 시 배터리 확인, 비상정지 경로 시험(BT 취소, 키보드, 웹).
  STM32에 host timeout이 없다는 사실(AGENTS) 유지 — host watchdog 의존. 자체 펌웨어(2단계)에서 timeout + 정지 시 PWM 차단(바퀴 울림 032) 같이 해결.
- **자원 예산**: 단계마다 CPU load/RAM/온도/컨트롤러 주기를 기록(`docs/benchmarks/system/`). 2026-10-07에 이미 load 11로 DWB가 3 Hz까지 떨어진 적 있음.
- **로그**: 시험 스크립트는 CSV + 필요 시 rosbag(`tools/nav/benchmark` 형식). 임무 시작/종료 자동 rosbag은 11단계에서.
- **문서**: 단계마다 PRD/test-plan, 실패는 troubleshooting, 수치는 checklist와 benchmarks. 커밋 규칙은 AGENTS "Git 규칙".

## 5. 준비물(구매/제작)
| 물품 | 단계 | 비고 |
|---|---|---|
| ST-Link | 2 | 자체 펌웨어 flash(ROADMAP 대기 항목) |
| AprilTag 인쇄물(36h11, 여러 크기) | 7 | 3D 위치 정답 |
| 색 블록 3~5개(2.5~3 cm) | 8 | 그리퍼 개폐 폭 확인 후 크기 확정 |
| 타워 램프(3색, 깜빡임) | 10 | 전원 방식(USB 권장) |
| 대상 부품 실물 1종 | 9·11 | 블록 다음 단계 |
| 충전기/여분 배터리 | 전부 | 시험 시간 확보(오늘처럼 9.4 V에서 중단) |

## 6. 위험과 대응
| 위험 | 영향 | 대응 |
|---|---|---|
| 5자유도라 top-down 파지 가능 영역이 좁음 | 8단계 성공률 | 6단계 작업 영역 지도로 미리 확인, 주행으로 위치 맞추기(11) |
| eye-in-hand + 느린 관절 피드백 | 3D 오차 | 정지 후 캡처 고정(7), 필요 시 `arm_poll_hz` 12 Hz |
| 벤더 URDF 카메라 장착값 오차 | 3D 오차 | 7단계 손-눈 검증/보정 |
| 서보 백래시 | 파지 위치 오차, depth 기준 영상 | 접근 방향 통일, 파지 확인, 장기적으로 기준 영상 대신 self-filter |
| Jetson 자원 부족 | 주행 불안정 | 9단계 예산 측정, 기능별 on/off(lifecycle) |
| open-loop odom | 접근 위치 오차 | 2~3단계 엔코더, 마지막은 시각 재검출 |
| 시험 시간(배터리) | 반복 횟수 부족 | 충전 계획, 팔 시험과 주행 시험 분리 |

## 7. 진행 방식
- 기본 순서(ROADMAP 그대로): 1단계 마무리 → 2~3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13.
- **제안(미승인)**: ST-Link 도착 전까지 2~3단계가 막혀 있으면 그 사이에 5~7단계(팔·인식, 로봇 정지 상태)를 병행한다.
  주행과 독립이고 개발 순서의 취지(핵심 통합 우선, 음성 나중)는 지킨다. 승인되면 ROADMAP에 반영한다.
- 단계마다 게이트 수치를 checklist에 남기고, 통과 못 하면 다음 단계로 가지 않는다.
- 이 문서와 ROADMAP이 어긋나면 ROADMAP을 먼저 고치고 이 문서를 맞춘다.
