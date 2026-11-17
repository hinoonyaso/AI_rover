# 임무 주행 단계 Gazebo 시험 (2026-11-16)

신뢰 수준: 시뮬레이션 실측. 실제 로봇·전체 임무·웹 임무 관리자 연동 시험이 아니다.

## 환경과 조건
- Jetson에서 Gazebo Harmonic headless, ROS Jazzy, `ROS_DOMAIN_ID=31`, `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`, Fast DDS. 외부 discovery peers와 사용자 DDS 설정은 제거했다. 도메인 25의 물리 로봇에는 명령하지 않았다.
- `jetrover_gazebo sim.launch.py gui:=false`; Nav2 `use_sim_time:=true`, `tools/nav/ab_params/nav2_params_mppi.yaml`, `precise_approach:=false`.
- 시험 스크립트는 Action 전송 전에 `GazeboSimSystem` 활성, `bt_navigator`의 시뮬레이션 시간, 진행하는 `/clock`, 도메인 및 로컬 검색을 확인한다. 실제 로봇 안전이나 격리 완전성을 보증하는 기능이 아니다.
- 알려진 Gazebo 시작점 `(1.02, 0.37, yaw 1.45 rad)`을 AMCL에 지정. 목표 `(1.00, 1.45, yaw 1.571 rad)`, `map` 프레임. 벽시계 제한 90초, Action 결과 확인. 위치 오차 수치는 AMCL TF이며 Gazebo ground truth 정량 검증이 아니다.

## 결과
1. 깊이 장애물 처리 기본값 `false`로 시작한 첫 시험은 Nav2 collision monitor가 요구하는 깊이 점군이 없어 정지를 보고했고, 90초 후 취소됐다(`status=5`). 첫 초기 위치 추정도 자동 스캔 매칭 0.798로 기준 0.8에 미달해 수동 초기화했다.
2. `depth_obstacles:=true`로 재기동한 뒤 위치 초기화 전송 타이밍을 개선했다. 시작 위치 TF `(1.02, 0.37)`를 확인하고 다시 목표를 전송했다. 충돌 감시는 점군과 레이저를 사용하며 구간별 50% 감속을 보고했다. 90초 후에도 목표 완료 결과가 없어 취소했다(`status=5`). 취소 후 AMCL 기준 위치 `(0.838, 1.475)`로, 목표 위치까지 약 0.164 m이고 yaw는 약 -0.148 rad였다.
3. 해당 위치에서 초기 자세를 덮어쓰지 않고 `--resume`으로 같은 목표를 다시 요청했다. **29.4초 후 Nav2 `status=4`(SUCCEEDED), `error_code=0`**을 받았다. 이는 별도 재시도 1회의 성공이며 최초 출발부터 90초 내 성공이 아니다.

깊이 소스의 타임스탬프가 1.027초 차이나 한 차례 충돌 감시가 정지 후 복귀한 로그와, 느린 시뮬레이션 시간·제어 주기 경고가 있었다. 두 현상의 원인과 성공률은 이 시험만으로 확정할 수 없다. 최종 위치·자세의 ground truth 오차 및 반복 성공률도 측정하지 않았다. 시뮬레이션 Nav2 Action을 직접 시험했으며 기존 모의 임무 관리자의 ROS 어댑터 연결, 임무 상태·DB/UI 전달 및 Stack Light 점검은 아직 없다.

시험 후 Gazebo와 Nav2 프로세스를 종료했고 기존 `jetinspect-dashboard`, `jetinspect-ros-monitor`, `jetinspect-camera` 서비스는 active였다. 관련 임시 로그: `/tmp/jetinspect-gazebo-logs/`(시스템 임시 파일이므로 영구 보존 보장 없음).
