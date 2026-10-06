cmake_minimum_required(VERSION 3.8)
project(jetrover_base)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)

add_library(${PROJECT_NAME}_lib
  src/serial_port.cpp
  src/rrc_protocol.cpp
  src/mecanum.cpp
  src/crash_guard.cpp
)
target_include_directories(${PROJECT_NAME}_lib PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/include
)
target_compile_features(${PROJECT_NAME}_lib PUBLIC cxx_std_17)

add_executable(base_node src/base_node.cpp)
target_link_libraries(base_node ${PROJECT_NAME}_lib)
ament_target_dependencies(base_node rclcpp geometry_msgs nav_msgs sensor_msgs std_msgs)

install(TARGETS base_node DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY config launch DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  find_package(ament_cmake_gtest REQUIRED)
  # RRC 코덱 단위시험(하드웨어 불필요) / RRC codec unit tests (no hardware)
  ament_add_gtest(test_rrc_protocol test/test_rrc_protocol.cpp)
  target_link_libraries(test_rrc_protocol ${PROJECT_NAME}_lib)
  ament_add_gtest(test_mecanum test/test_mecanum.cpp)
  target_link_libraries(test_mecanum ${PROJECT_NAME}_lib)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
