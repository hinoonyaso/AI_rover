# 035 — 자체 펌웨어(rrc_m4) 첫 flash: 부팅 직후 lockup, 이어서 0.8초마다 IWDG 리셋 (2026-10-10)

- 상태: **해결**(두 원인 모두 수정, 실기 확인)
- 관련: `firmware/rrc_m4/`(`app/src/system.c`, `app/inc/stm32f4xx_hal_conf.h`, `app/src/drv_lcd.c`), `firmware_source/PINMAP.md`
- 도구: J-Link OB 클론 + openocd(읽기 전용 레지스터/메모리 조회, breakpoint). 절차는 `firmware/rrc_m4/README.md` "SWD 디버거 첫날 순서"

## 증상 1 — 호스트 UART로 0바이트, 코어 lockup
`MOTOR_ENABLE=OFF` RRC 빌드를 flash(verify 통과)한 뒤 호스트 UART(USART3, 1 Mbaud)에서 바이트가 하나도 안 옴.
SWD로 보니 `clearing lockup after double fault`, CFSR `0x00020001`(INVSTATE+IACCVIOL), HardFault 벡터 fetch 후 PC `0x07fffffe` 등
매번 다른 이상한 주소. 클럭 설정 후(RCC SWS=PLL) USART3·PD8/PD9는 미초기화. **플래시를 디버거로 두 번 읽으면 서로 607바이트 달랐다**
(백업 때 vendor 펌웨어 상태에서는 두 번 읽기가 같았음). `reset halt`(HSI 16 MHz) 상태에서는 verify가 통과.

### 원인 — 크리스털 주파수 가정 오류(2배 오버클럭)
보드 크리스털은 **16 MHz**인데 펌웨어는 8 MHz로 가정(`HSE_VALUE 8000000`, PLL M=8 N=336 P=2) → 실제 SYSCLK **336 MHz**,
VCO 672 MHz(최대 432 MHz 초과). 플래시 대기 상태(5)로는 못 따라가 명령/데이터를 엉뚱하게 읽고 lockup.
근거(vendor 바이너리, `firmware_source/decompile/decompiled.c`): `HAL_RCC_GetSysClockFreq`가 PLL 입력을 `16000000`으로 계산
(HSE_VALUE==HSI_VALUE라 분기가 합쳐짐), `SystemClock_Config`가 M=8, N=168(0xa8), P=2, Q=7 → 16/8×168/2 = 168 MHz.
`PINMAP.md`의 "8 MHz 외부 크리스털"은 문서 기반 **추정**이었고 틀렸다(폐기).

### 해결
`HSE_VALUE 16000000`, PLL **M=8 N=168 P=2 Q=7**(vendor와 동일, VCO 입력 2 MHz, SYSCLK 168, USB 48 MHz).

## 증상 2 — 동작은 하지만 약 0.8초마다 IWDG 리셋
텔레메트리 프레임이 나오기 시작(CRC 정상)했지만 상태 프레임의 uptime이 101→201 ms에서 다시 101로, reset cause `0x24`(IWDG+PIN).
heartbeat 표(`g_watch`)를 멈추지 않고 읽어 보니 모든 heartbeat가 정상 증가하다 **부팅 후 약 275 ms에 감독 태스크까지 전부 정지**.
그 시점에 halt하면 PC는 `system_fatal`의 무한 루프, IPSR=14(PendSV). `system_fatal`에 breakpoint → 호출 경로
`PendSV_Handler → vTaskSwitchContext(taskCHECK_FOR_STACK_OVERFLOW) → vApplicationStackOverflowHook(t = lcd_slot)`.

### 원인 — LCD 태스크 스택 넘침
`drv_lcd_print()`가 글자 한 줄을 그리려고 `uint8_t buf[160*2*8]`(2,560 B)를 스택에 잡는데 lcd 태스크 스택이 640워드 = 2,560 B.
첫 화면 출력(약 275 ms) 때 넘쳐 FreeRTOS 검사(`configCHECK_FOR_STACK_OVERFLOW 2`)가 `system_fatal`로 보내고,
인터럽트가 꺼진 채 멈춰 감독 태스크가 IWDG를 못 먹여 500 ms 뒤 리셋.

### 해결
LCD 픽셀 버퍼 두 개(`g_line_buf` 320 B, `g_text_buf` 2,560 B)를 정적 메모리로 이동(LCD 드라이버는 lcd 태스크만 호출).
`sizeof(buf)` → `sizeof(g_text_buf)`로 함께 수정(포인터가 되면 4바이트만 보내게 되므로).

## 확인 (2026-10-10, 모터 스위치 OFF, 바퀴 띄움)
5초 수신: 20,892 B, CRC 오류 0. uptime 연속 증가(12.5 → 17.4 s). IMU(FUNC7) 50 Hz, WHEEL(0x21) 50 Hz, STATUS(0x20) 10 Hz,
배터리(FUNC0) 2 Hz **12.528 V**(vendor 펌웨어 12.55 V와 일치). 가속도 |a| ≈ 0.96 g. 자이로 정지 값을 base_node 축으로 바꾸면
(0.209, 0.172, −0.017) rad/s로 `base.yaml`의 기존 `gyro_bias`(0.197, 0.168, −0.017)와 일치 → 센서 고유 bias, 펌웨어 정상.
모터 fault 4개 모두 1(드라이버 fault 핀 PD3 High) — 모터 스위치 OFF(드라이버 무전원) 때문으로 **추정**, 스위치 ON에서 확인 필요.

## 추가 (같은 날) — 상태 화면이 안 바뀜: 화면 종류 자체가 달랐다
LED는 정상(호스트 LED 명령에만 깜빡이는 설계, PE10 토글 확인). 보드 화면은 vendor 시절 그림이 그대로 남아 있었고,
추정 제어 핀 PD11~14를 SWD로 하나씩 토글해도 무반응. vendor `oled_task`를 따라가 보니 **SSD1306 128×32 흑백 OLED,
I2C 0x3C, IMU와 같은 소프트웨어 I2C 버스(PB10/PB11)를 `oled_mutex`로 공유**(u8g2 ssd1306_128x32_univision).
`drv_lcd.c`를 SSD1306 I2C 드라이버로 교체하고, `drv_imu.c`에 버스 뮤텍스 + `drv_i2c_write_raw`를 추가(한 번에 1페이지씩 보내 IMU 대기 ≤ 약 5 ms).
결과: 4줄 표시(사용자 확인), IMU 49.6 Hz(전 50.2), CRC 오류 0, uptime 단조 증가.

## 재발 방지
- 하드웨어 상수(크리스털, 핀 극성)는 문서만 믿지 말고 vendor 바이너리와 교차 확인한다(`PINMAP.md`의 [B] 표시).
- 태스크 스택보다 큰 지역 배열을 두지 않는다. 브링업 때 `uxTaskGetStackHighWaterMark`로 여유를 기록할 것(체크리스트에 추가).
- 디버그 순서: UART 0바이트면 SWD로 fault 레지스터(CFSR/HFSR) → RCC/USART 상태 → `system_fatal` breakpoint로 호출 경로.
