# 환경 버전 기록

- `versions_<기계>_<날짜>.md`: `tools/env/snapshot_versions.sh` 출력(읽기 전용 명령만, 설치·변경 없음). 설치 **절차와 이유**는 `setup/ENVIRONMENT_SETUP.md`, 여기는 **결과 버전**.
- 다시 찍기: Jetson `bash tools/env/snapshot_versions.sh > docs/environment/versions_jetson_$(date +%Y%m%d).md`,
  host `scp tools/env/snapshot_versions.sh sang@172.30.1.50:/tmp/ && ssh sang@172.30.1.50 bash /tmp/snapshot_versions.sh > docs/environment/versions_host_$(date +%Y%m%d).md`.
- 큰 설치·업데이트(apt upgrade, JetPack) 전후에 찍어 두면 회귀 원인을 버전 차이로 좁힐 수 있다.

## 2026-10-29 요약
| | Jetson (jetrover) | host PC (sang-GF63-8RC) |
|---|---|---|
| OS / 커널 | Ubuntu 24.04.5, 6.8.12-tegra, L4T R39.2.1, JetPack 7.2.1 | Ubuntu 24.04.5, 7.0.0 x86_64 |
| ROS 2 | Jazzy, Nav2 1.3.13, slam_toolbox 2.8.5, MoveIt 2.12.4, BT.CPP 4.10.0 | 같은 버전(Nav2 1.3.13 등) |
| Gazebo | gz 8.15.0 | gz 8.15.0 (sim 실행은 host) |
| Python | 3.12.3, numpy 1.26.4, OpenCV 4.6.0(aruco·AprilTag 36h11 포함) | 같음 + transforms3d 0.4.1 |
| 카메라 드라이버 | `src/OrbbecSDK_ROS2` main 0ea4ab6(SDK v1) 소스 오버레이 — apt `ros-jazzy-orbbec-camera` 2.9.3도 깔려 있지만 쓰지 않음(troubleshooting/013) | - |

주의
- `rmw-cyclonedds-cpp`는 버전이 비어 있다 = 설치 기록만 남고 지금은 미설치(FastDDS 사용, `setup/fastdds_wifi_only.xml`).
- host의 `~/jetrover_ws`는 git으로 동기화하지 않고 필요한 파일만 복사한다(git HEAD 07745d1은 의미 없음). sim 시험 전 바뀐 파일을 scp + 빌드.
- Docker 개발환경(체크리스트 0번)은 만들지 않았다: Jetson micro-ROS 빌드가 docker 불가(`micro_ros/build_microros_lib.sh`), 지금은 기능 구현 우선(체크리스트 메모). 대신 이 스냅샷 + `setup/ENVIRONMENT_SETUP.md`로 재현한다.
