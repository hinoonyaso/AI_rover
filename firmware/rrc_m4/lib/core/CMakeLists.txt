add_library(rrc_core STATIC
    src/pid.c
    src/encoder_motor.c
    src/mecanum.c
    src/robot_ctrl.c
    src/blink.c
    src/button.c
    src/pwm_servo.c
    src/bus_servo.c
    src/sbus.c
    src/gamepad.c
    src/imu.c
    src/battery.c
    src/local_drive.c
)
target_include_directories(rrc_core PUBLIC include)
target_compile_options(rrc_core PRIVATE -Wall -Wextra)
if(NOT CMAKE_CROSSCOMPILING)
    target_link_libraries(rrc_core PUBLIC m)
endif()

if(RRC_BUILD_HOST_TESTS)
    add_executable(test_core tests/test_core.c)
    target_link_libraries(test_core PRIVATE rrc_core)
    add_test(NAME core_tests COMMAND test_core)
endif()
