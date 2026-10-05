/* 한글: USB 호스트 저수준 드라이버(HAL HCD, OTG_HS 내장 FS PHY, PB14/PB15). VBUS 스위치 핀은 미확인이라 항상 전원이 켜져 있다고 가정한다. */
/* USB host low-level driver over HAL HCD (OTG_HS in full-speed mode with the embedded PHY). */
#include "usbh_core.h"

static HCD_HandleTypeDef hhcd;

void HAL_HCD_MspInit(HCD_HandleTypeDef *h)
{
    GPIO_InitTypeDef g = {0};
    if (h->Instance != USB_OTG_HS) {
        return;
    }
    __HAL_RCC_GPIOB_CLK_ENABLE();
    g.Pin = GPIO_PIN_14 | GPIO_PIN_15; /* DM, DP */
    g.Mode = GPIO_MODE_AF_PP;
    g.Pull = GPIO_NOPULL;
    g.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    g.Alternate = GPIO_AF12_OTG_HS_FS;
    HAL_GPIO_Init(GPIOB, &g);
    __HAL_RCC_USB_OTG_HS_CLK_ENABLE();
    HAL_NVIC_SetPriority(OTG_HS_IRQn, 5, 0);
    HAL_NVIC_EnableIRQ(OTG_HS_IRQn);
}

void HAL_HCD_MspDeInit(HCD_HandleTypeDef *h)
{
    if (h->Instance == USB_OTG_HS) {
        __HAL_RCC_USB_OTG_HS_CLK_DISABLE();
        HAL_NVIC_DisableIRQ(OTG_HS_IRQn);
    }
}

void OTG_HS_IRQHandler(void) { HAL_HCD_IRQHandler(&hhcd); }

void HAL_HCD_SOF_Callback(HCD_HandleTypeDef *h) { USBH_LL_IncTimer(h->pData); }
void HAL_HCD_Connect_Callback(HCD_HandleTypeDef *h) { USBH_LL_Connect(h->pData); }
void HAL_HCD_Disconnect_Callback(HCD_HandleTypeDef *h) { USBH_LL_Disconnect(h->pData); }
void HAL_HCD_PortEnabled_Callback(HCD_HandleTypeDef *h) { USBH_LL_PortEnabled(h->pData); }
void HAL_HCD_PortDisabled_Callback(HCD_HandleTypeDef *h) { USBH_LL_PortDisabled(h->pData); }
void HAL_HCD_HC_NotifyURBChange_Callback(HCD_HandleTypeDef *h, uint8_t chnum, HCD_URBStateTypeDef urb_state)
{
    (void)h; (void)chnum; (void)urb_state;
}

USBH_StatusTypeDef USBH_LL_Init(USBH_HandleTypeDef *phost)
{
    hhcd.Instance = USB_OTG_HS;
    hhcd.Init.Host_channels = 12;
    hhcd.Init.speed = HCD_SPEED_FULL;
    hhcd.Init.dma_enable = DISABLE;
    hhcd.Init.phy_itface = HCD_PHY_EMBEDDED;
    hhcd.Init.Sof_enable = DISABLE;
    hhcd.Init.low_power_enable = DISABLE;
    hhcd.Init.vbus_sensing_enable = DISABLE;
    hhcd.Init.use_external_vbus = DISABLE;
    hhcd.pData = phost;
    phost->pData = &hhcd;
    if (HAL_HCD_Init(&hhcd) != HAL_OK) {
        return USBH_FAIL;
    }
    USBH_LL_SetTimer(phost, HAL_HCD_GetCurrentFrame(&hhcd));
    return USBH_OK;
}

USBH_StatusTypeDef USBH_LL_DeInit(USBH_HandleTypeDef *phost)
{
    HAL_HCD_DeInit(phost->pData);
    return USBH_OK;
}

USBH_StatusTypeDef USBH_LL_Start(USBH_HandleTypeDef *phost)
{
    HAL_HCD_Start(phost->pData);
    return USBH_OK;
}

USBH_StatusTypeDef USBH_LL_Stop(USBH_HandleTypeDef *phost)
{
    HAL_HCD_Stop(phost->pData);
    return USBH_OK;
}

USBH_SpeedTypeDef USBH_LL_GetSpeed(USBH_HandleTypeDef *phost)
{
    switch (HAL_HCD_GetCurrentSpeed(phost->pData)) {
    case 0: return USBH_SPEED_HIGH;
    case 1: return USBH_SPEED_FULL;
    case 2: return USBH_SPEED_LOW;
    default: return USBH_SPEED_FULL;
    }
}

USBH_StatusTypeDef USBH_LL_ResetPort(USBH_HandleTypeDef *phost)
{
    HAL_HCD_ResetPort(phost->pData);
    return USBH_OK;
}

uint32_t USBH_LL_GetLastXferSize(USBH_HandleTypeDef *phost, uint8_t pipe)
{
    return HAL_HCD_HC_GetXferCount(phost->pData, pipe);
}

USBH_StatusTypeDef USBH_LL_OpenPipe(USBH_HandleTypeDef *phost, uint8_t pipe, uint8_t epnum, uint8_t dev_address,
                                    uint8_t speed, uint8_t ep_type, uint16_t mps)
{
    HAL_HCD_HC_Init(phost->pData, pipe, epnum, dev_address, speed, ep_type, mps);
    return USBH_OK;
}

USBH_StatusTypeDef USBH_LL_ClosePipe(USBH_HandleTypeDef *phost, uint8_t pipe)
{
    HAL_HCD_HC_Halt(phost->pData, pipe);
    return USBH_OK;
}

USBH_StatusTypeDef USBH_LL_SubmitURB(USBH_HandleTypeDef *phost, uint8_t pipe, uint8_t direction, uint8_t ep_type,
                                     uint8_t token, uint8_t *pbuff, uint16_t length, uint8_t do_ping)
{
    HAL_HCD_HC_SubmitRequest(phost->pData, pipe, direction, ep_type, token, pbuff, length, do_ping);
    return USBH_OK;
}

USBH_URBStateTypeDef USBH_LL_GetURBState(USBH_HandleTypeDef *phost, uint8_t pipe)
{
    return (USBH_URBStateTypeDef)HAL_HCD_HC_GetURBState(phost->pData, pipe);
}

/* The board's USB-A VBUS switch (if any) is not identified (PINMAP.md): assume always powered. */
USBH_StatusTypeDef USBH_LL_DriverVBUS(USBH_HandleTypeDef *phost, uint8_t state)
{
    (void)phost;
    (void)state;
    return USBH_OK;
}

USBH_StatusTypeDef USBH_LL_SetToggle(USBH_HandleTypeDef *phost, uint8_t pipe, uint8_t toggle)
{
    HCD_HandleTypeDef *h = phost->pData;
    if (h->hc[pipe].ep_is_in) {
        h->hc[pipe].toggle_in = toggle;
    } else {
        h->hc[pipe].toggle_out = toggle;
    }
    return USBH_OK;
}

uint8_t USBH_LL_GetToggle(USBH_HandleTypeDef *phost, uint8_t pipe)
{
    HCD_HandleTypeDef *h = phost->pData;
    return h->hc[pipe].ep_is_in ? h->hc[pipe].toggle_in : h->hc[pipe].toggle_out;
}

void USBH_Delay(uint32_t delay) { HAL_Delay(delay); }
