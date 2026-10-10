/* 한글: 클럭 트리(HSE 8MHz→168MHz), HAL 타임베이스(TIM6, SysTick은 FreeRTOS 전용), FreeRTOS 훅, newlib 스텁, 폴트 핸들러. */
/* Clock tree, HAL time base (TIM6), FreeRTOS hooks, newlib stubs, fault handlers. */
#include <errno.h>
#include <stdint.h>
#include <string.h>
#include <sys/stat.h>

#include "FreeRTOS.h"
#include "app_config.h"
#include "board.h"
#include "system.h"
#include "task.h"

static volatile uint32_t g_reset_cause;

uint32_t system_reset_cause(void) { return g_reset_cause; }

void system_capture_reset_cause(void)
{
    g_reset_cause = RCC->CSR >> 24; /* flags: LPWRRSTF..PINRSTF, IWDGRSTF is bit 29 -> bit 5 here */
    __HAL_RCC_CLEAR_RESET_FLAGS();
}

/* HSE 16 MHz -> SYSCLK 168 MHz, USB 48 MHz, APB1 42 MHz (timers 84 MHz), APB2 84 MHz (timers 168 MHz).
 * 2026-10-10: the crystal is 16 MHz, not 8 MHz (vendor binary: HAL_RCC_GetSysClockFreq uses 16000000 for
 * the PLL source, SystemClock_Config M=8 N=168 P=2). With the old 8 MHz assumption (M=8 N=336) the chip ran
 * at 336 MHz (VCO 672 MHz > 432 max), flash reads went random and the core locked up (troubleshooting/035).
 * 한글: 크리스털은 16 MHz(vendor 바이너리로 확인). 8 MHz 가정이면 336 MHz로 2배 오버클럭되어 lockup이 났다. */
void system_clock_config(void)
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};

    __HAL_RCC_PWR_CLK_ENABLE();
    __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);
    osc.OscillatorType = RCC_OSCILLATORTYPE_HSE | RCC_OSCILLATORTYPE_LSI;
    osc.HSEState = RCC_HSE_ON;
    osc.LSIState = RCC_LSI_ON;
    osc.PLL.PLLState = RCC_PLL_ON;
    osc.PLL.PLLSource = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLM = 8;   /* 16 MHz / 8 = 2 MHz VCO input (ST's recommended value, low jitter) */
    osc.PLL.PLLN = 168; /* VCO 336 MHz; /P2 = 168 MHz, /Q7 = 48 MHz (same as the vendor firmware) */
    osc.PLL.PLLP = RCC_PLLP_DIV2;
    osc.PLL.PLLQ = 7;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK) {
        system_fatal("HSE/PLL");
    }
    clk.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV4;
    clk.APB2CLKDivider = RCC_HCLK_DIV2;
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_5) != HAL_OK) {
        system_fatal("clock");
    }
}

/* HAL time base on TIM6 so SysTick belongs to FreeRTOS. */
static TIM_HandleTypeDef g_tim6;

/* 한글: HAL 시간 기준을 TIM6(1kHz)로 옮겨 SysTick을 FreeRTOS에 넘긴다. */
HAL_StatusTypeDef HAL_InitTick(uint32_t priority)
{
    (void)priority;
    __HAL_RCC_TIM6_CLK_ENABLE();
    g_tim6.Instance = TIM6;
    g_tim6.Init.Prescaler = (HAL_RCC_GetPCLK1Freq() * 2 / 1000000) - 1; /* 1 MHz */
    g_tim6.Init.Period = 1000 - 1;                                       /* 1 kHz */
    g_tim6.Init.CounterMode = TIM_COUNTERMODE_UP;
    if (HAL_TIM_Base_Init(&g_tim6) != HAL_OK) {
        return HAL_ERROR;
    }
    HAL_NVIC_SetPriority(TIM6_DAC_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(TIM6_DAC_IRQn);
    return HAL_TIM_Base_Start_IT(&g_tim6);
}

void TIM6_DAC_IRQHandler(void)
{
    if (__HAL_TIM_GET_FLAG(&g_tim6, TIM_FLAG_UPDATE)) {
        __HAL_TIM_CLEAR_FLAG(&g_tim6, TIM_FLAG_UPDATE);
        HAL_IncTick();
    }
}

/* ---- fatal path: outputs off (callers register a hook), then spin so the IWDG resets us ---- */
static void (*g_safe_hook)(void);

void system_set_safe_state_hook(void (*hook)(void)) { g_safe_hook = hook; }

/* 한글: 치명적 오류: 인터럽트 끄고 모터 출력 0(훅) 후 정지 — IWDG가 리셋한다. */
__attribute__((noreturn)) void system_fatal(const char *why)
{
    (void)why;
    __disable_irq();
    if (g_safe_hook) {
        g_safe_hook();
    }
    for (;;) {
    } /* IWDG is running: the MCU resets */
}

void rrc_assert_failed(const char *file, int line)
{
    (void)file;
    (void)line;
    system_fatal("assert");
}

void vApplicationMallocFailedHook(void) { system_fatal("malloc"); }

void vApplicationStackOverflowHook(TaskHandle_t t, char *name)
{
    (void)t;
    (void)name;
    system_fatal("stack");
}

void HardFault_Handler(void) { system_fatal("hardfault"); }
void MemManage_Handler(void) { system_fatal("memmanage"); }
void BusFault_Handler(void) { system_fatal("busfault"); }
void UsageFault_Handler(void) { system_fatal("usagefault"); }

/* Static allocation hooks (configSUPPORT_STATIC_ALLOCATION with timers off still needs idle). */
void vApplicationGetIdleTaskMemory(StaticTask_t **tcb, StackType_t **stack, uint32_t *size)
{
    static StaticTask_t idle_tcb;
    static StackType_t idle_stack[configMINIMAL_STACK_SIZE];
    *tcb = &idle_tcb;
    *stack = idle_stack;
    *size = configMINIMAL_STACK_SIZE;
}

/* ---- newlib stubs (no file system, heap via sbrk for libc/micro-ROS-internal malloc) ---- */
extern char end[]; /* from linker script */
extern char _estack[];
static char *g_brk;

void *_sbrk(int incr)
{
    if (!g_brk) {
        g_brk = end;
    }
    char *prev = g_brk;
    /* keep 4 KB for MSP below _estack */
    if ((uintptr_t)g_brk + (uintptr_t)incr > (uintptr_t)_estack - 0x1000u) {
        errno = ENOMEM;
        return (void *)-1;
    }
    g_brk += incr;
    return prev;
}

int _close(int fd) { (void)fd; return -1; }
int _fstat(int fd, struct stat *st) { (void)fd; st->st_mode = S_IFCHR; return 0; }
int _isatty(int fd) { (void)fd; return 1; }
int _lseek(int fd, int off, int whence) { (void)fd; (void)off; (void)whence; return 0; }
int _read(int fd, char *p, int n) { (void)fd; (void)p; (void)n; return 0; }
int _write(int fd, char *p, int n) { (void)fd; (void)p; return n; }
int _getpid(void) { return 1; }
int _kill(int pid, int sig) { (void)pid; (void)sig; errno = EINVAL; return -1; }
void _exit(int status) { (void)status; system_fatal("exit"); for (;;) { } }
