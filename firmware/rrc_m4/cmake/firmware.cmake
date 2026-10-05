# 한글: 펌웨어 타깃: COMM_MODE(RRC/MICROROS), MOTOR_ENABLE, LOCAL_DRIVE_ENABLE 옵션. 크로스 컴파일일 때만 포함된다.
# Firmware target. Included only when cross-compiling.
set(COMM_MODE "RRC" CACHE STRING "RRC or MICROROS")
set_property(CACHE COMM_MODE PROPERTY STRINGS RRC MICROROS)
option(MOTOR_ENABLE "Drive the motors (default OFF until bring-up checks pass)" OFF)
option(LOCAL_DRIVE_ENABLE "Allow Bluetooth/gamepad/SBUS to drive the robot" OFF)

set(TP ${CMAKE_SOURCE_DIR}/third_party)
set(CPU_FLAGS -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16)

file(GLOB HAL_SRC ${TP}/stm32f4xx_hal_driver/Src/stm32f4xx_hal*.c ${TP}/stm32f4xx_hal_driver/Src/stm32f4xx_ll_usb.c)
list(FILTER HAL_SRC EXCLUDE REGEX "_template|msp_template|timebase")
# only compile the HAL modules enabled in stm32f4xx_hal_conf.h
set(HAL_KEEP hal hal_adc hal_adc_ex hal_cortex hal_dma hal_dma_ex hal_exti hal_flash hal_flash_ex hal_flash_ramfunc
    hal_gpio hal_hcd hal_iwdg hal_pwr hal_pwr_ex hal_rcc hal_rcc_ex hal_spi hal_tim hal_tim_ex hal_uart ll_usb)
set(HAL_FILES "")
foreach(m ${HAL_KEEP})
    list(APPEND HAL_FILES ${TP}/stm32f4xx_hal_driver/Src/stm32f4xx_${m}.c)
endforeach()

set(RTOS_SRC
    ${TP}/FreeRTOS-Kernel/tasks.c ${TP}/FreeRTOS-Kernel/queue.c ${TP}/FreeRTOS-Kernel/list.c
    ${TP}/FreeRTOS-Kernel/stream_buffer.c ${TP}/FreeRTOS-Kernel/event_groups.c
    ${TP}/FreeRTOS-Kernel/portable/GCC/ARM_CM4F/port.c
    ${TP}/FreeRTOS-Kernel/portable/MemMang/heap_4.c)

set(APP_SRC
    app/src/main.c app/src/system.c app/src/stm32f4xx_it.c app/src/app.c app/src/app_comm.c app/src/tasks.c
    app/src/drv_motor.c app/src/drv_imu.c app/src/drv_misc.c app/src/drv_bus_servo.c app/src/drv_uart.c
    app/src/drv_lcd.c app/src/lcd_font.c app/src/usbh_conf.c app/src/usb_gamepad.c)
file(GLOB USBH_CORE ${TP}/stm32_mw_usb_host/Core/Src/usbh_core.c ${TP}/stm32_mw_usb_host/Core/Src/usbh_ctlreq.c
    ${TP}/stm32_mw_usb_host/Core/Src/usbh_ioreq.c ${TP}/stm32_mw_usb_host/Core/Src/usbh_pipes.c)
list(APPEND APP_SRC ${USBH_CORE})

set(INCLUDES
    app/inc
    ${TP}/cmsis_core/CMSIS/Core/Include
    ${TP}/cmsis_device_f4/Include
    ${TP}/stm32f4xx_hal_driver/Inc
    ${TP}/stm32_mw_usb_host/Core/Inc
    ${TP}/FreeRTOS-Kernel/include
    ${TP}/FreeRTOS-Kernel/portable/GCC/ARM_CM4F
    lib/core/include lib/comm/include lib/protocol/include)

set(MICROROS_DIR ${CMAKE_SOURCE_DIR}/micro_ros/firmware/build)
if(COMM_MODE STREQUAL "MICROROS")
    if(NOT EXISTS ${MICROROS_DIR}/libmicroros.a)
        message(FATAL_ERROR "libmicroros.a not found: run micro_ros/build_microros_lib.sh first")
    endif()
    list(APPEND APP_SRC app/src/comm_microros.c app/src/microros_support.c)
    list(APPEND INCLUDES ${MICROROS_DIR}/include)
endif()

add_executable(rrc_m4.elf ${APP_SRC} ${HAL_FILES} ${RTOS_SRC}
    ${TP}/cmsis_device_f4/Source/Templates/system_stm32f4xx.c
    ${TP}/cmsis_device_f4/Source/Templates/gcc/startup_stm32f407xx.s)
target_include_directories(rrc_m4.elf PRIVATE ${INCLUDES})
target_compile_definitions(rrc_m4.elf PRIVATE STM32F407xx USE_HAL_DRIVER
    COMM_MODE=COMM_MODE_${COMM_MODE})
if(MOTOR_ENABLE)
    target_compile_definitions(rrc_m4.elf PRIVATE MOTOR_ENABLE=1)
endif()
if(LOCAL_DRIVE_ENABLE)
    target_compile_definitions(rrc_m4.elf PRIVATE LOCAL_DRIVE_ENABLE=1)
endif()
target_compile_options(rrc_m4.elf PRIVATE ${CPU_FLAGS} -Os -g3 -ffunction-sections -fdata-sections
    -Wall -Wextra -Wno-unused-parameter -fno-common -fstack-usage)
target_link_options(rrc_m4.elf PRIVATE ${CPU_FLAGS}
    -T${CMAKE_SOURCE_DIR}/app/linker/STM32F407VETx_FLASH.ld
    -Wl,--gc-sections -Wl,-Map=rrc_m4.map --specs=nano.specs --specs=nosys.specs -Wl,--print-memory-usage)
target_link_libraries(rrc_m4.elf PRIVATE rrc_comm rrc_core rrc_protocol)
if(COMM_MODE STREQUAL "MICROROS")
    target_link_libraries(rrc_m4.elf PRIVATE ${MICROROS_DIR}/libmicroros.a)
endif()
target_link_libraries(rrc_m4.elf PRIVATE m c nosys)

add_custom_command(TARGET rrc_m4.elf POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O binary rrc_m4.elf rrc_m4.bin
    COMMAND ${CMAKE_OBJCOPY} -O ihex rrc_m4.elf rrc_m4.hex
    COMMAND ${CMAKE_SIZE} rrc_m4.elf)
