add_library(rrc_protocol STATIC
    src/rrc_protocol.c
    src/rrc_funcs.c
)
target_include_directories(rrc_protocol PUBLIC include)
target_compile_options(rrc_protocol PRIVATE -Wall -Wextra)

if(RRC_BUILD_HOST_TESTS)
    add_executable(test_protocol tests/test_protocol.c)
    target_link_libraries(test_protocol PRIVATE rrc_protocol)
    enable_testing()
    add_test(NAME protocol_tests COMMAND test_protocol)
endif()
