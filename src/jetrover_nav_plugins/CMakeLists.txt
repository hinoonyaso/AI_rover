cmake_minimum_required(VERSION 3.8)
project(jetrover_nav_plugins)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(nav2_mppi_controller REQUIRED)
find_package(nav2_core REQUIRED)
find_package(pluginlib REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)
find_package(xtensor REQUIRED)

# Same flags as nav2_mppi_controller (xtensor). / nav2_mppi_controller와 같은 최적화 옵션
add_compile_options(-O3 -fno-math-errno -fno-signed-zeros)

add_library(lateral_ratio_critic SHARED src/lateral_ratio_critic.cpp)
target_include_directories(lateral_ratio_critic PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
target_compile_features(lateral_ratio_critic PUBLIC cxx_std_17)
ament_target_dependencies(lateral_ratio_critic nav2_mppi_controller nav2_core pluginlib rclcpp_lifecycle xtensor)

# MPPI looks critics up through the nav2_mppi_controller class loader.
# 한글: MPPI는 nav2_mppi_controller 이름으로 critic 플러그인을 찾는다.
pluginlib_export_plugin_description_file(nav2_mppi_controller critics.xml)

install(TARGETS lateral_ratio_critic
  ARCHIVE DESTINATION lib LIBRARY DESTINATION lib RUNTIME DESTINATION bin)
install(DIRECTORY include/ DESTINATION include)
install(FILES critics.xml DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
  find_package(ament_cmake_gtest REQUIRED)
  ament_add_gtest(test_lateral_ratio test/test_lateral_ratio.cpp)
  target_include_directories(test_lateral_ratio PRIVATE include)
  ament_target_dependencies(test_lateral_ratio xtensor)
endif()

ament_export_include_directories(include)
ament_export_libraries(lateral_ratio_critic)
ament_package()
