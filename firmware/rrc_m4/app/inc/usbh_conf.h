/* 한글: USB 호스트 라이브러리 설정(OTG_HS 코어, 내장 FS PHY, OS 포트 없음). */
/* USB host library configuration (OTG_HS core, embedded full-speed PHY on PB14/PB15). No OS port:
 * USBH_Process() is polled from the usb task. */
#ifndef USBH_CONF_H
#define USBH_CONF_H

#include <stdlib.h>
#include <string.h>

#include "stm32f4xx.h"
#include "stm32f4xx_hal.h"

#define USBH_MAX_NUM_ENDPOINTS 2U
#define USBH_MAX_NUM_INTERFACES 2U
#define USBH_MAX_NUM_CONFIGURATION 1U
#define USBH_KEEP_CFG_DESCRIPTOR 1U
#define USBH_MAX_NUM_SUPPORTED_CLASS 1U
#define USBH_MAX_SIZE_CONFIGURATION 0x100U
#define USBH_MAX_DATA_BUFFER 0x100U
#define USBH_DEBUG_LEVEL 0U
#define USBH_USE_OS 0U
#define USBH_IN_NAK_PROCESS 0

#define USBH_malloc malloc
#define USBH_free free
#define USBH_memset memset
#define USBH_memcpy memcpy

#define USBH_UsrLog(...) do {} while (0)
#define USBH_ErrLog(...) do {} while (0)
#define USBH_DbgLog(...) do {} while (0)

#endif
