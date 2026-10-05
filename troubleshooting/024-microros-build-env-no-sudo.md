# 024 — micro-ROS 라이브러리 빌드가 sudo/툴체인 문제로 막힘 (해결, 2026-10-05)

## 증상
`micro_ros/build_microros_lib.sh`(micro_ros_setup)가 두 군데서 멈췄다.
1. `sudo: a password is required ... apt-get install python3-mypy / clang-tidy` — `create_firmware_ws.sh`의 `rosdep install -y`.
2. `unique_identifier_msgs__rosidl_typesupport_c ... fatal error: cstddef: No such file or directory`.

## 원인
1. rosdep이 빌드에 필요 없는 lint/test 도구를 sudo apt로 설치하려 한다. 이 환경은 sudo 비밀번호가 없다.
2. Jazzy의 `rosidl_typesupport_c`가 `.cpp` 파일을 생성한다. 사용자 로컬 툴체인(`~/.local/opt/stm32`, `.deb`를 `dpkg -x`로 푼 것)에는 libstdc++ 헤더가 없었다.
   (docker 방식은 `permission denied ... docker.sock`로 불가.)

## 해결
1. `micro_ros/shim/rosdep`: `install`만 no-op으로 넘기고 나머지는 `/usr/bin/rosdep`으로 전달, `build_microros_lib.sh`가 PATH 앞에 둔다.
2. `apt-get download libstdc++-arm-none-eabi-dev`(sudo 불필요)를 `dpkg -x`로 `~/.local/opt/stm32/root`에 풀고, `micro_ros/toolchain.cmake`가 `-isystem .../newlib/c++/13.2.1`을 직접 준다 (`tool-wrapper`는 수정 안 함). 기록: `setup/ENVIRONMENT_SETUP.md` 10번.

## 확인
`ls micro_ros/firmware/build/libmicroros.a`. 재현: `micro_ros/build_microros_lib.sh` (`firmware/`를 지우고 다시 실행).
