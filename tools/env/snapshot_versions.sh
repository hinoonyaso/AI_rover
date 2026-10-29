#!/usr/bin/env bash
# 한글: 이 기계(Jetson 또는 host PC)의 OS·ROS·apt·Python 패키지 버전을 마크다운으로 출력한다(설치·변경 없음, 읽기만).
#       체크리스트 0번 "전체 패키지 버전/환경 문서화". 결과는 docs/environment/에 날짜별로 저장한다.
# Print OS / ROS / apt / Python package versions of this machine as Markdown (read-only).
# Usage: bash tools/env/snapshot_versions.sh > docs/environment/versions_<host>_<date>.md
# set -u 를 쓰지 않는다: ROS setup.bash가 정의 안 된 변수를 읽어 조용히 끝난다 / setup.bash trips set -u
source /opt/ros/jazzy/setup.bash 2>/dev/null
echo "# 환경 버전 스냅샷: $(hostname) ($(date +%F))"
echo
echo "생성: \`tools/env/snapshot_versions.sh\` (읽기 전용). 신뢰 수준: 확정(이 시점 명령 출력)."
echo
echo "## 시스템"
echo '```'
grep PRETTY_NAME /etc/os-release
uname -srm
[ -f /etc/nv_tegra_release ] && head -1 /etc/nv_tegra_release        # Jetson L4T
dpkg-query -W -f='${Package} ${Version}\n' nvidia-jetpack 2>/dev/null
python3 --version
gcc --version | head -1
cmake --version | head -1
echo '```'
echo
echo "## ROS 2 (apt, ros-jazzy-*)"
echo '```'
dpkg-query -W -f='${Package} ${Version}\n' 'ros-jazzy-*' 2>/dev/null | grep -E \
  'ros-jazzy-(ros-base|rclcpp|rclpy|navigation2|nav2-bringup|nav2-bt-navigator|nav2-controller|nav2-smac-planner|nav2-mppi-controller|nav2-collision-monitor|slam-toolbox|robot-localization|rplidar-ros|moveit|moveit-ros-move-group|ros2-control|ros-gz|ros-gz-bridge|gz-.*-vendor|behaviortree-cpp|tf2-ros|cv-bridge|orbbec-camera|apriltag.*|micro-ros.*|rmw-fastrtps-cpp|rmw-cyclonedds-cpp) '
echo "(전체 ros-jazzy-* 개수: $(dpkg-query -W 'ros-jazzy-*' 2>/dev/null | wc -l))"
echo '```'
echo
echo "## Python (시스템)"
echo '```'
python3 - <<'PY'
import importlib
for m in ('numpy', 'scipy', 'cv2', 'yaml', 'serial', 'transforms3d', 'open3d', 'torch', 'ultralytics', 'pytest'):
    try:
        mod = importlib.import_module(m)
        print(m, getattr(mod, '__version__', '?'))
    except Exception:
        print(m, '-')
PY
echo '```'
echo
echo "## 워크스페이스"
echo '```'
cd ~/jetrover_ws 2>/dev/null && { echo "jetrover_ws $(git rev-parse --short HEAD 2>/dev/null) ($(git log -1 --format=%cd --date=short 2>/dev/null))";
  [ -d src/OrbbecSDK_ROS2/.git ] && echo "OrbbecSDK_ROS2 $(git -C src/OrbbecSDK_ROS2 rev-parse --short HEAD) $(git -C src/OrbbecSDK_ROS2 rev-parse --abbrev-ref HEAD)"; }
command -v arm-none-eabi-gcc >/dev/null && arm-none-eabi-gcc --version | head -1
command -v gz >/dev/null && echo "gz $(gz sim --versions 2>/dev/null | head -1)"
command -v uv >/dev/null && uv --version
echo '```'
