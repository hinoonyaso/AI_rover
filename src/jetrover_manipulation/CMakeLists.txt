cmake_minimum_required(VERSION 3.8)
project(jetrover_manipulation)

find_package(ament_cmake REQUIRED)

# 한글: 설정/launch 파일만 설치한다(코드 없음). / Config + launch only, no compiled code yet.
install(DIRECTORY config launch DESTINATION share/${PROJECT_NAME})

# 한글: 브리지 노드(Python)와 시험 설치. / Bridge node (Python) + tests.
install(PROGRAMS scripts/trajectory_bridge.py DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_bridge_logic test/test_bridge_logic.py)
endif()

ament_package()
