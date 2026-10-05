# third_party (vendor 복사본, 필요한 부분만 남김)

`git clone --depth 1` 후 `.git`과 문서/예제/테스트를 제거했다 (2026-10-05). 수정하지 않았다.

| 디렉터리 | 출처 | 커밋 | 라이선스 |
|---|---|---|---|
| `cmsis_core/` (CMSIS/Core/Include) | github.com/STMicroelectronics/cmsis_core | afc5ca6af0a49232fde7eb4548dd0962d119ce14 | Apache-2.0 |
| `cmsis_device_f4/` (Include, system_stm32f4xx.c, startup_stm32f407xx.s) | github.com/STMicroelectronics/cmsis_device_f4 | 9192c7b9df75a142f2027ab266601fe061fc00b3 | Apache-2.0 |
| `stm32f4xx_hal_driver/` | github.com/STMicroelectronics/stm32f4xx_hal_driver | 1f6451c3e07728b4c830744de380e56bf5bc0026 | BSD-3-Clause |
| `stm32_mw_usb_host/` (Core, Class/HID) | github.com/STMicroelectronics/stm32_mw_usb_host | d013fac0f8b97e8316a79ef946a7dbab4ef4431d | BSD-3-Clause/ST |
| `FreeRTOS-Kernel/` (ARM_CM4F, heap_4) | github.com/FreeRTOS/FreeRTOS-Kernel | 8be86d4a24fd4091f8f4192018423ab590f408db | MIT |

micro-ROS는 여기 두지 않는다: `micro_ros/` 디렉터리에서 별도 빌드한다 (`firmware/rrc_m4/micro_ros/README.md`).
