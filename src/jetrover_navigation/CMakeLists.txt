cmake_minimum_required(VERSION 3.8)
project(jetrover_navigation)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch config DESTINATION share/${PROJECT_NAME})
# 한글: AMCL 초기 위치 자동 추정(스캔-지도 매칭), localization.launch.py가 실행한다.
install(PROGRAMS scripts/scan_match_init.py DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
