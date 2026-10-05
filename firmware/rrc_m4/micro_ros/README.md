# micro_ros — micro-ROS 빌드 (Jetson 네이티브, docker 없이)

| 스크립트 | 산출물 | 상태(2026-10-05) |
|---|---|---|
| `build_microros_lib.sh` | `firmware/build/libmicroros.a`(12 MB) + `include/` — STM32F407용 micro-ROS 클라이언트 | **빌드 성공** |
| `build_agent.sh` | `~/jetrover_ws/uros_agent_ws` — Jetson용 `micro_ros_agent` | 빌드 시도 중/결과는 `build_agent.log` |

- `micro_ros_setup`: github.com/micro-ROS/micro_ros_setup 브랜치 jazzy, 커밋 `ed45678c6c0b567277b019f61c395add51c0783e` (`setup_src/`).
- `toolchain.cmake`(Cortex-M4F hard float, libstdc++ 헤더 경로 포함), `colcon.meta`(XRCE 커스텀 시리얼 + 프레이밍, 노드 1/퍼블리셔 8/구독 6/서비스 2/히스토리 4).
- sudo가 없어서 `shim/rosdep`(install no-op)을 쓴다. 이유와 libstdc++ 헤더 추가: `troubleshooting/024`, `setup/ENVIRONMENT_SETUP.md` 10번.
- `firmware/`, `setup_ws/`, `*.log`는 재생성 가능한 빌드 산출물이다.

## 펌웨어 빌드 (MICROROS 모드)
```bash
cd firmware/rrc_m4
cmake -S . -B build-arm-uros -DCMAKE_TOOLCHAIN_FILE=cmake/arm-none-eabi.cmake -DCOMM_MODE=MICROROS && cmake --build build-arm-uros -j2
```
측정(2026-10-05): flash 207 KB(40 %), RAM 111 KB(86 %, FreeRTOS 힙 40 KB 포함), CCM 35 KB. **RAM이 빠듯하다** — 런타임 힙 최소 여유는 LCD 마지막 줄(`H..K`)에서 확인하고, `rcl` 초기화가 실패하면 `RRC_FREERTOS_HEAP_BYTES`를 먼저 의심한다(실기에서 아직 확인 안 함).

## 실행 (flash 후, 별도 승인)
```bash
source /opt/ros/jazzy/setup.bash && source ~/jetrover_ws/uros_agent_ws/install/setup.bash && source ~/jetrover_ws/install/setup.bash
ros2 launch jetrover_microros microros.launch.py          # agent + rrc_bridge + URDF + EKF (jetrover_base와 동시 실행 금지)
ros2 topic echo /rrc/status                               # MCU 상태, /rrc/wheel_rps 엔코더 속도
ros2 service call /rrc/estop std_srvs/srv/SetBool "{data: false}"   # e-stop 해제
```
RRC fallback: ISP 포트 `/dev/ttyACM1`(115200)에서 같은 RRC 프로토콜이 나온다. 열 때 DTR/RTS 주의(`firmware/rrc_m4/README.md`).
