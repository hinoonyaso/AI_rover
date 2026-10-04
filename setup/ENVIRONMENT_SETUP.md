# 환경 설정 기록

이 로봇(Jetson)에서 `sudo`나 시스템 전역 설치가 필요했던 작업을 모두 기록한다.
**새 Jetson이나 재설치 후 이 순서대로 실행하면 지금과 같은 환경이 된다.**
`apt install` 계열은 root 셸 하나에 모아서 한 번에 실행해도 된다.

새로운 sudo/apt/시스템 설정이 생기면 이 파일에 표와 함께 추가한다 (날짜, 명령, 이유, 확인 방법).

## 설치 순서

### 1. ROS2 패키지 (apt)
```bash
sudo apt install \
  ros-jazzy-robot-localization \
  ros-jazzy-xacro \
  ros-jazzy-joint-state-publisher \
  ros-jazzy-rplidar-ros \
  ros-jazzy-slam-toolbox \
  ros-jazzy-nav2-map-server \
  ros-jazzy-orbbec-camera
```

| 날짜 | 패키지 | 이유 | 확인 |
|---|---|---|---|
| 2026-09-20 | `ros-jazzy-robot-localization` | EKF (`/odom`, `odom→base_footprint` TF) | `ros2 pkg list \| grep robot_localization` |
| 2026-09-21 | `ros-jazzy-xacro`, `ros-jazzy-joint-state-publisher` | URDF 작업 대비 (xacro는 아직 실사용 안 함, 일반 URDF만 씀) | `ros2 pkg list` |
| 2026-09-21 | `ros-jazzy-rplidar-ros` | RPLIDAR A1 드라이버 (`rplidar_composition`) | `jetrover_bringup/launch/lidar.launch.py` 실행, `/scan` 확인 |
| 2026-09-21 | `ros-jazzy-slam-toolbox` | SLAM (`jetrover_navigation/launch/slam.launch.py`) | `ros2 lifecycle get /slam_toolbox` → `active` |
| 2026-09-22 | `ros-jazzy-nav2-map-server` | 표준 지도(`.pgm/.yaml`) 저장 (`map_saver_cli`, `slam_toolbox`의 `save_map` 서비스가 내부적으로 사용) | `/slam_toolbox/save_map` 서비스 호출 결과 `result=0`, `.pgm/.yaml` 생성 확인 |
| 2026-09-22 | `ros-jazzy-orbbec-camera` | Orbbec DaBai DCW(RGB-D) 카메라 드라이버 (`orbbec_camera::OBCameraNodeDriver`) | `jetrover_perception/launch/camera.launch.py` 실행, 이미지 토픽 확인 (진행 중) |
| 2026-09-28 | `ros-jazzy-nav2-amcl`, `ros-jazzy-nav2-lifecycle-manager` | AMCL localization (`jetrover_navigation/launch/localization.launch.py`) — 이때 기록을 빠뜨렸다가 2026-10-04에 뒤늦게 추가함 | 실제 로봇으로 `localization.launch.py` 실행, `map_server`+`amcl` lifecycle active 확인 |
| 2026-10-04 | `ros-jazzy-navigation2`, `ros-jazzy-nav2-bringup` | Nav2 전체(costmap/planner/controller/bt_navigator/behaviors/dwb/smac_planner 등, `prd/slam-nav2.md` 8번) | `ros2 pkg prefix nav2_bringup` 등 11개 패키지 전부 확인(`checklist` 8.1) |

### 2. ch341 커널 모듈 (out-of-tree 빌드)
Jetson 커널(`6.8.12-1021-tegra`)이 `CONFIG_USB_SERIAL_CH341`을 빼고 빌드돼서, LiDAR(CH340 USB-시리얼)가 `/dev/ttyUSB*`로 안 잡힌다.
mainline 커널 소스에서 직접 빌드해서 설치했다. 자세한 내용: `drivers/ch341/README.md`, `troubleshooting/012`.

```bash
cd ~/jetrover_ws/drivers/ch341
make            # 커널 헤더(nvidia-l4t-kernel-headers, 이미 설치돼 있음)로 ch341.ko 빌드
sudo ./install.sh   # /lib/modules/<kver>/extra/에 설치, depmod, modprobe, 부팅 시 자동 로드 설정
```
- 날짜: 2026-09-21
- 커널이 업데이트되면 모듈을 다시 빌드해야 한다(버전이 다르면 `install.sh`가 거부한다): `make clean && make && sudo ./install.sh`.
- 확인: `lsmod | grep ch341`, `ls /dev/ttyUSB*`.

## 검토했지만 설치하지 않은 것
| 항목 | 상태 | 이유 |
|---|---|---|
| `stm32flash` | 미설치 | STM32 펌웨어 재플래시를 검토하다 중단함(받은 파일이 이미 분석한 것과 동일, ISP 포트도 못 찾음). 필요해지면 이 zip처럼 이 파일에 추가한다. |
| `ros-jazzy-foxglove-bridge` | 미설치, 제안만 함 | VS Code SSH 환경에서 실시간 RViz 대안으로 제안했으나 아직 필요 요청 없었음. 필요해지면 `tools/viz/README.md` 참고. |

## 참고
- `sudo`가 필요한 명령은 이 세션(Claude/Codex)이 직접 실행하지 못한다. 항상 사용자에게 요청해서 실행한 뒤 결과를 알려달라고 한다 (`AGENTS.md` 안전 규칙 3).
- apt 패키지는 버전을 고정하지 않았다(설치 시점의 `candidate` 버전). 문제가 생기면 `apt-cache policy <패키지>`로 설치된 버전을 확인한다.

### 3. Orbbec 카메라 USB 권한 (udev 규칙)
`ros-jazzy-orbbec-camera`를 설치해도 USB 접근 권한이 없어서 드라이버가 카메라를 못 연다
(`Failed to open USB device: Access denied`). 패키지에 포함된 규칙 파일을 시스템에 설치해야 한다.

```bash
sudo cp /opt/ros/jazzy/share/orbbec_camera/udev/99-obsensor-libusb.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```
- 날짜: 2026-09-22
- 카메라 USB 케이블을 뽑았다 꽂거나 재부팅하면 규칙이 바로 적용된다(트리거만으로도 대개 즉시 적용됨).
- 확인: `ls -l /dev/dabai_dcw /dev/dabai_dcw_rgb` (규칙의 `SYMLINK`), 또는 카메라 launch 로그에 `Access denied`가 다시 안 나오는지.

### 4. OrbbecSDK_ROS2 `main` 브랜치(SDK v1) 빌드 의존성
DaBai DCW는 legacy OpenNI(SDK v1) 장치인데, apt로 설치한 `ros-jazzy-orbbec-camera`(2.9.3)는 SDK v2 기반이라
USB 열거 단계에서 실패한다(troubleshooting/013). `src/OrbbecSDK_ROS2`(main 브랜치, SDK v1)를 소스로 빌드해서
같은 이름(`orbbec_camera`)으로 apt 버전을 오버레이한다.

```bash
sudo apt install ros-jazzy-image-transport-plugins ros-jazzy-compressed-image-transport
```
- 날짜: 2026-09-22
- 나머지 의존성(`libgflags-dev`, `nlohmann-json3-dev`, `ros-jazzy-image-transport` 등)은 이미 설치돼 있었다.
- 확인: `cd ~/jetrover_ws && colcon build --packages-select orbbec_camera` 성공 여부.

### 5. OrbbecSDK_ROS2(소스, SDK v1)의 udev 규칙 재설치
소스로 받은 저장소 자체의 udev 규칙 스크립트로 다시 설치했다(3번 항목의 apt 버전 규칙 파일을 덮어씀, 내용은 동일한 것으로 보임).
```bash
cd ~/jetrover_ws/src/OrbbecSDK_ROS2/orbbec_camera/scripts
sudo bash install_udev_rules.sh
```
- 날짜: 2026-09-22

### 6. 스왑 파일 4 GB 추가
`colcon build`(네이티브 C++ SDK 컴파일)가 메모리를 다 써서 시스템이 멈추고 SSH가 끊기는 문제가 있었다
(스왑 0B, RAM 7.3 GiB, GNOME 데스크톱과 동시 사용: troubleshooting/014). 스왑을 추가해서
메모리 부족 시 멈추는 대신 느려지기만 하도록 했다.

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```
- 날짜: 2026-09-23
- 확인: `free -h`의 `Swap` 줄에 `4.0Gi`가 보여야 한다.
- 재부팅해도 `/etc/fstab`에 등록했으니 자동으로 다시 켜진다.

### 7. web_video_server (카메라를 VS Code SSH 환경 브라우저로 보기)
카메라(또는 다른 이미지 토픽)를 MJPEG로 웹에 띄워서, VS Code의 포트 포워딩 + 로컬 브라우저로 실시간으로 본다.
GUI가 필요한 `rqt_image_view`와 달리 순수 웹 서버라 SSH만으로 충분하다.

```bash
sudo apt install ros-jazzy-web-video-server
```
- 날짜: 2026-09-23
- 사용법은 `tools/viz/README.md` 참고.

### 8. STM32 펌웨어 재작성용 ARM 툴체인 + STM32CubeProgrammer
자체 STM32 펌웨어(`~/.claude/plans/enchanted-chasing-sky.md`)를 빌드/flash하기 위해 사용자가 직접 설치함.
`sudo apt`가 아니라 `~/.local/opt/stm32/`에 로컬로 설치됨 (설치 스크립트는 기록 안 됨 — 다음에 같은 걸 다시 하려면
`arm-none-eabi-gcc`, `STM32CubeProgrammer` 공식 배포본을 그 경로에 설치하면 됨).

```bash
export PATH="$PATH:/home/sang/.local/opt/stm32/bin"
arm-none-eabi-gcc --version     # 13.2.1
STM32_Programmer_CLI --version  # 2.23.0
```
- 날짜: 2026-09-27
- 확인: 위 두 명령이 버전을 출력하면 정상.
- **아직 없음**: `openocd`, `stlink-tools`(`st-info`/`st-flash`) — ST-Link 호환보드 도착 후 `sudo apt install openocd stlink-tools`로 설치 예정 (사용자 승인/sudo 필요).
- PATH를 매번 export하지 않으려면 `~/.bashrc`에 추가하는 것을 고려.
