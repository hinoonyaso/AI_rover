/* 한글: USB 호스트 게임패드: ST 기본 HID 클래스는 게임패드를 거부("Protocol not supported")하므로 자체 최소 클래스를 쓴다. 원시 리포트는 FUNC 0x23으로도 올려 레이아웃 확정에 쓴다. */
/* USB HOST gamepad: minimal HID-class driver on the ST host core (the stock HID class rejects
 * gamepads, "Protocol not supported"; the vendor firmware patched it, we use our own class).
 * Reports are decoded with core/gamepad.c's table-driven layout (UNVERIFIED default) and also
 * forwarded raw on FUNC 0x23 until the layout is confirmed. */
#include <string.h>

#include "FreeRTOS.h"
#include "app.h"
#include "task.h"
#include "usb_gamepad.h"
#include "usbh_core.h"

#define HID_CLASS 0x03

typedef enum { GP_INIT, GP_GET_DATA, GP_POLL, GP_ERROR } gp_state_t;

typedef struct {
    uint8_t pipe_in;
    uint8_t ep_addr;
    uint16_t length;
    uint8_t poll;
    uint16_t timer;
    gp_state_t state;
    uint8_t report[64];
} gp_handle_t;

static USBH_HandleTypeDef g_host;
static gp_handle_t *g_gp;
static volatile uint8_t g_connected;
static usb_gamepad_report_cb_t g_cb;

/* 한글: 첫 HID 인터페이스의 인터럽트 IN 엔드포인트를 열어 리포트를 받는다. */
static USBH_StatusTypeDef gp_init(USBH_HandleTypeDef *phost)
{
    const uint8_t itf = USBH_FindInterface(phost, HID_CLASS, 0xFFU, 0xFFU);
    if (itf == 0xFFU || itf >= USBH_MAX_NUM_INTERFACES) {
        return USBH_FAIL;
    }
    if (USBH_SelectInterface(phost, itf) != USBH_OK) {
        return USBH_FAIL;
    }
    gp_handle_t *h = USBH_malloc(sizeof(*h));
    if (!h) {
        return USBH_FAIL;
    }
    memset(h, 0, sizeof(*h));
    phost->pActiveClassData = h;
    g_gp = h;

    const USBH_InterfaceDescTypeDef *d = &phost->device.CfgDesc.Itf_Desc[itf];
    int found = 0;
    for (uint8_t i = 0; i < d->bNumEndpoints && i < USBH_MAX_NUM_ENDPOINTS; i++) {
        if (d->Ep_Desc[i].bEndpointAddress & 0x80U) { /* first interrupt IN endpoint */
            h->ep_addr = d->Ep_Desc[i].bEndpointAddress;
            h->length = d->Ep_Desc[i].wMaxPacketSize;
            h->poll = d->Ep_Desc[i].bInterval < 8 ? 8 : d->Ep_Desc[i].bInterval;
            found = 1;
            break;
        }
    }
    if (!found) {
        return USBH_FAIL;
    }
    if (h->length > sizeof(h->report)) {
        h->length = sizeof(h->report);
    }
    h->pipe_in = USBH_AllocPipe(phost, h->ep_addr);
    USBH_OpenPipe(phost, h->pipe_in, h->ep_addr, phost->device.address, phost->device.speed, USB_EP_TYPE_INTR,
                  h->length);
    USBH_LL_SetToggle(phost, h->pipe_in, 0U);
    h->state = GP_GET_DATA;
    g_connected = 1;
    return USBH_OK;
}

static USBH_StatusTypeDef gp_deinit(USBH_HandleTypeDef *phost)
{
    gp_handle_t *h = phost->pActiveClassData;
    if (h) {
        if (h->pipe_in) {
            USBH_ClosePipe(phost, h->pipe_in);
            USBH_FreePipe(phost, h->pipe_in);
        }
        USBH_free(h);
        phost->pActiveClassData = NULL;
        g_gp = NULL;
    }
    g_connected = 0;
    return USBH_OK;
}

static USBH_StatusTypeDef gp_request(USBH_HandleTypeDef *phost)
{
    (void)phost; /* no SET_IDLE / report-descriptor parsing: the receiver streams on its interrupt pipe */
    return USBH_OK;
}

static USBH_StatusTypeDef gp_process(USBH_HandleTypeDef *phost)
{
    gp_handle_t *h = phost->pActiveClassData;

    switch (h->state) {
    case GP_GET_DATA:
        USBH_InterruptReceiveData(phost, h->report, (uint8_t)h->length, h->pipe_in);
        h->state = GP_POLL;
        h->timer = (uint16_t)phost->Timer;
        break;
    case GP_POLL:
        if (USBH_LL_GetURBState(phost, h->pipe_in) == USBH_URB_DONE) {
            const uint32_t n = USBH_LL_GetLastXferSize(phost, h->pipe_in);
            if (n && g_cb) {
                g_cb(h->report, n);
            }
            h->state = GP_GET_DATA;
        } else if (USBH_LL_GetURBState(phost, h->pipe_in) == USBH_URB_STALL) {
            if (USBH_ClrFeature(phost, h->ep_addr) == USBH_OK) {
                h->state = GP_GET_DATA;
            }
        } else if ((uint32_t)((uint16_t)phost->Timer - h->timer) > 2U * h->poll) {
            h->state = GP_GET_DATA; /* NAK (no new data): re-arm */
        }
        break;
    default:
        break;
    }
    return USBH_OK;
}

static USBH_StatusTypeDef gp_sof(USBH_HandleTypeDef *phost)
{
    (void)phost;
    return USBH_OK;
}

static USBH_ClassTypeDef g_class = {"GAMEPAD", HID_CLASS, gp_init, gp_deinit, gp_request, gp_process, gp_sof, NULL};

static void host_event(USBH_HandleTypeDef *phost, uint8_t id)
{
    (void)phost;
    if (id == HOST_USER_DISCONNECTION) {
        g_connected = 0;
    }
}

void usb_gamepad_task(void *arg)
{
    (void)arg;
    vTaskDelay(pdMS_TO_TICKS(500)); /* let the rest of the system come up first */
    if (USBH_Init(&g_host, host_event, 0) == USBH_OK) {
        USBH_RegisterClass(&g_host, &g_class);
        USBH_Start(&g_host);
    }
    for (;;) {
        USBH_Process(&g_host);
        vTaskDelay(pdMS_TO_TICKS(1));
    }
}

void usb_gamepad_set_cb(usb_gamepad_report_cb_t cb) { g_cb = cb; }
int usb_gamepad_connected(void) { return g_connected; }
