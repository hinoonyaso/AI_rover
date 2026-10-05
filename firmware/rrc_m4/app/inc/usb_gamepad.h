/* 한글: USB 호스트 게임패드 태스크/콜백 인터페이스. */
#ifndef USB_GAMEPAD_H
#define USB_GAMEPAD_H

#include <stddef.h>
#include <stdint.h>

typedef void (*usb_gamepad_report_cb_t)(const uint8_t *report, size_t len);

/* FreeRTOS task body (polls the USB host stack). */
void usb_gamepad_task(void *arg);
void usb_gamepad_set_cb(usb_gamepad_report_cb_t cb);
int usb_gamepad_connected(void);

#endif
