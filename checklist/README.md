# 체크리스트

- 전체 항목은 [PROJECT_CHECKLIST.md](PROJECT_CHECKLIST.md)에 있다 (`[x]` 완료 · `[~]` 부분 완료 · `[ ]` 미완료).
- **작업을 끝낼 때마다** 해당 항목의 상태를 바꾸고, 새로 알게 된 사실(수치, 원인)을 항목 옆에 한 줄로 적는다.
- 오류를 만나면 [../troubleshooting/](../troubleshooting/)에 기록한다.

## 진행률 (2026-09-20 기준)

| 영역 | 상태 |
|---|---|
| Jetson/ROS2 개발환경 | 완료 |
| STM32 protocol 분석 | 완료 |
| Base driver | 거의 완료 |
| IMU | 완료 (gyro scale 97%, accel 스케일 보정은 보류) |
| Open-loop odom | 거의 완료 (바닥 주행 1차 완료: 전진·옆 이동은 명령과 일치(0.99), 회전은 명령의 81%) |
| EKF | 구현 완료 / 실주행 검증 남음 |
| **STM32 안정성** | **미해결 (hang 9회, 원인 미확정. RST 버튼으로 hang 상태에서도 즉시 복구 가능함을 확인(2026-09-23) — 이전 "버튼 안 통함" 기록은 정정됨. UART1에서 DTR=0&RTS=1이면 확실히 멈추지만(ISP 진입, Hiwonder 문서와 일치) 자동으로 정상 앱에 안 돌아와서 hang 자동 복구용으론 못 씀 — 이 경로는 닫음, RST만이 유일한 복구)** |
| TF/URDF | 부분 완료 (URDF 기본 트리, `base_footprint` 체계, 실제 로봇 TF 확인. 팔/카메라/실측 footprint 남음) |
| LiDAR | 동작 (`/scan` 14 Hz, TF·방향 검증 완료, `ch341` 드라이버 설치). 장시간 안정성 시험 남음 |
| SLAM | **키보드 조종 한 바퀴 완주, hang 없이 지도 완성** (posegraph 저장). loop closure 정량화, 표준 map 저장(nav2_map_server), 반복 주행은 남음 |
| AMCL, Nav2 | 미완료 |
| RGB-D 카메라 | **동작** (Orbbec DaBai DCW, SDK v1 소스 빌드로 해결. TF 연결·calibration 남음) |
| Vision AI, 3D Perception | 미완료 |
| MoveIt2, Grasp, Servo | 미완료 |
| Mission BT | 미완료 |
| FastAPI, React 관제, DB | 미완료 |
| RAG/Memory, Voice AI | 미완료 |
| 시스템 통합 | 미완료 |

## 지금 당장 남은 일
1. 전진을 더 길게(0.6 m 이상) 재측정하고 속도별(0.05/0.1/0.2 m/s)로 반복해서 스케일이 일정한지 확인
2. 더 긴 주행과 반복에서도 STM32 hang이 없는지 관찰
3. 그다음 URDF/TF → LiDAR → SLAM → Nav2
