# 임무 Action 격리 시험

이 디렉터리는 실제 임무 관리자나 주행 실행기가 아니다. 전체 임무의 주행 단계에 사용할 Nav2 `NavigateToPose` 결과 처리 방식을 가짜 Action 서버로 검증하는 시험 도구다. 테스트 목표 `(1.0, 1.45, 0.0)`은 `map` 프레임(m, m, rad)의 시뮬레이션 시험값이며 실제 작업 지점이 아니다. 위치 유효성·장애물 회피·물리적 주행은 시험하지 않는다.

`fake_nav_adapter.py`는 `/mission_test_<임의 UUID 32자리>/navigate_to_pose` 형식 이외의 Action 이름을 거부하며, ROS 초기화 전에 도메인 31, localhost discovery, Fast DDS를 확인한다. 외부 피어·discovery server·DDS 사용자 설정 경로가 있으면 거부한다. 이 제약은 이 가짜 테스트에 한하며 실제 로봇 제어에 충분한 안전 보증이 아니다. 실제 `/navigate_to_pose` 연결, BT, 권한 및 웹 임무 관리자는 구현하지 않았다.

```bash
source /opt/ros/jazzy/setup.bash
env -u ROS_STATIC_PEERS -u ROS_DISCOVERY_SERVER -u FASTRTPS_DEFAULT_PROFILES_FILE \
  -u FASTDDS_DEFAULT_PROFILES_FILE -u CYCLONEDDS_URI \
  ROS_DOMAIN_ID=31 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST \
  RMW_IMPLEMENTATION=rmw_fastrtps_cpp \
  /usr/bin/python3 tools/mission/test_fake_nav_adapter.py -v
```

2026-11-15 Jetson: 격리 가짜 서버에서 성공, 실패, 목표 거부, 취소 확인, 취소 미확인, 서버 부재 및 격리 조건 거부 시험 통과. 타임아웃 시 취소 확인이 없으면 `unknown`으로 반환한다. 이 가짜 서버 시험 자체는 Gazebo/Nav2 주행을 검증하지 않는다. 이후 Gazebo 주행과 대시보드 연결 시험은 아래 기록을 참조한다. 실행 중 사용자 취소의 Gazebo 통합 시험, BT 및 영구 임무 DB는 미검증·미구현이다. 실제 로봇에 명령하지 않았다.

## Gazebo 시뮬레이션 주행 (2026-11-16)
별도 격리 시험 도구 `gazebo_nav_trial.py`는 하드웨어 확인과 시뮬레이션 시계 검증 후 알려진 Gazebo 목표 하나를 전송한다. 물리적 로봇이나 실제 임무의 안전을 보증하지 않는다. 결과·시행 조건과 재시도 한계는 `docs/benchmarks/sim/mission_navigation_20261116.md`를 참고한다. `--resume`은 앞선 취소 후 목표 반경 0.30 m 안에서만 같은 목표를 다시 보낸다.

2026-11-16: 대시보드 임무 API에서 격리 Gazebo Nav2를 실행하는 기능을 연결했다. 각 회차마다 시작점부터 초기화한 격리 반복 시험 2/2 성공. 상세와 제한은 `docs/benchmarks/sim/mission_dashboard_gazebo_20261116.md`.

`--inspection`을 `test_dashboard_gazebo.py`에 전달하면 격리 가상 시험판을 추가하고 주행 후 RGB 관측 결과를 SQLite에 저장하는 임무를 시험한다. `--inspection-browser`는 Firefox에서 임무를 시작하고 결과 표시까지 확인하며, `--inspection-cancel`은 점검 중 브라우저 취소를 확인한다. 두 경우 모두 가상 환경 전용이다. 자세한 결과와 실패 이력은 `prd/gazebo-stack-light-test-plan.md`. 이 임무는 `mode: gazebo`, `kind: inspect_stack_light`, 빈 `parameters`를 사용하며 관제 화면에서 선택할 수 있다.

추가 옵션 `--inspection-restart`, `--inspection-repeat`, `--inspection-inverted`는 각각 점검 중 관리자 재시작, 독립 Gazebo 3회 반복, 반전 색상 조합을 시험한다. ROS 영상 발행 중단은 별도 도메인 98에서 `test_observer_disconnect_ros.py`로 확인한다. 반복 시험의 세 번째 Nav2 기동은 시간 초과되어 원인 확인이 남아 있다.

`--inspection-bridge-loss`는 점검 중 실제 영상 수신을 확인한 뒤 해당 시험의 ROS-Gazebo 브리지를 종료해 실패 처리를 검증한다. 이때 카메라 외 `/clock` 등도 중단된다. `diagnose_nav2_restarts.py`는 주행 명령 없이 Gazebo와 위치 추정 관리자의 기동 및 노드 정리를 3회 확인하고 `/tmp`에 로그를 보존한다. 이 시험만으로 전체 Nav2 주행 관리자의 준비를 보장하지 않으며 기존 간헐 오류 원인은 아직 확정되지 않았다.

임무 통합 시험은 초기 위치 설정 후 위치 추정·주행 라이프사이클 관리자 양쪽의 활성화를 확인하며 실패 시 `/tmp/jetinspect-mission-failure-*`에 로그와 노드 상태를 보존한다. 간헐적으로 라이프사이클 서비스 응답 전송 시간 초과가 재현됐으나 원인은 아직 확정되지 않았다.
