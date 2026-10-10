/* 한글: 모터/엔코더 드라이버. 모터1 핀 배정은 확정(공식 문서), 모터2~4는 추정. 엔코더 타이머는 ARR=60000, 오버플로 ISR이 overflow_num을 증감한다. */
/* 4 encoder motors: TIM1/TIM9/TIM10/TIM11 PWM (2 lines per motor), TIM2/3/4/5 encoders, TIM7 10 ms tick.
 * Pin/channel pairs are in firmware_source/PINMAP.md; motor 1 is CONFIRMED, motors 2..4 ASSUMED. */
#include "drv_motor.h"

#include "app_config.h"
#include "board.h"

typedef struct {
    TIM_HandleTypeDef *rev_tim;
    uint32_t rev_ch;
    TIM_HandleTypeDef *fwd_tim;
    uint32_t fwd_ch;
} pwm_pair_t;

static TIM_HandleTypeDef htim1, htim9, htim10, htim11; /* PWM */
static TIM_HandleTypeDef htim2, htim3, htim4, htim5;   /* encoders */
static TIM_HandleTypeDef htim7;

/* motor idx -> pair {rev, fwd}; "fwd" is driven for a positive pulse. 2026-10-10 RAW_PWM test (wheels
 * lifted): M0/M1 positive = roll forward, M3 positive = roll backward (mirrored right side, vendor
 * convention: right wheels have negative rps forward). M2 rolled FORWARD on positive with the assumed
 * CH1 rev / CH2 fwd, so its pair is swapped to match M3; then every encoder counts up on a positive
 * pulse (MOTOR_ENCODER_SIGN all +1). troubleshooting/036.
 * 한글: M2만 +PWM이 전진이라 짝을 맞바꿈 → 오른쪽 두 바퀴 모두 +PWM = 후진(vendor 규약), 엔코더 부호 전부 +1. */
static const pwm_pair_t PAIRS[4] = {
    {&htim1, TIM_CHANNEL_3, &htim1, TIM_CHANNEL_4},
    {&htim1, TIM_CHANNEL_1, &htim1, TIM_CHANNEL_2},
    {&htim9, TIM_CHANNEL_2, &htim9, TIM_CHANNEL_1},
    {&htim10, TIM_CHANNEL_1, &htim11, TIM_CHANNEL_1},
};
/* motor idx -> encoder timer (CONFIRMED: M1=TIM5, M2=TIM2, M3=TIM4, M4=TIM3) */
static TIM_HandleTypeDef *const ENC[4] = {&htim5, &htim2, &htim4, &htim3};

static enc_motor_t *g_motors[4];
static TaskHandle_t g_tick_task;

static void gpio_af(GPIO_TypeDef *port, uint32_t pins, uint32_t af, uint32_t pull)
{
    GPIO_InitTypeDef g = {0};
    g.Pin = pins;
    g.Mode = GPIO_MODE_AF_PP;
    g.Pull = pull;
    g.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    g.Alternate = af;
    HAL_GPIO_Init(port, &g);
}

static void pwm_timer_init(TIM_HandleTypeDef *h, TIM_TypeDef *inst, uint32_t ch_mask)
{
    TIM_OC_InitTypeDef oc = {0};
    h->Instance = inst;
    h->Init.Prescaler = MOTOR_PWM_PSC;
    h->Init.CounterMode = TIM_COUNTERMODE_UP;
    h->Init.Period = MOTOR_PWM_ARR;
    h->Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    h->Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
    HAL_TIM_PWM_Init(h);
    oc.OCMode = TIM_OCMODE_PWM1;
    oc.Pulse = 0;
    oc.OCPolarity = TIM_OCPOLARITY_HIGH;
    oc.OCFastMode = TIM_OCFAST_DISABLE;
    oc.OCNPolarity = TIM_OCNPOLARITY_HIGH;
    oc.OCIdleState = TIM_OCIDLESTATE_RESET;
    oc.OCNIdleState = TIM_OCNIDLESTATE_RESET;
    for (uint32_t ch = 0; ch < 4; ch++) {
        if (ch_mask & (1u << ch)) {
            HAL_TIM_PWM_ConfigChannel(h, &oc, ch * 4u);
            HAL_TIM_PWM_Start(h, ch * 4u);
        }
    }
}

static void enc_timer_init(TIM_HandleTypeDef *h, TIM_TypeDef *inst)
{
    TIM_Encoder_InitTypeDef e = {0};
    TIM_MasterConfigTypeDef m = {0};
    h->Instance = inst;
    h->Init.Prescaler = 0;
    h->Init.CounterMode = TIM_COUNTERMODE_UP;
    h->Init.Period = MOTOR_ENCODER_TIM_OVERFLOW;
    h->Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    h->Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    e.EncoderMode = TIM_ENCODERMODE_TI12;
    e.IC1Polarity = TIM_ICPOLARITY_RISING;
    e.IC1Selection = TIM_ICSELECTION_DIRECTTI;
    e.IC1Prescaler = TIM_ICPSC_DIV1;
    e.IC1Filter = 0;
    e.IC2Polarity = TIM_ICPOLARITY_RISING;
    e.IC2Selection = TIM_ICSELECTION_DIRECTTI;
    e.IC2Prescaler = TIM_ICPSC_DIV1;
    e.IC2Filter = 0;
    HAL_TIM_Encoder_Init(h, &e);
    m.MasterOutputTrigger = TIM_TRGO_RESET;
    m.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
    HAL_TIMEx_MasterConfigSynchronization(h, &m);
    __HAL_TIM_SET_COUNTER(h, 0);
    __HAL_TIM_CLEAR_IT(h, TIM_IT_UPDATE);
    __HAL_TIM_ENABLE_IT(h, TIM_IT_UPDATE);
    HAL_TIM_Encoder_Start(h, TIM_CHANNEL_ALL);
}

void drv_motor_init(enc_motor_t *motors[4])
{
    for (int i = 0; i < 4; i++) {
        g_motors[i] = motors[i];
    }
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_GPIOD_CLK_ENABLE();
    __HAL_RCC_GPIOE_CLK_ENABLE();
    __HAL_RCC_TIM1_CLK_ENABLE();
    __HAL_RCC_TIM9_CLK_ENABLE();
    __HAL_RCC_TIM10_CLK_ENABLE();
    __HAL_RCC_TIM11_CLK_ENABLE();
    __HAL_RCC_TIM2_CLK_ENABLE();
    __HAL_RCC_TIM3_CLK_ENABLE();
    __HAL_RCC_TIM4_CLK_ENABLE();
    __HAL_RCC_TIM5_CLK_ENABLE();
    __HAL_RCC_TIM7_CLK_ENABLE();

    /* PWM pins */
    gpio_af(GPIOE, GPIO_PIN_9 | GPIO_PIN_11 | GPIO_PIN_13 | GPIO_PIN_14, GPIO_AF1_TIM1, GPIO_NOPULL);
    gpio_af(GPIOE, GPIO_PIN_5 | GPIO_PIN_6, GPIO_AF3_TIM9, GPIO_NOPULL);
    gpio_af(GPIOB, GPIO_PIN_8, GPIO_AF3_TIM10, GPIO_NOPULL);
    gpio_af(GPIOB, GPIO_PIN_9, GPIO_AF3_TIM11, GPIO_NOPULL);
    /* encoder pins */
    gpio_af(GPIOA, GPIO_PIN_15, GPIO_AF1_TIM2, GPIO_PULLUP);
    gpio_af(GPIOB, GPIO_PIN_3, GPIO_AF1_TIM2, GPIO_PULLUP);
    gpio_af(GPIOB, GPIO_PIN_4 | GPIO_PIN_5, GPIO_AF2_TIM3, GPIO_NOPULL);
    gpio_af(GPIOB, GPIO_PIN_6 | GPIO_PIN_7, GPIO_AF2_TIM4, GPIO_NOPULL);
    gpio_af(GPIOA, GPIO_PIN_0 | GPIO_PIN_1, GPIO_AF2_TIM5, GPIO_NOPULL);
    /* fault input */
    GPIO_InitTypeDef g = {0};
    g.Pin = MOTOR_FAULT_PIN;
    g.Mode = GPIO_MODE_INPUT;
    g.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(MOTOR_FAULT_PORT, &g);

    pwm_timer_init(&htim1, TIM1, 0xF);
    __HAL_TIM_MOE_ENABLE(&htim1);
    pwm_timer_init(&htim9, TIM9, 0x3);
    pwm_timer_init(&htim10, TIM10, 0x1);
    pwm_timer_init(&htim11, TIM11, 0x1);
    drv_motor_all_off();

    enc_timer_init(&htim2, TIM2);
    enc_timer_init(&htim3, TIM3);
    enc_timer_init(&htim4, TIM4);
    enc_timer_init(&htim5, TIM5);
    HAL_NVIC_SetPriority(TIM2_IRQn, 5, 0);
    HAL_NVIC_SetPriority(TIM3_IRQn, 5, 0);
    HAL_NVIC_SetPriority(TIM4_IRQn, 5, 0);
    HAL_NVIC_SetPriority(TIM5_IRQn, 5, 0);
    HAL_NVIC_EnableIRQ(TIM2_IRQn);
    HAL_NVIC_EnableIRQ(TIM3_IRQn);
    HAL_NVIC_EnableIRQ(TIM4_IRQn);
    HAL_NVIC_EnableIRQ(TIM5_IRQn);
}

void drv_motor_start_tick(TaskHandle_t t)
{
    g_tick_task = t;
    htim7.Instance = TIM7;
    htim7.Init.Prescaler = 83; /* 84 MHz / 84 = 1 MHz */
    htim7.Init.Period = 9999;  /* 10 ms */
    htim7.Init.CounterMode = TIM_COUNTERMODE_UP;
    HAL_TIM_Base_Init(&htim7);
    HAL_NVIC_SetPriority(TIM7_IRQn, 5, 0);
    HAL_NVIC_EnableIRQ(TIM7_IRQn);
    HAL_TIM_Base_Start_IT(&htim7);
}

static void set_ccr(const pwm_pair_t *p, uint32_t rev, uint32_t fwd)
{
    __HAL_TIM_SET_COMPARE(p->rev_tim, p->rev_ch, rev);
    __HAL_TIM_SET_COMPARE(p->fwd_tim, p->fwd_ch, fwd);
}

/* 한글: 부호 있는 펄스(±1000): 양수는 정방향 핀에 PWM, 음수는 역방향 핀에 PWM. MOTOR_ENABLE=0이면 항상 0. */
void drv_motor_set_pulse(uint8_t idx, int pulse)
{
    if (idx >= 4) {
        return;
    }
#if !MOTOR_ENABLE
    pulse = 0;
#endif
    if (pulse > 1000) pulse = 1000;
    if (pulse < -1000) pulse = -1000;
    if (pulse > 0) {
        set_ccr(&PAIRS[idx], 0, (uint32_t)pulse);
    } else if (pulse < 0) {
        set_ccr(&PAIRS[idx], (uint32_t)(-pulse), 0);
    } else {
        set_ccr(&PAIRS[idx], 0, 0);
    }
}

int64_t drv_motor_read_counter(uint8_t idx)
{
    return (int64_t)__HAL_TIM_GET_COUNTER(ENC[idx]);
}

/* 한글: PD3 fault 입력(High=fault는 추정 극성). */
int drv_motor_fault_active(void)
{
    return HAL_GPIO_ReadPin(MOTOR_FAULT_PORT, MOTOR_FAULT_PIN) == GPIO_PIN_SET;
}

/* 한글: 레지스터만 만지는 안전 정지(폴트 핸들러/감독 태스크에서 호출 가능). */
void drv_motor_all_off(void)
{
    TIM1->CCR1 = TIM1->CCR2 = TIM1->CCR3 = TIM1->CCR4 = 0;
    TIM9->CCR1 = TIM9->CCR2 = 0;
    TIM10->CCR1 = 0;
    TIM11->CCR1 = 0;
}

/* ---- interrupts ---- */
static void enc_overflow_irq(TIM_HandleTypeDef *h, int motor)
{
    if (__HAL_TIM_GET_FLAG(h, TIM_FLAG_UPDATE) && __HAL_TIM_GET_IT_SOURCE(h, TIM_IT_UPDATE)) {
        __HAL_TIM_CLEAR_FLAG(h, TIM_FLAG_UPDATE);
        if (g_motors[motor]) {
            enc_motor_on_overflow(g_motors[motor], __HAL_TIM_IS_TIM_COUNTING_DOWN(h) ? 1 : 0);
        }
    }
}

void TIM5_IRQHandler(void) { enc_overflow_irq(&htim5, 0); }
void TIM2_IRQHandler(void) { enc_overflow_irq(&htim2, 1); }
void TIM4_IRQHandler(void) { enc_overflow_irq(&htim4, 2); }
void TIM3_IRQHandler(void) { enc_overflow_irq(&htim3, 3); }

/* 한글: 10ms 제어 틱: 제어 태스크를 깨운다. */
void TIM7_IRQHandler(void)
{
    if (__HAL_TIM_GET_FLAG(&htim7, TIM_FLAG_UPDATE)) {
        __HAL_TIM_CLEAR_FLAG(&htim7, TIM_FLAG_UPDATE);
        if (g_tick_task) {
            BaseType_t woken = pdFALSE;
            vTaskNotifyGiveFromISR(g_tick_task, &woken);
            portYIELD_FROM_ISR(woken);
        }
    }
}
