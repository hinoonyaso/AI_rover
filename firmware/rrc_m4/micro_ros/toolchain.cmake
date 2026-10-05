# 한글: STM32F407(Cortex-M4F, 하드 플로트)용 micro-ROS 크로스 툴체인. libstdc++ 헤더 경로를 직접 지정한다(사용자 로컬 툴체인에 기본 포함 안 됨).
# micro-ROS cross toolchain for STM32F407 (Cortex-M4F, hard float). Used by build_microros_lib.sh.
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_CROSSCOMPILING 1)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
set(TOOLCHAIN_BIN $ENV{HOME}/.local/opt/stm32/bin)
set(CMAKE_C_COMPILER ${TOOLCHAIN_BIN}/arm-none-eabi-gcc)
set(CMAKE_CXX_COMPILER ${TOOLCHAIN_BIN}/arm-none-eabi-g++)
set(CMAKE_AR ${TOOLCHAIN_BIN}/arm-none-eabi-ar)
set(CMAKE_RANLIB ${TOOLCHAIN_BIN}/arm-none-eabi-ranlib)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)

set(FLAGS "-O2 -ffunction-sections -fdata-sections --param max-inline-insns-single=500 -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard -DCLOCK_MONOTONIC=0 -D'__attribute__(x)='" CACHE STRING "" FORCE)
set(CMAKE_C_FLAGS_INIT "${FLAGS} -std=c11" CACHE STRING "" FORCE)
# The user-local toolchain (~/.local/opt/stm32/root, extracted from .deb files) needs the libstdc++ headers
# added by hand; rosidl_typesupport_c in Jazzy generates a few .cpp files that include <cstddef>.
set(CXXINC "$ENV{HOME}/.local/opt/stm32/root/usr/include/newlib/c++/13.2.1")
set(CMAKE_CXX_FLAGS_INIT "${FLAGS} -std=c++14 -fno-exceptions -fno-rtti -isystem ${CXXINC} -isystem ${CXXINC}/arm-none-eabi/thumb/v7e-m+fp/hard" CACHE STRING "" FORCE)
set(__BIG_ENDIAN__ 0)
