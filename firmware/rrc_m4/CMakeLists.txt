cmake_minimum_required(VERSION 3.16)
project(rrc_m4 C ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Host-native build for the protocol codec + its unit tests (no ARM
# toolchain, no target hardware needed). Set to OFF once this project also
# gains an ARM cross-compile target for the actual firmware.
option(RRC_BUILD_HOST_TESTS "Build lib/protocol's host-native unit tests" ON)

if(CMAKE_CROSSCOMPILING)
    set(RRC_BUILD_HOST_TESTS OFF)
endif()
if(RRC_BUILD_HOST_TESTS)
    enable_testing()
endif()
add_subdirectory(lib/protocol)
add_subdirectory(lib/core)
add_subdirectory(lib/comm)

# ---------------------------------------------------------------------------
# ARM firmware (cross build): cmake -S . -B build-arm -DCMAKE_TOOLCHAIN_FILE=cmake/arm-none-eabi.cmake
#     -DCOMM_MODE=RRC|MICROROS -DMOTOR_ENABLE=0|1
# ---------------------------------------------------------------------------
if(CMAKE_CROSSCOMPILING)
    include(cmake/firmware.cmake)
endif()
