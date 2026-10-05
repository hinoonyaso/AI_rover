// 한글: FreeRTOS 설정(STM32F407, 168MHz).
#ifndef FREERTOS_CONFIG_H
#define FREERTOS_CONFIG_H

#include <stdint.h>
#include "app_config.h"
extern uint32_t SystemCoreClock;

// 한글: 스케줄러: 선점형, 1kHz 틱, 우선순위 8단계(0~7, 높을수록 우선).
#define configUSE_PREEMPTION 1
#define configUSE_TIME_SLICING 1
#define configCPU_CLOCK_HZ (SystemCoreClock)
#define configTICK_RATE_HZ ((TickType_t)1000)
#define configMAX_PRIORITIES 8
#define configMINIMAL_STACK_SIZE ((uint16_t)128)
#define configMAX_TASK_NAME_LEN 16
#define configUSE_16_BIT_TICKS 0
#define configUSE_MUTEXES 1
#define configUSE_RECURSIVE_MUTEXES 1
#define configUSE_COUNTING_SEMAPHORES 1
#define configQUEUE_REGISTRY_SIZE 0
#define configUSE_TASK_NOTIFICATIONS 1
#define configTASK_NOTIFICATION_ARRAY_ENTRIES 1
#define configUSE_IDLE_HOOK 1
#define configUSE_TICK_HOOK 0
#define configUSE_MALLOC_FAILED_HOOK 1
#define configCHECK_FOR_STACK_OVERFLOW 2
#define configUSE_TRACE_FACILITY 1
#define configUSE_STATS_FORMATTING_FUNCTIONS 0
#define configGENERATE_RUN_TIME_STATS 0
#define configUSE_STREAM_BUFFERS 1

/* Memory: dynamic heap (heap_4, used by micro-ROS) + static allocation for the fixed tasks. */
// 한글: 메모리: 고정 태스크는 정적 할당(스택은 CCM), micro-ROS가 쓰는 동적 힙은 heap_4.
#define configSUPPORT_STATIC_ALLOCATION 1
#define configSUPPORT_DYNAMIC_ALLOCATION 1
#define configTOTAL_HEAP_SIZE ((size_t)(RRC_FREERTOS_HEAP_BYTES))
#define configAPPLICATION_ALLOCATED_HEAP 0

// 한글: 소프트웨어 타이머 태스크는 쓰지 않는다(주기 작업은 ui_task가 담당).
#define configUSE_TIMERS 0

#define INCLUDE_vTaskPrioritySet 1
#define INCLUDE_uxTaskPriorityGet 1
#define INCLUDE_vTaskDelete 1
#define INCLUDE_vTaskSuspend 1
#define INCLUDE_vTaskDelayUntil 1
#define INCLUDE_vTaskDelay 1
#define INCLUDE_xTaskGetSchedulerState 1
#define INCLUDE_xTaskGetCurrentTaskHandle 1
#define INCLUDE_uxTaskGetStackHighWaterMark 1
#define INCLUDE_xTaskGetIdleTaskHandle 1
#define INCLUDE_eTaskGetState 1
#define INCLUDE_xTaskAbortDelay 1

/* Cortex-M4F, 4 priority bits. Interrupts at priority >= 5 may call FromISR APIs. */
#ifdef __NVIC_PRIO_BITS
#define configPRIO_BITS __NVIC_PRIO_BITS
#else
#define configPRIO_BITS 4
#endif
// 한글: Cortex-M4F 4비트 우선순위: 숫자 5 이상인 인터럽트만 FromISR API를 호출할 수 있다(드라이버 IRQ는 모두 5).
#define configLIBRARY_LOWEST_INTERRUPT_PRIORITY 15
#define configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY 5
#define configKERNEL_INTERRUPT_PRIORITY (configLIBRARY_LOWEST_INTERRUPT_PRIORITY << (8 - configPRIO_BITS))
#define configMAX_SYSCALL_INTERRUPT_PRIORITY (configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY << (8 - configPRIO_BITS))

// 한글: assert 실패 시 모터를 끄고 멈춘다(IWDG가 리셋).
#define configASSERT(x) do { if ((x) == 0) { rrc_assert_failed(__FILE__, __LINE__); } } while (0)
void rrc_assert_failed(const char *file, int line);

// 한글: FreeRTOS 포트 핸들러를 Cortex-M 예외 벡터 이름에 연결한다.
#define vPortSVCHandler SVC_Handler
#define xPortPendSVHandler PendSV_Handler
#define xPortSysTickHandler SysTick_Handler

#endif
