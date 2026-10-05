/* 한글: DMA UART: IDLE 라인 수신→스트림 버퍼, 스트림 버퍼→DMA 송신. 호스트(USART3)/보조(USART1)/블루투스(USART2)에 사용. */
/* DMA UARTs with IDLE-line reception into a FreeRTOS stream buffer and DMA transmission from a
 * stream buffer. One instance per port; used for the host link (USART3), aux/RRC-debug (USART1),
 * Bluetooth (USART2). */
#ifndef DRV_UART_H
#define DRV_UART_H

#include <stddef.h>
#include <stdint.h>
#include "FreeRTOS.h"
#include "stream_buffer.h"

typedef enum { UART_PORT_HOST = 0, UART_PORT_AUX, UART_PORT_BT, UART_PORT_COUNT } uart_port_id_t;

void drv_uart_init(uart_port_id_t id, uint32_t baud);
/* Blocking-free enqueue (drops if the TX buffer is full). Returns bytes accepted. */
size_t drv_uart_write(uart_port_id_t id, const uint8_t *data, size_t len);
/* Waits up to `ticks` for received bytes. */
size_t drv_uart_read(uart_port_id_t id, uint8_t *buf, size_t max, TickType_t ticks);
/* TX pump: call from the owning TX task / low-priority loop; returns after the current DMA completes. */
void drv_uart_tx_poll(uart_port_id_t id);
/* Polling transmit for low-rate ports (Bluetooth). */
void drv_uart_send_blocking(uart_port_id_t id, const uint8_t *data, size_t len);
StreamBufferHandle_t drv_uart_tx_buffer(uart_port_id_t id);
uint32_t drv_uart_dropped(uart_port_id_t id);
/* Raw access for transports that manage their own buffers (micro-ROS). */
void drv_uart_flush_rx(uart_port_id_t id);

#endif
