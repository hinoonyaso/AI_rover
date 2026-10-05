/* 한글: 진입점: HAL 초기화 → 클럭 → 싱글톤 → 태스크 생성 → 스케줄러 시작. */
#include "FreeRTOS.h"
#include "app.h"
#include "board.h"
#include "drv_motor.h"
#include "system.h"
#include "task.h"

int main(void)
{
    HAL_Init();
    system_capture_reset_cause(); /* before anything clears RCC_CSR */
    system_clock_config();
    system_set_safe_state_hook(app_safe_state);

    app_init();
    app_create_tasks();
    vTaskStartScheduler();
    system_fatal("scheduler");
    return 0;
}
