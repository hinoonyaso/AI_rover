# JetInspect-M 관제·기록 개발 환경

같은 Wi-Fi의 PC 또는 Jetson 브라우저에서 `https://172.30.1.82:8765/`를 열어 로그인한다. 서버는 이 Wi-Fi IP에만 바인딩하고 `172.30.1.0/24`의 클라이언트만 허용한다. 실제 로봇은 읽기 전용이며 모의 임무와 격리 Gazebo 임무를 실행할 수 있다. 모터·팔 제어 및 비상정지는 제공하지 않는다.

초기 계정은 `operator`(조회·모의/Gazebo 임무 실행)와 `viewer`(조회 전용)다. 로그인한 사용자는 왼쪽 계정 영역의 **비밀번호 변경**에서 현재 비밀번호를 확인한 후 12자 이상의 새 비밀번호로 바꿀 수 있다. 변경하면 해당 계정의 모든 세션이 종료되며 새 비밀번호로 다시 로그인한다. 초기 암호 파일은 변경 후 자동 갱신되지 않는다. 최초 암호는 Jetson 사용자만 읽을 수 있는 `~/.local/share/jetinspect-ops/auth/initial-passwords.txt`에 있다. 다음 명령으로 각 암호를 변경한 뒤 대시보드를 재시작하면 기존 세션이 만료된다.

HTTPS는 자체 서명 인증서이므로 다른 PC의 브라우저에 처음에는 신뢰 경고가 표시된다. Jetson에서 아래 명령으로 SHA-256 지문을 확인하고, 브라우저에 표시된 인증서 지문과 비교한 뒤 해당 인증서를 신뢰하거나 예외를 추가한다. 인증서가 바뀌거나 지문이 다르면 접속하지 말고 원인을 확인한다. 공개 인증서는 `~/.local/share/jetinspect-ops/tls/dashboard.crt`이며 개인 키 `dashboard.key`는 공유하지 않는다.

```bash
openssl x509 -in ~/.local/share/jetinspect-ops/tls/dashboard.crt -noout -fingerprint -sha256
```

IP가 바뀌면 바인딩 주소와 인증서가 기존 주소에 묶여 있어 설정을 다시 만들어야 한다. 가능하면 라우터에서 Jetson의 IP를 고정 할당한다. 설정 생성 도구는 `python3 ~/jetrover_ws/tools/ops/setup_lan_https.py --address <Jetson IP> --network <대역/CIDR>`이며, 기존 TLS 파일은 덮어쓰지 않는다.

```bash
~/.local/share/jetinspect-ops/venv/bin/python ~/jetrover_ws/tools/ops/backend/setup_auth.py password operator
~/.local/share/jetinspect-ops/venv/bin/python ~/jetrover_ws/tools/ops/backend/setup_auth.py password viewer
systemctl --user restart jetinspect-dashboard
```

- Python 3.12 전용 venv: `~/.local/share/jetinspect-ops/venv`, 패키지 버전은 `requirements.txt`.
- Node.js v24.11.1 ARM64: `~/.local/share/jetinspect-ops/node`, React/Vite 의존성은 `frontend/package-lock.json`.
- MySQL 8.0.46 ARM64: `~/.local/share/jetinspect-ops/mysql`, 데이터는 `mysql-data`. 공식 아카이브 MD5 `62376634565907ec31b74da3bc645b2b`. Ubuntu `libaio1t64` 0.3.113-6build1.1은 사용자 폴더에 추출 후 `libaio.so.1` 링크로 사용(패키지 SHA-256 `43ddf90a93e31a949d554bf29f65f23fd1ad6ce40bc694efede9bc970e0849f0`). 시스템 패키지는 변경하지 않았다.
- MySQL은 TCP를 끄고 권한 700의 사용자 전용 소켓 디렉터리를 사용한다. 로컬 root 계정은 암호가 없으므로 이 Linux 사용자 계정 및 root 권한을 가진 프로세스는 DB에 접근할 수 있다. 다중 사용자나 운영망 공개용 설정이 아니다.
- DB `jetinspect`: `system_metrics`는 60초마다 저장하며 7일 보존, `robot_events`는 현재 관제 서버 시작 이벤트를 기록한다. 모의/Gazebo 임무와 상태 이력은 별도 테이블에 보관하며 일반적인 detection 수집은 미구현이다.
- ROS 도메인 25의 `/battery_state`, `/imu/data_raw`, `/scan`, `/depth_cam/color/image_raw`를 구독만 한다. 배터리 전압과 최근 수신율을 표시하며 수신이 없거나 상태가 오래되면 미확인으로 표시한다. 센서 미수신은 로봇 고장의 증명이 아니다. 실시간 미션·맵·Nav2 상태는 아직 연결하지 않았다. 카메라는 아래 미리보기로만 표시한다.

## 대시보드 표시

화면은 호스트 지표, DB와 ROS 모니터 상태, 배터리 전압, IMU·LiDAR·카메라 토픽별 수신율과 경과 시간, 최근 지표 이력과 운영 기록을 표시한다. 수신 표본이 부족하면 주기 계산 중으로, 데이터가 만료되면 미확인으로 표시한다. 모니터 스냅샷은 8초, 센서 자료는 10초 미만일 때 유효하다. 기준은 개발용이며 실기 검증 전이다. DB 기록 시각의 시간대는 아직 확인되지 않았다. 상세 계약은 `DATA_CONTRACT.md`를 참고한다.

2026-11-15: 가상 스냅샷 API 단위 시험 4건, 가상 상태의 React 서버 렌더링 정상·만료·오류·복구 확인, Vite 빌드 및 localhost 상태 API 확인. 이는 브라우저 상호작용이나 실제 센서 시험이 아니다. 실행 중 서비스에 변경을 적용했다. 실제 센서와 재부팅·장시간 부하는 미검증이다.

```bash
cd ~/jetrover_ws/tools/ops/frontend
PATH="$HOME/.local/share/jetinspect-ops/node/bin:$PATH" node test-dashboard.mjs
~/.local/share/jetinspect-ops/venv/bin/python -m unittest discover -s ~/jetrover_ws/tools/ops -p test_ops.py -v
```

## 로봇 관제 및 자원 추이

운영 현황은 최근 최대 60개 DB 표본의 CPU·메모리·저장 공간·온도를 그래프로 표시한다. 가로축은 측정 순서로, 표본 간 시간 간격이 일정하다고 가정하면 안 된다. 연결 상태 요약의 미확인은 고장 판정이 아니다.

WORKSPACE의 **로봇 관제**에서 카메라 정지 화면을 약 2초마다 볼 수 있다. ROS 모니터는 컬러 토픽에서 초당 최대 1장의 JPEG를 생성하며 5초 이상 오래된 파일은 제공하지 않는다. 기존 `jetinspect-camera` 임시 서비스나 다른 카메라 드라이버가 실행 중이어야 한다. 저장 지도 이미지는 `maps/lap2_20261005.pgm`의 2026-11-15 복사본이며 지도 원본이 바뀌어도 자동으로 갱신되지 않는다. Gazebo 위치를 별도로 표시하며 실제 로봇 위치는 연결되지 않았다. 로봇 관제의 시뮬레이션 임무 패널은 최근 50개 임무 중 진행 상태를 표시하며 임무 관리로 이동할 수 있다. 실제 임무 관리자는 별도로 미연결로 표시한다. 화면은 로봇 구동·안전 판단 기능을 제공하지 않는다.

2026-11-15: 가상 상태 API 테스트 7건, React 서버 렌더링과 빌드 통과. 카메라 드라이버가 실행된 상태에서 localhost 미리보기 API의 640×360 JPEG와 저장 지도 PNG 응답을 확인했다. 브라우저 상호작용, 실제 지도 위치 및 임무 데이터는 미검증이다.

## 모의 임무 관리

WORKSPACE의 **임무 관리**에서 모의 점검을 생성한 뒤 선택하여 모의 실행·취소와 상태 이력을 확인할 수 있다. 실행기는 3초 간격으로 모의 상태를 진행하며 로봇이나 ROS 명령을 전송하지 않는다. 결과는 실제 점검 결과가 아니다. 실제 임무 실행은 허용되지 않는다.

모의·Gazebo 임무와 상태 이력은 로컬 MySQL에 저장하며 목록은 페이지당 50건씩 조회한다. 기존 `/tmp/jetinspect-mission-<사용자 UID>/missions.sqlite3`가 있으면 최초 시작 시 원본을 보존하고 한 번만 복사한다. 대시보드 재시작 시 진행 중이던 모의 임무는 `interrupted`로 남는다. DB 연결이 끊기면 새 요청을 거부하고 실행 중인 Gazebo 작업을 중단한 뒤 연결 복구를 시도한다. 모의 쓰기 요청은 운영자 계정과 현재 HTTPS 주소의 동일 출처를 요구한다. 이는 실제 로봇 제어를 위한 권한 체계가 아니다.

2026-11-15: 격리 SQLite에서 API·동시성·취소·재시작·DB 오류/복구 등을 포함한 관련 테스트 23건 통과. 임시 DB와 별도 로컬 테스트 서버에서 Firefox로 모의 임무 생성·실행·성공·이력·취소를 두 차례 확인했다. 운영 DB·로봇은 사용하지 않았다. MySQL 연동과 실기 시험은 미검증이다. 브라우저 검증 명령: `~/.local/share/jetinspect-ops/venv/bin/python ~/jetrover_ws/tools/ops/test_mission_browser.py` (Firefox 및 geckodriver 필요).

## Gazebo 주행 임무

WORKSPACE → **임무 관리**에서 `Gazebo 주행`을 선택해 임무를 생성하고 **Gazebo 실행**을 누르면 고정 시뮬레이션 목표 `(1.00, 1.45, yaw 1.571 rad)`를 사용할 수 있다. Gazebo와 Nav2는 임무별로 자동 기동하고 완료·취소 후 자동 종료한다. 준비 중에는 `Gazebo 환경 준비 중`으로 표시된다. 이미 다른 시뮬레이터가 도메인 31에서 실행 중이면 종료하지 않고 충돌을 알린다. 실행기는 도메인 31, 지정된 루프백 전용 UDP 프로필, GazeboSimSystem 및 시뮬레이션 clock을 검사한다.

다음은 별도 수동 진단용 설정이다. 대시보드 자동 실행과 동시에 수동 시뮬레이터를 실행하지 않는다.

```bash
source /opt/ros/jazzy/setup.bash
source ~/jetrover_ws/install/setup.bash
export ROS_DOMAIN_ID=31 ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp GZ_IP=127.0.0.1
unset ROS_STATIC_PEERS ROS_DISCOVERY_SERVER FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI GZ_PARTITION FASTDDS_BUILTIN_TRANSPORTS ROS_LOCALHOST_ONLY
export FASTRTPS_DEFAULT_PROFILES_FILE="$HOME/jetrover_ws/tools/mission/fastdds-loopback.xml"
```

이 프로필은 UDP 인터페이스를 127.0.0.1로 제한하고 DDS 공유 메모리 전송을 끈다. `SUBNET`만 단독으로 설정하면 같은 격리가 되지 않으므로 반드시 프로필과 함께 사용한다. Gazebo·Nav2·임무 실행기에 모두 같은 설정을 사용하며 실제 로봇용 설정에는 적용하지 않는다.

수동 진단 시에는 첫 번째 터미널에서 `ros2 launch jetrover_gazebo sim.launch.py gui:=false depth_obstacles:=true`, 두 번째 터미널에서 `ros2 launch jetrover_navigation nav2.launch.py use_sim_time:=true params_file:=$HOME/jetrover_ws/tools/nav/ab_params/nav2_params_mppi.yaml precise_approach:=false`를 실행한다. 사용 후 두 터미널에서 Ctrl+C로 종료하고 잔여 프로세스를 확인한다. 이 기능은 실제 로봇 제어가 아니다.

2026-11-16 격리 API→Gazebo 시작점 반복 시험 2/2 성공(약 131초, 125초). 시험 조건·제한은 `docs/benchmarks/sim/mission_dashboard_gazebo_20261116.md` 참조. 이후 임무 이력은 MySQL로 이전했다.

## Gazebo 경광등 점검 임무
임무 관리에서 **Gazebo 경광등 점검**을 선택해 임무를 생성하고 **Gazebo 실행**을 누르면 Gazebo·Nav2와 가상 경광등 시험판을 자동으로 준비한 뒤 주행·점검한다. 시험판은 가상 이미지용이며 실물 장비가 아니다. 아래는 별도 수동 진단 시 시험판을 배치하는 명령이다.

```bash
ros2 run ros_gz_sim create -world jetrover_room -file ~/jetrover_ws/tools/mission/stack_light_robot_view.sdf -name robot_view_stack_light
gz service -s /world/jetrover_room/set_pose --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 5000 --req 'name: "robot_view_stack_light", position: {x: 1.001, y: 1.770, z: 0.158}, orientation: {x: -0.301, y: 0.301, z: 0.640, w: 0.640}'
```

점검 임무는 카메라 시야 확보를 위해 일반 주행보다 엄격한 위치 0.03 m·방향 0.08 rad 도착 허용 오차를 적용한다. 더 엄격한 조건으로 주행이 오래 걸리거나 완료되지 않을 수 있다. 점검 결과가 없거나 영상이 불충분하면 성공하지 않는다. 화면과 이력에 주행과 점검 단계를 구분해 표시한다. 현재 색상 탐색은 가상 시험판 전용이며 개선 후 새 Gazebo에서 점검 성공 2회, 점검 중 브라우저 취소 1회를 확인했다. 실제 설비의 판정과 장시간 반복 성능은 검증되지 않았다. 시험 과정은 `prd/gazebo-stack-light-test-plan.md`에 기록했다.

2026-11-19: 가상 경광등 관측이 실패하면 수신 영상 수·유효 표본·시각 오류·표본 초기화·형식 오류와 색상별 판정 불가 사유를 임무 결과에 기록하고 화면에 표시한다. 이전 이력과 해당 진단이 없는 실패는 기존 방식으로 표시한다. 격리 ROS 영상 중단, 격리 DB·작업자 및 Firefox 화면 시험으로 확인했다. 실제 설비나 카메라 판정 정확도는 검증하지 않았다. 녹화 영상 오프라인 시험은 `tools/mission/README.md`를 참조한다.

임무 관리의 **경광등 녹화 영상 시험**에서 운영자가 최대 8MB·1280×720 영상을 선택하고 빨강·노랑·초록 영역을 원본 영상 픽셀 `x,y,너비,높이`로 지정하면 처음 3초를 관측해 색상별 결과와 첫·마지막 표본을 볼 수 있다. 영상과 결과는 임시 처리 후 저장하지 않는다. 조회자 사용 불가, 동일 출처·로그인이 필요하며 동시 실행은 하나로 제한한다. 가상 시험판용 분류기를 사용하므로 실제 설비 판정에 사용해서는 안 된다. 합성 영상의 API·Firefox 검증만 완료했고 실제 영상 성능 및 임무 이력 연결은 미검증이다.

## 데이터베이스 탐색

대시보드의 WORKSPACE에서 **데이터베이스**를 선택하면 `jetinspect`의 `system_metrics`, `robot_events`, `missions`, `mission_events` 테이블을 페이지당 50행씩 읽을 수 있다. 새로고침과 이전/다음 페이지를 제공한다. 시스템 지표와 운영 이벤트의 DB 기록 시각 시간대는 미확인이다. 행의 상세 버튼에서 긴 값 전체를 확인하고 복사할 수 있다. 임의 SQL 실행 및 편집은 제공하지 않는다.

저장 지도에는 별도 `jetinspect-gazebo-pose` 서비스가 읽은 Gazebo TF 위치만 표시한다. 5초 넘게 갱신되지 않으면 미확인으로 표시하며 실제 로봇 위치는 제공하지 않는다.

## 센서 연결 관리

운영 현황의 **센서 연결**에서 운영자만 카메라·IMU·LiDAR를 각각 연결·종료할 수 있다. 실행 상태와 실제 수신 여부는 별개로 표시한다. `jetinspect-camera`, `jetinspect-base-sensors`, `jetinspect-lidar`는 수동 시작 서비스이며 자동 시작하지 않는다. 기존 외부 ROS 드라이버가 있으면 중복 시작을 거부하고, 종료는 대시보드 전용 서비스에만 적용한다.

IMU 연결은 base_node의 `sensor_only` 모드다. 이 모드는 바퀴 명령을 구독하지 않고 모터·팔 프레임과 e-stop 해제를 전송하지 않는다. 팔 관절 피드백과 구동용 base_node의 정상 기능은 제공하지 않는다. 별도 실행 중인 드라이버의 원격 종료는 지원하지 않는다. 카메라 실행은 실제 장치와 USB 자원을 사용한다. 시리얼 의사 터미널 시험에서 가상 IMU를 수신하고 시작·종료 포함 제어 프레임 0개를 확인했다.

## 센서 보정 후보

보정 화면에는 11개 작업과 결과 이력이 표시된다. 측정 결과는 후보로 저장되며, 적용 가능한 항목은 현재 설정·후보를 검토한 후 운영자가 별도로 적용한다. 적용 시 전용 백업을 만들고, 이후 파일이 바뀌지 않았을 때 복원할 수 있다. 조회자는 읽기만 가능하다. 저장된 후보나 이력을 불러오는 동작은 실제 설정을 변경하지 않는다.

- IMU: 정지 자이로와 사용자가 지지한 6자세 가속도 후보를 측정한다. 자이로 bias와 축별 가속도 offset/scale은 설치된 base.yaml에 별도 적용한다. 가속도 교차축 오차는 보정하지 않는다.
- 카메라: 컬러 체커보드 후보를 8~40장으로 계산하고 CameraInfo와 비교한다. 카메라 원본은 드라이버에서 MJPG로 수신되며 디코딩 후 캡처를 PNG로 보존한다. 컬러 CameraInfo는 별도 적용한다. RGB-D 정합 시작 모드는 HW_D2C/SW_D2C/OFF 중에서 별도 백업·적용·복원할 수 있으며 카메라 재시작이 필요하다. 이는 공장 RGB-D 외부 파라미터를 변경하지 않는다. 독립적으로 측정한 깊이·컬러 3D 대응점으로 외부 변환 후보를 계산할 수 있지만 장치나 데이터 경로에 적용하지 않는다.
- LiDAR: 기준 위치를 수동 입력하고 스캔과 TF로 방향을 비교한다. 위치와 독립 실측한 본체 장착 yaw를 각각 설치 URDF에 적용할 수 있다. lidar_frame의 별도 회전은 유지하며 가까운 물체의 스캔 오차를 장착 yaw로 간주하지 않는다.
- 바퀴·오도메트리: 바퀴 포트별 피드백을 외부 기준과 비교하고, 원시 오도메트리 기록 및 기존 주행 결과를 비교한다. 명령 적분 기반 시험 3개 이상으로 계산한 축별 배율만 적용하며 엔코더·EKF 보정값으로 취급하지 않는다. 휠 포트별 다점 외부 속도 비교는 비율·잔차 후보만 생성하며 PID와 제어기 설정을 변경하지 않는다.
- 관절·그리퍼: 실제 서보 응답이 신선할 때 독립 기준과 비교해 관절 오프셋을 적용할 수 있다. 개폐 폭의 두 점 보정은 대시보드 표시 전용이다. 그리퍼 외부 힘 측정 기능은 사용자 요청으로 제외했다. 센서 연결에서 기존 IMU 전용 모드를 종료한 뒤 팔 관측 모드를 시작하면 서보 위치·온도 읽기와 관절 상태 발행이 가능하다. 두 모드는 동시에 실행할 수 없다. 이 모드는 구동·토크 명령을 받지 않는다.
- 카메라–팔·TCP: 수동 3차원 대응점, 다중 자세 핸드아이 및 TCP 접점 자세에서 후보를 계산한다. 핸드아이는 실제 카메라 TF를 이용하여 설치 URDF 카메라 장착값에, TCP는 엔드이펙터 위치에 별도 적용할 수 있다. 핸드아이 자세는 체커보드 영상과 해당 시각의 팔 TF를 함께 캡처하거나 수동 입력할 수 있고, TCP 자세는 정지 상태에서 읽기 전용 TF 캡처가 가능하다. 대칭 체커보드 코너 순서가 뒤집히지 않게 주의한다. 두 결과 모두 독립 검증이 필요하다.
- 외형·배터리: 실측 외형은 기본 Nav2 양쪽 costmap의 기존 범위를 축소하지 않는 경우에만 적용한다. 배터리 다점 보정은 대시보드 표시 전용이고 원본 전압·안전 경고는 유지된다. 표본 범위 밖에서는 외삽하지 않는다.

설정은 설치 트리 또는 사용자 전용 디렉터리에 저장한다. 설치 트리의 값은 재빌드 시 원본 설정에 의해 덮일 수 있고, 관련 노드를 별도로 재시작해야 반영된다. 카메라·TF·팔·Nav2 설정의 적용은 실제 위치 판단과 향후 동작에 영향을 준다. 독립적인 측정으로 검증하고, 실제 바퀴·팔 구동과 설정값 덮어쓰기는 프로젝트 안전 규칙에 따라 별도 승인한다. 대시보드는 보정을 위해 구동 명령을 보내지 않는다. 후보 수집 중 임시 촬영 영상은 서버 정상 종료 또는 초기화 시 삭제된다.

## 실행 및 복구

사용자 서비스 4개: `jetinspect-mysql`, `jetinspect-dashboard`, `jetinspect-ros-monitor`, `jetinspect-gazebo-pose`. 로그인 없이 부팅 시에도 시작되도록 `loginctl enable-linger sang`을 설정했다. 로봇 bringup과 물리 구동은 실행하지 않는다. 실제 재부팅 후 기동은 아직 검증하지 않았다.

```bash
systemctl --user status jetinspect-mysql jetinspect-dashboard jetinspect-ros-monitor
systemctl --user restart jetinspect-dashboard
journalctl --user -u jetinspect-dashboard -n 100 --no-pager
systemctl --user stop jetinspect-dashboard jetinspect-ros-monitor jetinspect-mysql
systemctl --user start jetinspect-mysql jetinspect-ros-monitor jetinspect-dashboard
```

설정 원본은 `systemd/`, 설치본은 `~/.config/systemd/user/`다. 변경 후 설치본 복사와 `systemctl --user daemon-reload`가 필요하다. 서비스 journal의 최대 보존량은 시스템 설정을 따르며 별도 logrotate 설정은 하지 않았다.

```bash
# Python 의존성 복원 및 화면 빌드 (Node와 MySQL 바이너리 설치는 별도)
env -u PYTHONPATH ~/.local/share/jetinspect-ops/venv/bin/pip install -r ~/jetrover_ws/tools/ops/requirements.txt
PATH="$HOME/.local/share/jetinspect-ops/node/bin:$PATH" npm --prefix ~/jetrover_ws/tools/ops/frontend ci
PATH="$HOME/.local/share/jetinspect-ops/node/bin:$PATH" npm --prefix ~/jetrover_ws/tools/ops/frontend run build
# DB 테이블이 없을 때 기존 데이터 보존하며 생성
env -u PYTHONPATH ~/.local/share/jetinspect-ops/venv/bin/python ~/jetrover_ws/tools/ops/backend/init_db.py
# DB 백업 (개인 디렉터리, 권한 600)
~/jetrover_ws/tools/ops/backup.sh
# 수동 rosbag 기록 (종료 Ctrl-C; 디스크 사용량 직접 확인)
~/jetrover_ws/tools/ops/record_rosbag.sh
# 60분 상태 시험 (예: 30초 간격, 자체적으로 로봇 기능을 켜지 않음)
/usr/bin/python3 ~/jetrover_ws/tools/ops/soak.py --minutes 60 --interval 30 --url https://172.30.1.82:8765 --ca-file ~/.local/share/jetinspect-ops/tls/dashboard.crt --username <계정>
```

상태 시험은 실행 시 비밀번호를 숨겨 입력받으며, 세션 유효기간 때문에 최대 470분이다. URL과 CA 파일은 실제 서버 주소와 신뢰 설정에 맞게 지정한다.

ROS bag은 `~/.local/share/jetinspect-ops/bags`, 시험 JSONL은 `soak`, DB 백업은 `backups`. bag 자동 시작·용량 제한·자동 정리와 DB 백업 자동화는 미구현이다. 서비스 장애 시 systemd가 재시작을 시도하며, UI는 DB 연결 실패를 표시한다. 백업은 별도 장치에 복사하지 않으면 디스크 고장에 대비되지 않는다.

## 확인 결과

2026-11-12: 화면 빌드·HTTP 200, DB 상태 및 지표 기록, DB 중단 시 unavailable·재시작 후 기록 보존 확인. 백업을 별도 임시 DB에 복원해 지표 2건 조회. ROS 별도 도메인에서 가상 배터리 12.3 V와 IMU 약 9.9 Hz 수신 확인. 1분 기준 시험은 5초 간격 12개 표본에서 오류 0건. 실제 ROS 센서 및 동시 부하·장시간 시험, 재부팅 후 자동 시작은 별도 검증 필요. ROS 모니터는 물리적인 안전 기능이 아니다.

LiDAR 장착 위치는 base_link 기준 lidar_link 원점의 수동 X/Y/Z 실측 후보로 저장한다. TF나 URDF에 적용되지 않으며 lidar_frame의 스캔 방향 검증을 대신하지 않는다.

오도메트리 비교는 완료된 같은 시험의 수동 입력값만 비교한다. 이동은 cm, 누적 회전은 도 단위이며 로봇을 구동하거나 보정 계수를 변경하지 않는다.

휠 전진 방향 화면은 기존 시험의 바퀴별 관찰값만 기록하며 모터를 구동하거나 속도를 측정하지 않는다.

센서 보정 화면의 현재 카메라 정보는 컬러·깊이 CameraInfo 최신 관측값이다. 모니터와 대시보드를 새 코드로 재시작해야 하며 값이 공장 보정 또는 RGB-depth 정합을 증명하지는 않는다.

컬러 카메라 보정 후보는 해상도가 같은 최신 CameraInfo의 fx/fy/cx/cy와 비교한다. 장치 동일성을 자동으로 확인하거나 비교 차이로 정확도를 판정하지 않는다.

RGB·깊이 대응점 비교는 최신 두 CameraInfo의 해상도와 프레임이 같을 때 수동 좌표의 픽셀 오차를 저장한다. 영상 동기화와 실제 정합 정확도는 별도로 확인해야 한다.

팔·그리퍼 기준 각도 비교는 실행 중인 base_node의 런타임 매핑과 서보 응답 진단이 필요하다. sensor_only 모드에서는 관절 정보를 받을 수 없다. 비교는 로봇을 구동하거나 설정을 적용하지 않는다.

자이로 설정은 확인된 후보를 설치 base.yaml에 별도 적용하며 이전 파일을 개인 백업으로 보관한다. 노드 재시작이 필요하며 src 원본은 바꾸지 않아 재빌드로 덮일 수 있다. 카메라 변환은 고정 자세의 수동 3D 대응점에 한정하며 핸드아이 또는 TCP 보정이 아니다.

### RGB-D 외부 변환 소프트웨어 적용

독립적으로 측정한 깊이·컬러 광학 좌표 대응점으로 후보를 만든 후 화면에서 별도 보정 노드용으로 적용·복원할 수 있다. RGB-D 시작 정합을 OFF로 선택하고 카메라를 재시작해 미정합 깊이와 깊이 CameraInfo를 받아야 한다. `depth_cam_depth_optical_frame` 16UC1 입력만 수용하며 이미 정합된 입력은 거부한다. 화면에서 보정 노드를 시작하면 후보 회전·이동을 적용해 `/depth_cam/depth_corrected/image_raw`와 같은 경로의 `camera_info`를 발행한다. 픽셀 겹침은 가장 가까운 깊이를 남기며 빈 픽셀은 0이다. 원본과 기존 장애물 판단 구독을 자동 전환하지 않는다. 카메라 내부 공장값은 바뀌지 않는다.

합성 깊이 영상과 격리 ROS 토픽에서 위치 이동을 검증했으며, 실제 원본 카메라 모드·정합 정확도·성능은 아직 검증하지 않았다. 원본 모드 변경은 기존 인식·안전 경로에 영향을 주므로 설정을 검토하고 별도 실기 검증 후 사용한다.

### 보정 깊이 소비자 선택 (실기 안전 검증 전)

보정 노드가 내는 토픽을 큐브 인식에 선택하려면 `ros2 launch jetrover_perception cube_detector.launch.py depth_source:=corrected`를 사용한다. 큐브 인식은 컬러·깊이 프레임과 시각을 확인하며 입력이 없을 때 원본으로 되돌리지 않는다.

장애물 클라우드 연결은 별도의 보정 배경이 필요하다. 팔 홈 자세와 장애물이 없는 장면을 확인하고, 활성 변환 및 보정 노드가 동작할 때 `tools/ops/calibration/capture_rgbd_background.py OUTPUT.npy ~/.local/share/jetinspect-ops/calibration/rgbd-extrinsic-active.json`으로 기준 영상을 저장한다. 이후 `ros2 launch jetrover_perception camera.launch.py depth_source:=corrected corrected_background_path:=OUTPUT.npy`를 지정한다. 원래 카메라 서비스를 먼저 중지해 중복 드라이버를 피해야 한다. 기준 이미지와 보정 파일 해시가 다르거나 실행 중 보정이 바뀌면 장애물/지우기 포인트를 내지 않는다. 이 확인은 촬영 당시 팔 자세, 빈 공간, 카메라 파라미터의 물리적 정확성을 보증하지 않는다. 실기 Nav2·충돌 감지의 설정과 정지 동작을 별도 검증하기 전에는 주행에 사용하지 않는다.

대시보드 **센서 보정 → RGB-D 3차원 외부 변환 후보 → 장애물 처리 입력 연결**에서도 위 기준 영상을 촬영하고 보정 또는 기존 깊이를 선택할 수 있다. 선택은 다음 카메라 서비스 시작 시 적용된다. 큐브 감지기는 `ros2 launch jetrover_perception cube_detector.launch.py`로 다시 시작하면 저장된 선택을 따른다. 실행 중 보정값이 변경되면 보정 기준 영상과 불일치하므로 장애물 클라우드는 중단된다. 정합을 끈 미정합 영상은 기존 배경과 비교되지 않도록 광학 프레임이 다른 경우 차단한다.

## 지식 검색과 벡터 데이터베이스

WORKSPACE의 **지식 검색**에서 허용된 프로젝트 문서를 검색하고 로컬 AI 답변 및 출처 문단을 확인한다. **문서 색인 새로 만들기**는 운영자만 사용할 수 있으며 색인 전환까지 기존 결과를 유지한다. 현재 지정 문서 목록은 `backend/knowledge.py`의 `SOURCES`이고 임의 파일 업로드·PDF·이력 DB 자동 수집은 제공하지 않는다. 문서에 적힌 확정/추정/계획은 문맥과 원문을 확인해야 한다. 검색 점수는 정답 확률이 아니다. 실시간 상태·제어에는 사용하지 않는다.

벡터 DB는 `~/.local/share/jetinspect-ops/knowledge`의 Qdrant 로컬 모드이며 하나의 대시보드 프로세스만 사용할 수 있다. 모델은 `~/.local/share/jetinspect-ops/knowledge-models`에 저장된다. 색인은 CPU 두 스레드로 수행하며 생성은 기존 `tools/voice`의 Qwen 모델을 사용한다. 모델 파일이 없으면 오류를 표시하고 자동으로 외부에 자료를 전송하거나 내려받지 않는다. 기존 세대의 자동 삭제·백업 복원 UI는 아직 없다. 실행 전용 환경의 의존성은 `requirements.txt`에 명시되어 있다.

실제 한국어 검색 품질, 로봇 작업과의 동시 부하 및 음성/임무 이력 연동은 아직 충분히 검증되지 않았다.

2026-11-18: 지식 검색의 기본 답변은 LLM 요약 대신 검색된 원문과 출처를 직접 표시한다. **AI 생성 답변 · 느림**은 기존 로컬 모델을 선택적으로 실행하며 문서 밖 설명이 포함될 수 있다. 실시간 상태를 묻는 일부 표현은 관제 화면 확인을 안내한다. 30개 고정 질문의 출처 Hit@5 25/25, 무관·실시간 질문 거부 5/5 및 실제 지연은 `docs/benchmarks/rag/knowledge-evaluation-20261118.md` 참조. 이는 문단 수준 정답률이나 생성형 답변의 정확도 보증은 아니다.

검색 결과는 한국어 부분 문자열과 벡터 유사도를 함께 사용하며 선택된 청크의 앞뒤에 있는 같은 색인 버전의 문맥을 덧붙인다. 센서 실시간 질의와 관련 없는 질의의 구분은 규칙 기반이므로 항상 정확하지 않다. 개선 후 실제 서버 평가는 `docs/benchmarks/rag/knowledge-search-improvement-20261118.md` 참조.

### 지식 색인 백업과 EXAONE 선택 답변

운영자는 지식 검색 화면에서 **색인 백업**을 누를 수 있다. 백업은 `~/.local/share/jetinspect-ops/backups/`에 소유자 전용 JSON으로 저장된다. 활성 세대와 문단·벡터·모델 식별자에 대한 SHA-256 무결성 검사를 포함한다. 원본 백업을 별도 저장장치에도 보관해야 디스크 고장에 대비할 수 있다. 이 해시는 백업의 출처를 인증하는 서명이 아니다.

복원은 기존 색인을 덮어쓰지 않는 **새 디렉터리**에만 가능하다. 실제 운영 색인을 교체하지 않으며, 복원본의 상태와 검색 결과를 확인한 뒤 별도의 운영 절차가 필요하다. 이미 존재하는 경로 또는 손상된 백업은 거부한다.

```bash
# 사용 중인 대시보드에서 백업 버튼을 사용하거나, 색인이 사용 중이지 않을 때 CLI 백업
~/.local/share/jetinspect-ops/venv/bin/python ~/jetrover_ws/tools/ops/knowledge_backup.py backup ~/.local/share/jetinspect-ops/backups/knowledge-manual.json
# 새 경로에만 복원
~/.local/share/jetinspect-ops/venv/bin/python ~/jetrover_ws/tools/ops/knowledge_backup.py restore ~/.local/share/jetinspect-ops/backups/knowledge-manual.json /tmp/knowledge-restored
```

**EXAONE 외부 답변**은 운영자가 외부 전송을 확인한 경우에만 질문과 검색된 최대 3개 결과의 기본·추가 관련 문단을 전송한다. 근거가 없거나 실시간 질문이면 호출하지 않는다. API 키는 Git 제외 `tools/ops/.env`의 `EXAONE_API_KEY` 또는 환경변수에 둔다. 제공자 요청 제한과 답변 오류가 발생할 수 있으며 기본값은 원문 근거 답변이다. 2026-11-19의 17개 질문 평가와 2개 모델 비교는 `docs/benchmarks/rag/independent-evaluation-20261119.md`에 기록했다.

2026-11-19 추가: 문단 본문에 나타나는 드문 질의 글자쌍을 순위에 반영하고, 같은 문서·색인 버전의 떨어진 관련 문단 하나를 추가할 수 있으며 영어 `LiDAR` 실시간 질문을 유보한다. EXAONE 확인 시 각 결과의 추가 문단도 외부로 보낼 수 있다. 최종 별도 질문의 근거 8/10은 그대로였고 무관·실시간 유보는 3/4→4/4였다. 로컬 생성 중 카메라 주기가 낮아진 단일 시험을 포함해 상세와 한계는 `docs/benchmarks/rag/rerank-evaluation-20261119.md` 참조.

2026-11-19 추가 평가에서 실시간 이동·충전량 및 일부 영어 현재 상태 질문과 문서 단어/장치 별칭이 하나도 일치하지 않는 의미 검색 결과는 근거 부족으로 유보하도록 보완했다. 표현이 다른 실제 질문도 유보될 수 있고 일부 무관한 질문은 여전히 자료를 반환할 수 있다. 최종 별도 16문항은 근거 8/10, 무관 유보 5/6이었다. 센서와 함께 10분간 로컬 생성을 시험한 결과와 조건은 `docs/benchmarks/rag/extended-evaluation-20261119.md`에 기록했다.

생성 부하 재시험은 별도 경로로 복원한 색인과 개인 경로를 사용한다. 장치 전압과 메모리를 관찰하므로 센서가 연결된 정지 상태에서 실행한다. 지정 출력과 입력은 덮어쓰지 않는다.

```bash
~/.local/share/jetinspect-ops/venv/bin/python ~/jetrover_ws/tools/ops/evaluation/prepare_generation_stability.py --store /tmp/knowledge-restored --output /tmp/rag-stability-inputs.json
~/.local/share/jetinspect-ops/venv/bin/python ~/jetrover_ws/tools/ops/evaluation/evaluate_generation_stability.py --inputs /tmp/rag-stability-inputs.json --output ~/.local/share/jetinspect-ops/soak/rag-stability-new.json --seconds 600
```

### 음성 관제 시제품

운영자로 로그인한 뒤 **음성 관제 → 마이크 켜기**를 선택하고 브라우저의 마이크 권한을 허용한다. 접속 PC의 HTTPS 인증서가 신뢰되어야 마이크를 사용할 수 있다. 화면을 벗어나거나 마이크를 끄면 입력이 중단된다. `로버 배터리 상태 알려줘`, `로버 카메라 연결 방법 알려줘`, `로버 모의 점검 시작해`, `로버 모의 임무 취소해`처럼 발화마다 호출어를 붙인다. 호출어만 말했다면 다음 요청에도 호출어를 붙인다. `인식 문장 직접 시험`으로 마이크 없이 명령 분류를 확인할 수 있다.

모의 임무 시작과 취소는 인식한 내용을 화면에서 확인하거나 `로버 확인`이라고 말해야 요청된다. 취소 대상이 모의 임무 하나로 확정되지 않으면 임무 화면에서 선택한다. 실제 로봇과 Gazebo의 주행·팔 동작은 음성 명령으로 실행하지 않는다. 조회 결과나 생성형 답변은 제어 명령으로 실행되지 않는다.

마이크가 켜진 동안 브라우저의 간단한 음량 기준 VAD가 발화 구간을 잘라 서버로 보내고, 서버의 Whisper가 호출어 검사 **전에** 로컬 전사한다. 녹음 구간은 임시 파일에서 처리 후 삭제된다. 오디오 응답은 기본 꺼짐이며 선택 시 PC의 브라우저/OS 음성 합성을 사용한다. 응답 재생 중 입력을 무시하지만 완전한 에코 제거는 아니다. 초기 합성 음성 시험에서 호출어 오인식이 발생했으며 실제 사람 음성·소음 환경의 정확도는 아직 검증하지 않았다. 호출어가 틀리게 인식되면 명령이 무시될 수 있으므로 화면의 인식 문장을 확인한다.

## 로봇 마이크 음성 관제 (Hello Hiwonder, 2026-11-22)

대시보드 **음성 관제 → 로봇 마이크** 패널에서 운영자가 **듣기 시작**을 누르면 서버(`backend/robot_voice.py`)가 R818 마이크 보드의 제어 시리얼을 연다.

1. 보드가 "Hello Hiwonder"를 직접 감지(키워드 `hello hi wonder`, `tools/audio/r818_set_wake_word.py`) → 로봇 스피커 비프음.
2. 보드 USB 마이크(`plughw:CARD=XFMDPV0018,DEV=0`, `JETROVER_MIC_DEVICE`)로 명령 하나를 녹음: 비프 잔향 0.16초 제외, 4초 안에 말 시작, 무음 1초에 종료, 최대 6초, 0.24초 이상 발화만 인정.
3. 로컬 Whisper(허용 명령 어휘 힌트) → 비발화 환각(`[구독]`, 같은 문장 반복) 제거 → 기존 제한 의도(`voice_intent.classify`).
4. 상태 조회·문서 근거·임무 상태는 바로 로봇 스피커(Piper)로 답한다. 모의 점검 시작·모의 임무 취소는 30초 안에 다시 호출해 "확인"이라고 말하거나 패널 버튼으로 확인해야 실행된다. 실제 주행·팔·Gazebo 명령은 거부한다.

API: `GET /api/voice/robot`(상태·최근 20건), `POST /api/voice/robot/{start|stop|confirm|dismiss}`(운영자). 시리얼은 독점으로 열리므로 듣는 동안 `tools/audio/r818_*` 도구와 동시에 못 쓴다. 음성은 메모리에서만 처리하고 전사용 임시 WAV는 자동 삭제한다. 시험: `test_robot_voice.py`(가짜 장치), 실기 2026-11-22 가짜 임무 저장소로 상태·모의 시작·확인 왕복 통과.

## 문서 답변: EXAONE 우선 (2026-11-22)

`GET /api/knowledge/ask`가 기본 답변 경로다(대시보드 **답변 (EXAONE 우선)**, 로봇 음성 문서 질문). 검색 근거가 있으면 질문과 상위 문단 최대 3개를 EXAONE으로 보내 답을 받고, 근거 없음·키 없음·EXAONE 오류 시 로컬 근거 답변으로 대체하며 화면에 사유를 표시한다. 근거가 없으면 외부로 보내지 않는다. 로컬만 쓰려면 `tools/ops/.env`에 `KNOWLEDGE_ANSWER_PROVIDER=local`. 로봇 음성은 EXAONE 답에서 출처 번호·마크다운을 빼고 앞 문장(최대 180자)만 읽는다.
- EXAONE(K-EXAONE 2.5)은 항상 추론 후 답하므로 `max_tokens`에 추론 토큰이 포함된다. 1024에서는 실제 근거 질문에 추론만 하고 빈 답(`finish_reason: length`)을 내 로컬로 대체됐다 → 4096으로 올렸다. 응답 시간 실측 20~33초라, 로봇 음성은 먼저 "문서를 확인하고 있습니다"라고 안내한다. 음성 전사의 "라이더"는 "라이다"로 고쳐 검색한다.
