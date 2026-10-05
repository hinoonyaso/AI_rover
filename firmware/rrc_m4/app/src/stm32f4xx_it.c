/* 한글: 주변장치 IRQ는 각 드라이버 파일에 있고, 여기에는 나머지 예외 벡터만 둔다. */
/* Cortex-M exception vectors not owned by FreeRTOS/HAL drivers. Peripheral IRQ handlers live next to
 * their drivers (drv_*.c). SVC/PendSV/SysTick are mapped to the FreeRTOS port in FreeRTOSConfig.h;
 * HardFault/MemManage/BusFault/UsageFault are in system.c. */
#include "board.h"

void NMI_Handler(void) { for (;;) { } }
void DebugMon_Handler(void) {}
