cmake_minimum_required(VERSION 3.8)
project(jetrover_perception)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch config DESTINATION share/${PROJECT_NAME})
install(PROGRAMS scripts/depth_colorizer.py scripts/sparse_point_cloud.py scripts/cube_detector.py
  scripts/depth_scan_filter.py
  DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_cube_detector test/test_cube_detector.py)
  ament_add_pytest_test(test_stack_light test/test_stack_light.py)
  ament_add_pytest_test(test_depth_scan_filter test/test_depth_scan_filter.py)
  ament_add_pytest_test(test_depth_source_guard test/test_depth_source_guard.py)
  ament_add_pytest_test(test_floor_plane test/test_floor_plane.py)
endif()

ament_package()
