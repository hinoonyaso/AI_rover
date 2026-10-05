/* 한글: 부팅 시 GPIO 안전 상태(벤더 MX_GPIO_Init 복제), LED/부저/버튼, 배터리 ADC+DMA, PWM 서보(4슬롯 × 5ms = 20ms 프레임, 첫 명령 전까지 펄스 없음). */
#include "drv_misc.h"

#include "app_config.h"
#include "board.h"

/* ================= safe GPIO defaults (vendor MX_GPIO_Init) ================= */
void drv_gpio_safe_init(void)
{
    GPIO_InitTypeDef g = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_GPIOD_CLK_ENABLE();
    __HAL_RCC_GPIOE_CLK_ENABLE();

    /* levels first, then switch to output (no glitch) */
    HAL_GPIO_WritePin(GPIOE, GPIO_PIN_7 | GPIO_PIN_8, GPIO_PIN_SET);
    HAL_GPIO_WritePin(GPIOE, GPIO_PIN_10, GPIO_PIN_RESET); /* LED on, like the stock firmware at boot */
    HAL_GPIO_WritePin(GPIOD, GPIO_PIN_11 | GPIO_PIN_12 | GPIO_PIN_14, GPIO_PIN_SET);
    HAL_GPIO_WritePin(GPIOD, GPIO_PIN_13, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_8, GPIO_PIN_SET);
    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_9, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_8 | GPIO_PIN_11 | GPIO_PIN_12, GPIO_PIN_RESET);

    g.Mode = GPIO_MODE_OUTPUT_PP;
    g.Pull = GPIO_NOPULL;
    g.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    g.Pin = GPIO_PIN_7 | GPIO_PIN_8;
    HAL_GPIO_Init(GPIOE, &g);
    g.Speed = GPIO_SPEED_FREQ_LOW;
    g.Pin = GPIO_PIN_10;
    HAL_GPIO_Init(GPIOE, &g);
    g.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    g.Pin = GPIO_PIN_11 | GPIO_PIN_12 | GPIO_PIN_13 | GPIO_PIN_14;
    HAL_GPIO_Init(GPIOD, &g);
    g.Speed = GPIO_SPEED_FREQ_LOW;
    g.Pin = GPIO_PIN_8;
    HAL_GPIO_Init(GPIOC, &g);
    g.Speed = GPIO_SPEED_FREQ_HIGH;
    g.Pin = GPIO_PIN_9;
    HAL_GPIO_Init(GPIOC, &g);
    g.Pin = GPIO_PIN_8; /* buzzer: pull-down so it is silent while the pin is not driven */
    g.Pull = GPIO_PULLDOWN;
    g.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOA, &g);
    g.Pull = GPIO_NOPULL;
    g.Speed = GPIO_SPEED_FREQ_HIGH;
    g.Pin = GPIO_PIN_11 | GPIO_PIN_12;
    HAL_GPIO_Init(GPIOA, &g);

    /* buttons */
    g.Mode = GPIO_MODE_INPUT;
    g.Pull = GPIO_NOPULL; /* external 10k pull-ups */
    g.Pin = GPIO_PIN_0 | GPIO_PIN_1;
    HAL_GPIO_Init(GPIOE, &g);
}

void drv_ui_gpio_init(void) {}
void drv_led_write(int on) { HAL_GPIO_WritePin(LED_PORT, LED_PIN, on ? GPIO_PIN_RESET : GPIO_PIN_SET); }
void drv_buzzer_write(int on) { HAL_GPIO_WritePin(BUZZER_PORT, BUZZER_PIN, on ? GPIO_PIN_SET : GPIO_PIN_RESET); }
int drv_key_pressed(uint8_t i)
{
    return i == 0 ? HAL_GPIO_ReadPin(KEY1_PORT, KEY1_PIN) == GPIO_PIN_RESET
                  : HAL_GPIO_ReadPin(KEY2_PORT, KEY2_PIN) == GPIO_PIN_RESET;
}

/* ================= battery ================= */
static ADC_HandleTypeDef hadc1;
static DMA_HandleTypeDef hdma_adc1;
static volatile uint16_t g_adc[2];

void drv_battery_init(void)
{
    GPIO_InitTypeDef g = {0};
    ADC_ChannelConfTypeDef ch = {0};

    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_ADC1_CLK_ENABLE();
    __HAL_RCC_DMA2_CLK_ENABLE();
    g.Pin = GPIO_PIN_0;
    g.Mode = GPIO_MODE_ANALOG;
    g.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOB, &g);

    hdma_adc1.Instance = DMA2_Stream0;
    hdma_adc1.Init.Channel = DMA_CHANNEL_0;
    hdma_adc1.Init.Direction = DMA_PERIPH_TO_MEMORY;
    hdma_adc1.Init.PeriphInc = DMA_PINC_DISABLE;
    hdma_adc1.Init.MemInc = DMA_MINC_ENABLE;
    hdma_adc1.Init.PeriphDataAlignment = DMA_PDATAALIGN_HALFWORD;
    hdma_adc1.Init.MemDataAlignment = DMA_MDATAALIGN_HALFWORD;
    hdma_adc1.Init.Mode = DMA_NORMAL;
    hdma_adc1.Init.Priority = DMA_PRIORITY_LOW;
    hdma_adc1.Init.FIFOMode = DMA_FIFOMODE_DISABLE;
    HAL_DMA_Init(&hdma_adc1);

    hadc1.Instance = ADC1;
    hadc1.Init.ClockPrescaler = ADC_CLOCK_SYNC_PCLK_DIV8;
    hadc1.Init.Resolution = ADC_RESOLUTION_12B;
    hadc1.Init.ScanConvMode = ENABLE;
    hadc1.Init.ContinuousConvMode = DISABLE;
    hadc1.Init.DiscontinuousConvMode = DISABLE;
    hadc1.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_NONE;
    hadc1.Init.ExternalTrigConv = ADC_SOFTWARE_START;
    hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
    hadc1.Init.NbrOfConversion = 2;
    hadc1.Init.DMAContinuousRequests = DISABLE;
    hadc1.Init.EOCSelection = ADC_EOC_SEQ_CONV;
    __HAL_LINKDMA(&hadc1, DMA_Handle, hdma_adc1);
    HAL_ADC_Init(&hadc1);

    /* Vref channel: rank 1 (adc[0]) then PB0: rank 2 (adc[1]) - same order as the vendor */
    ch.Channel = ADC_CHANNEL_VREFINT;
    ch.Rank = 1;
    ch.SamplingTime = ADC_SAMPLETIME_480CYCLES;
    HAL_ADC_ConfigChannel(&hadc1, &ch);
    ch.Channel = ADC_CHANNEL_8;
    ch.Rank = 2;
    HAL_ADC_ConfigChannel(&hadc1, &ch);
}

void drv_battery_trigger(void)
{
    HAL_ADC_Start_DMA(&hadc1, (uint32_t *)g_adc, 2);
}

void drv_battery_get(uint16_t *vref, uint16_t *pb0)
{
    *vref = g_adc[0];
    *pb0 = g_adc[1];
}

/* ================= PWM servos: slotted software PWM ================= */
typedef struct {
    GPIO_TypeDef *port;
    uint16_t pin;
} servo_pin_t;
static const servo_pin_t SERVO_PINS[PWM_SERVO_COUNT] = PWM_SERVO_PINS_INIT;
static volatile uint16_t g_servo_us[PWM_SERVO_COUNT] = {1500, 1500, 1500, 1500};
static TIM_HandleTypeDef htim13;
static volatile uint8_t g_servo_slot;
static volatile uint8_t g_servo_running;

void drv_pwm_servo_init(void)
{
    __HAL_RCC_TIM13_CLK_ENABLE();
    htim13.Instance = TIM13;
    htim13.Init.Prescaler = 83; /* 84 MHz / 84 = 1 MHz */
    htim13.Init.Period = 5000 - 1; /* 4 servos x 5 ms = 20 ms frame */
    htim13.Init.CounterMode = TIM_COUNTERMODE_UP;
    HAL_TIM_Base_Init(&htim13);
    HAL_NVIC_SetPriority(TIM8_UP_TIM13_IRQn, 5, 0);
}

void drv_pwm_servo_set_pulse(uint8_t idx, uint16_t us)
{
    if (idx < PWM_SERVO_COUNT) {
        g_servo_us[idx] = us;
    }
}

/* 한글: 첫 서보 명령에서만 TIM13을 시작한다(그전에는 추정 핀에 펄스를 내보내지 않음). */
void drv_pwm_servo_enable(void)
{
    if (g_servo_running) {
        return;
    }
    g_servo_running = 1;
    HAL_NVIC_EnableIRQ(TIM8_UP_TIM13_IRQn);
    __HAL_TIM_SET_COUNTER(&htim13, 0);
    __HAL_TIM_CLEAR_FLAG(&htim13, TIM_FLAG_UPDATE | TIM_FLAG_CC1);
    __HAL_TIM_ENABLE_IT(&htim13, TIM_IT_UPDATE | TIM_IT_CC1);
    __HAL_TIM_SET_COMPARE(&htim13, TIM_CHANNEL_1, 1500);
    __HAL_TIM_ENABLE(&htim13);
}

/* 한글: 서보 슬롯 방식 소프트 PWM: 업데이트에서 해당 슬롯 핀을 올리고, 비교 일치에서 내린 뒤 다음 슬롯으로. */
void TIM8_UP_TIM13_IRQHandler(void)
{
    if (__HAL_TIM_GET_FLAG(&htim13, TIM_FLAG_UPDATE)) { /* slot start: raise the pin of this slot */
        __HAL_TIM_CLEAR_FLAG(&htim13, TIM_FLAG_UPDATE);
        const uint8_t s = g_servo_slot;
        __HAL_TIM_SET_COMPARE(&htim13, TIM_CHANNEL_1, g_servo_us[s]);
        HAL_GPIO_WritePin(SERVO_PINS[s].port, SERVO_PINS[s].pin, GPIO_PIN_SET);
    }
    if (__HAL_TIM_GET_FLAG(&htim13, TIM_FLAG_CC1)) { /* end of pulse: lower it, next slot */
        __HAL_TIM_CLEAR_FLAG(&htim13, TIM_FLAG_CC1);
        const uint8_t s = g_servo_slot;
        HAL_GPIO_WritePin(SERVO_PINS[s].port, SERVO_PINS[s].pin, GPIO_PIN_RESET);
        g_servo_slot = (uint8_t)((s + 1) % PWM_SERVO_COUNT);
    }
}
