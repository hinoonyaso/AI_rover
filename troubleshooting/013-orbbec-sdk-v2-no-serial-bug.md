# Orbbec DaBai DCW: depth 센서에 USB 시리얼이 없어서 SDK v2가 카메라를 못 찾음
- 날짜: 2026-09-22~23
- 상태: **해결** (SDK v1 소스 빌드로 우회)
- 관련: `jetrover_perception/launch/camera.launch.py`, `ros-jazzy-orbbec-camera` (2.9.3), `src/OrbbecSDK_ROS2`(소스, main 브랜치)

## 증상
카메라 드라이버를 띄우면 USB 권한 문제(udev 규칙 설치로 해결, 아래 참고)는 사라졌지만, 여전히 장치를 못 찾는다.
```
[warning] UsbEnumeratorLibusb.cpp:159 Invalid descriptor index: 0
[error]   UsbEnumeratorLibusb.cpp:424 Failed to query USB device serial number
[info]    DeviceManager.cpp:25 Current found device(s): (0)
```
`enable_depth: false` + `product_id: 0x0559`(RGB만 필터링)로 시험해도 **똑같이 `(0)`으로 실패한다.**

## 원인
`lsusb -v`로 보면 depth 센서(`2bc5:0659`)는 `iSerial 0`(USB 시리얼 번호 문자열 자체가 없음)이고,
RGB 카메라(`2bc5:0559`)는 시리얼이 있다(`CH23C42006S`). `orbbec_camera`(OrbbecSDK v2 기반, apt로 설치한 2.9.3)의
USB 열거 코드가 장치 스캔 도중 시리얼이 없는 장치를 만나면 **그 시점에서 스캔 전체가 실패한다** (개별 장치를 건너뛰지 않음).
그래서 RGB만 쓰려고 필터링해도 열거 단계 자체가 먼저 죽어서 소용없다.

**우리가 만든 게 아니라 업스트림 버그다.** GitHub `orbbec/OrbbecSDK_v2` 이슈 #51에 같은 DaBai 계열 카메라(Dabai DC1),
같은 에러 메시지, 같은 플랫폼 종류(ARM64 Linux, Raspberry Pi 5)로 정확히 재현한 보고가 있다(2025-04-05, 아직 미해결).
보고자는 **SDK v1.10.18로 내리면 된다**고 했다(SDK v2에서 생긴 회귀).

## 해결 또는 우회
**DaBai DCW는 legacy OpenNI(SDK v1) 장치다.** Orbbec 공식 SDK v1 문서에는 최소 펌웨어 2460으로 명시적으로 지원되지만,
SDK v2 쪽 문서에는 "향후 UVC로 전환 예정" 목록에만 있고 아직 정식 지원되지 않는다. 그래서 apt의 SDK v2 기반
`ros-jazzy-orbbec-camera`가 아니라 **`OrbbecSDK_ROS2`의 `main` 브랜치(SDK v1.x)를 소스로 빌드**해야 한다.

```bash
cd ~/jetrover_ws/src
git clone --branch main --depth 1 https://github.com/orbbec/OrbbecSDK_ROS2.git
cd ~/jetrover_ws/src/OrbbecSDK_ROS2/orbbec_camera/scripts && sudo bash install_udev_rules.sh
cd ~/jetrover_ws
MAKEFLAGS="-j2" colcon build --symlink-install --parallel-workers 1 \
  --packages-select orbbec_camera_msgs orbbec_camera orbbec_description \
  --cmake-args -DCMAKE_BUILD_TYPE=Release
```
같은 패키지 이름(`orbbec_camera`)이라 워크스페이스 오버레이로 apt 버전(SDK v2)을 자동으로 덮어쓴다
(`source ~/jetrover_ws/install/setup.bash`가 `/opt/ros/jazzy`보다 뒤에 오면 우선 적용).

**결과 (2026-09-23 확인)**: `libOrbbecSDK.so.1.10.37` 빌드됨. `jetrover_perception/launch/camera.launch.py` 실행 시
`Current found device(s): (1)`, `Device DaBai DCW connected` 정상. `color/image_raw`(640×360 rgb8, ~23 Hz),
`depth/image_raw`(~24 Hz), `ir/image_raw`(~23 Hz) 모두 정상 발행.

**주의**: 이 빌드(네이티브 C++ SDK) 도중 **메모리 부족으로 시스템 전체가 멈춘 적이 있다** (troubleshooting/014).
반드시 `MAKEFLAGS=-j2`, `--parallel-workers 1`로 낮춰서 빌드하고, 스왑이 있는지 먼저 확인한다.

## 확인/재발 방지
- USB 권한(udev) 문제와 이 문제는 별개였다. udev 규칙만으로는 이 문제가 풀리지 않았다.
- `lsusb -v -d 2bc5:0659`로 `iSerial 0`인지 재확인 가능(하드웨어 특성이라 안 바뀜) — 그래서 SDK v1 경로가 유일한 해결책이다.
- 참고: https://github.com/orbbec/OrbbecSDK_v2/issues/51 (v2의 버그), https://github.com/orbbec/OrbbecSDK_ROS2 (main 브랜치가 해결책)
