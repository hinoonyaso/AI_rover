# 한글: 사용자 로컬 ARM 툴체인(~/.local/opt/stm32/bin) 설정.
# Cross toolchain for the STM32F407 target. The toolchain lives in ~/.local/opt/stm32/bin
# (installed by the user, see setup/ENVIRONMENT_SETUP.md section 8).
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)
set(TOOLCHAIN_BIN $ENV{HOME}/.local/opt/stm32/bin)
set(CMAKE_C_COMPILER ${TOOLCHAIN_BIN}/arm-none-eabi-gcc)
set(CMAKE_CXX_COMPILER ${TOOLCHAIN_BIN}/arm-none-eabi-g++)
set(CMAKE_ASM_COMPILER ${TOOLCHAIN_BIN}/arm-none-eabi-gcc)
set(CMAKE_OBJCOPY ${TOOLCHAIN_BIN}/arm-none-eabi-objcopy)
set(CMAKE_SIZE ${TOOLCHAIN_BIN}/arm-none-eabi-size)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_C_FLAGS_INIT "-mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16 -ffunction-sections -fdata-sections")
set(CMAKE_ASM_FLAGS_INIT "-mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16")
