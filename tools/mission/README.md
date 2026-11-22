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

## 경광등 녹화 영상 관측 (실험)

실물 경광등 없이 기존 녹화 영상의 색상별 영역을 지정해 관측기를 시험할 수 있다. 좌표는 영상 픽셀의 `x,y,너비,높이`이며 빨강·노랑·초록 각각에 대해 지정한다.

```bash
/usr/bin/python3 tools/mission/inspect_stack_light_video.py /path/to/video.mp4 \
  --red 10,20,20,20 --yellow 10,45,20,20 --green 10,70,20,20 \
  --start 0 --duration 3 --interval 0.5
```

출력은 색상별 `on`, `off`, `blinking`, `unknown`과 판정 이유, 표본 수·관측 시간을 포함한다. `--evidence-dir /path/to/existing-directory`를 지정하면 판정 영역을 표시한 첫·마지막 표본을 새 하위 폴더에 저장한다. 기존 파일은 덮어쓰지 않는다. 영상은 최대 1280×720, 표본은 최대 40개로 제한한다. 영상이 짧거나 시야가 가려져 근거가 부족하면 `unknown`이다. 이것은 기존 **가상 시험판용 임계값**을 녹화 영상에 적용하는 오프라인 진단이며, 실제 설비 판정 정확도·대시보드 연동 또는 로봇 주행 검증이 아니다. 원본 영상은 수정하지 않는다.

검증: `source /opt/ros/jazzy/setup.bash && /usr/bin/python3 -m pytest -q tools/mission/test_stack_light_video.py src/jetrover_perception/test/test_stack_light.py`

### 출처별 정답 비교

JSON 파일의 `cases`에 각 영상의 `id`, `source`(`synthetic` / `gazebo` / `real`), `video`, `regions`, `expected`를 적는다. 동영상 경로는 JSON 파일 기준 상대 경로나 절대 경로다. 다음은 형식 예시이며 실제 평가 결과가 아니다.

```json
{"cases": [{"id": "sample-1", "source": "synthetic", "video": "sample.mp4",
  "regions": {"red": [10, 20, 20, 20], "yellow": [10, 45, 20, 20], "green": [10, 70, 20, 20]},
  "expected": {"red": "on", "yellow": "off", "green": "on"}}]}
```

`/usr/bin/python3 tools/mission/evaluate_stack_light_videos.py /path/to/cases.json`으로 실행하면 출처별 일치 수·판정 유보·파일 오류를 분리해 출력한다. `source`는 사용자가 입력한 라벨이며 영상의 실제 출처를 자동 검증하지 않는다. 실제 영상이 준비되지 않으면 실제 성능은 평가하지 않는다.

합성 정상·깜빡임·짧은 영상·가림·모호한 밝기 사례는 `/usr/bin/python3 tools/mission/evaluate_stack_light_synthetic.py`로 재현할 수 있다. 이 결과는 합성 예제의 회귀 확인이며 실제 설비 정확도가 아니다.
