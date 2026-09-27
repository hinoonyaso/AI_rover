cmake_minimum_required(VERSION 3.16)
project(rrc_m4 C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Host-native build for the protocol codec + its unit tests (no ARM
# toolchain, no target hardware needed). Set to OFF once this project also
# gains an ARM cross-compile target for the actual firmware.
option(RRC_BUILD_HOST_TESTS "Build lib/protocol's host-native unit tests" ON)

add_subdirectory(lib/protocol)
