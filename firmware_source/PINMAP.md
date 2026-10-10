# STM32F407VET6 (RRC 보드) 핀맵 — 정적 분석 + 공식 문서 교차검증

작성 2026-10-05. `BOARD_CONNECTORS.md`의 "아직 모르는 것" 항목을 채운다.
출처 3종을 교차한다:

- **[B]** 바이너리 정적 분석: `decompile/decompiled.c`의 GPIO/TIM/USART 초기화 (재현: `tools/firmware_re/extract_gpio.py`)
- **[D]** Hiwonder 공식 문서 저장소 `Hiwonder-docs/ROS-Robot-Control-Board` (커밋 07746775) `source/docs/1~3_*.md`
- **[실기]** 이 프로젝트에서 실제 로봇으로 확인한 것 (`AGENTS.md` 확정 사실)

표기: **확정** = 2개 이상 출처 일치 또는 실기 확인 / **추정** = 1개 출처 또는 구조적 추론 / **충돌** = 출처끼리 다름.
**flash 전에 "추정"은 SWD 실측 또는 단계별 브링업으로 확인한다**(`prd/rrc-microros-firmware-test-plan.md` 7번).

## 이번 분석으로 바로잡은 것
- 재구성 패키지(`reference/decompile_name_map.csv`)의 `MX_TIM8_Init`은 **TIM8이 아니라 TIM9**(`0x40014000`)다. TIM8(`0x40010400`)은 초기화되지 않는다.
- TIM9/10/11은 PWM 서보가 아니라 **모터 PWM 후반 4채널**이다(공식 하드웨어 문서 1.2.23: 모터 드라이버 YX-4055AM이 PE9, PE11, PE5, PE6, PE13, PE14, PB8, PB9로 구동). PWM 서보는 **TIM13 소프트웨어 PWM(GPIO)**(문서 3.6.5).
- 호스트 링크는 UART2가 아니라 **USART3(PD8/PD9) 1,000,000 baud** [B][D 3.16.6]. 보드 라벨 "USB serial port 2"가 이쪽이다(라벨의 숫자와 MCU의 USART 번호는 다르다). ISP/다운로드 포트 = USART1(PA9/PA10, 115200) [B].
- 부저는 문서 간 **충돌**: 하드웨어 문서 1.2.17은 PA4, 프로그램 분석 3.3.5와 바이너리는 PA8. 바이너리의 PA8만 푸시풀 출력으로 초기화됨(PA4는 아날로그) → **PA8 채택**.
- IMU는 **MPU6050**(하드웨어 문서 1.1.1/1.2.13) 이지만 프로그램 분석 3.5는 QMI8658이라고 쓴다 → 펌웨어는 **둘 다 자동 판별**한다.

## 통신
| 기능 | 핀 / 페리페럴 | 설정 | 상태 |
|---|---|---|---|
| 호스트(CH9102, "USB serial port 2") | USART3 PD8(TX)/PD9(RX) AF7 | 1,000,000 baud 8N1 | **확정** [B][D][실기] |
| ISP/다운로드(CH9102, "USB serial port 1") | USART1 PA9/PA10 AF7 | 115200 (ISP는 8E1) | **확정** [B][실기] |
| 블루투스 모듈 | USART2 PD5(TX)/PD6(RX) AF7 | 9600 | **확정** [B][D] |
| SBUS 수신기 | UART5 PC12(TX)/PD2(RX) AF8 | 100000 baud, 9bit 짝수 패리티, 2 정지(하드웨어 인버터) | **확정** [B][D] (PC12는 사용 안 함) |
| 버스 서보 | USART6 PC6(TX)/PC7(RX) AF8 + 방향 제어 PE7, PE8 | 115200 반이중 | 포트·baud **확정** [B][D](문서는 "PG6_TX"로 오기, 100핀 칩에 GPIOG 없음→PC6) / **PE7·PE8 역할과 극성은 추정**(초기값 둘 다 High, 버퍼 /OE 활성-Low 가정; 첫 전송이 실패하면 4가지 조합 자동 시도) |
| USB HOST(게임패드 동글) | OTG_HS 코어의 내장 FS PHY, PB14(DM)/PB15(DP) AF12 | 12 Mbit/s 호스트 | PB14/15 AF12 **확정** [B][D]. VBUS 전원 스위치 핀은 **미확인** |

## 모터 / 엔코더
모터 드라이버: YX-4055AM. 모터 1개당 PWM 2줄(정/역), 주파수 200 Hz (TIM PSC=839, ARR=999 → 168 MHz/840/1000) [B]. 출력 범위 ±1000 = 듀티 0~100%.
| 모터 | PWM 쌍(역방향 / **정방향**) | 엔코더 | 상태 |
|---|---|---|---|
| 1 (왼앞) | PE13 TIM1_CH3 / **PE14 TIM1_CH4** | TIM5 PA0(CH1)/PA1(CH2) AF2 | **확정** [D 3.9.5, 3.11.5 "PE13, PE14 = Motor1 구동, PA0/PA1 = Motor1 엔코더"] [B] |
| 2 (왼뒤) | PE9 TIM1_CH1 / **PE11 TIM1_CH2** | TIM2 PA15(CH1)/PB3(CH2) AF1 | 엔코더 **확정**(문서 "M2=TIM2" + [B]). PWM 쌍 배정은 **추정**(남은 핀을 모터 번호 순으로 배정, 쌍 안에서 "뒤쪽 핀=정방향"은 모터1 규칙을 일반화) |
| 3 (오른앞) | PE5 TIM9_CH1 / **PE6 TIM9_CH2** | TIM4 PB6/PB7 AF2 | 엔코더 **확정**. PWM **추정** |
| 4 (오른뒤) | PB8 TIM10_CH1 / **PB9 TIM11_CH1** | TIM3 PB4/PB5 AF2 | 엔코더 **확정**. PWM **추정** |
- 엔코더: 인코더 모드 TI12, ARR=60000(오버플로 ISR이 `overflow_num` 증감), 필터 0 [B]. 모터 번호↔타이머는 바이너리의 TIM7 ISR 호출 순서로 재확인 [B]: M1=TIM5, M2=TIM2, M3=TIM4, M4=TIM3.
- 제어 주기: TIM7 PSC=83, ARR=9999 → 10 ms (APB1 타이머 84 MHz) [B]. (문서 예제는 TIM6, 바이너리는 TIM7.)
- **PD3 = 모터 드라이버 fault 입력**(High면 출력 0, PID 정지) [B: `FUN_0800befc`가 PD3을 읽음]. 극성 **High = fault 확정**(2026-10-10 실기: 자체 펌웨어에서 모터 스위치 OFF → High(fault), ON → Low). 스위치 OFF(드라이버 무전원)도 fault로 읽힌다.
- 데드존 ±250, 클램프 ±1000, 속도 필터 0.9/0.1, PID 증분형 [D 3.11][B].
- **엔코더 부호(양의 PWM → 카운트 증가?)는 모터별로 미확인** → 펌웨어의 runaway 래치가 잡고, `ENCODER_SIGN[]`을 보드 설정에 둔다.
- `ticks_per_circle`/PID 게인/속도 상한은 공식 문서에 숫자가 없다(Hiwonder `encoder_motor.h` 상수는 문서에 미수록): JGB520 예제값(1320, 63/2.6/2.4)을 **추정 기본값**으로 쓰고 브링업에서 단계응답으로 튜닝한다.

## 센서
| 기능 | 핀 | 상태 |
|---|---|---|
| IMU I2C (소프트웨어 비트뱅잉) | SCL=PB10, SDA=PB11 (오픈드레인, 외부 10k 풀업) | **확정** [D 1.2.13/3.5.5] [B: PB10/PB11 GPIO 토글 함수군 `0x08005870~0x08005d30`] |
| IMU 데이터 준비 인터럽트 | PB12 EXTI (falling) | **확정** [D 3.5.5] [B: PB12 IT_FALLING] |
| IMU 출력율 | 약 111 Hz = 1 kHz/(1+8) | **확정** [실기 111 Hz] → MPU6050 SMPLRT_DIV=8, DLPF on |
| IMU 칩→보드 축 변환 | FUNC7 축: X=오른쪽, Y=뒤, Z=아래 [실기] | **미확인**: 칩 자체의 축 방향은 모른다. 기본값 항등 + `tools/imu_calibration/check_axes.py`로 확인 후 `IMU_AXIS_MAP`을 고친다 |
| 배터리 | ADC1: PB0(IN8) + 내부 Vrefint(IN17), DMA, 50 ms마다. mV = 1210/adc[0]·adc[1]·11, 필터 0.95/0.05, 20 V 초과 거부 | **확정** [D 3.4.6] [B: PB0 아날로그, ADC1 사용] [실기: FUNC0 mV] |
| 버튼 K1/K2 | PE0, PE1 입력(외부 풀업, 누르면 Low) | **확정** [D 1.2.6/3.3.5] [B: PE0/PE1 입력]. K1/K2와 PE0/PE1의 대응(어느 쪽이 button_id 1)은 **추정**: id1=PE0, id2=PE1 |

## 출력
| 기능 | 핀 | 상태 |
|---|---|---|
| 사용자 LED | PE10 (Low = 점등) | **확정** [D 1.2.4 "PE10 low output → LED on"] [B: PE10 출력, 초기 Low] |
| 부저 | PA8 (High = 울림, S8050 트랜지스터, 능동 부저 가정이라 주파수는 무시) | PA8 **확정**(바이너리+프로그램 문서) / 능동·수동 여부 **미확인** (FUNC2의 freq는 현재 무시) |
| PWM 서보 4채널 | PC8, PC9, PA11, PA12 GPIO 소프트웨어 PWM(TIM13, 20 ms 프레임) | **추정**: 바이너리에서 출력으로 초기화되는데 다른 용도가 설명되지 않는 4핀이고 [D 3.6.5]가 "GPIO write_pin + TIM13"이라고 함. 서보 번호↔핀 순서는 **추정**. 안전을 위해 **첫 서보 명령 전까지 펄스를 내보내지 않는다** |
| LCD(ST7735 80×160, SPI2) | SCK=PB13 AF5, MOSI=PC3 AF5, RES=PD14, DC=PD13, CS=PD12, BLK=PD11 | SPI 핀 **확정** [B][D 1.2.7]. 제어 핀 4개 배정은 **추정**: 문서 1.2.7의 나열 순서(PD14, PD13, PD12, PD11)가 커넥터 순서(RES, DC, CS, BLK)와 일치하고 바이너리의 초기값(PD11/12/14=High, PD13=Low)이 RES=1, DC=0, CS=1, BLK=1로 설명됨 |
| 모터 enable 스위치 | 하드웨어 스위치(모터 전원 차단), MCU 핀 없음 | [D 1.1.1] |

## 부팅 시 GPIO 출력 초기 상태(바이너리 `MX_GPIO_Init` 그대로 복제, 유휴 안전)
PE7=1, PE8=1, PE10=0, PB10=0, PB11=0, PD11=1, PD12=1, PD13=0, PD14=1, PC8=1, PC9=0, PA8=0, PA11=0, PA12=0.
(PC8=1은 의도가 불명하다. 서보 핀이라면 부팅 직후 1회 펄스 위험이 있어 **PC8은 서보 사용 시작 전까지 바이너리와 같은 High 유지**가 아니라 Low로 바꾸는 쪽이 안전해 보이지만, 바이너리 동작을 바꾸는 것이므로 임의로 바꾸지 않고 기본은 바이너리 그대로 둔다 — 시험 항목 참고.)

## 인터럽트 우선순위(바이너리 main에서 확인된 IRQ, 모두 우선순위 5 = FreeRTOS 호환)
DMA1 stream 0/1/3/4/5/6, TIM2/3/4/5, TIM7, TIM13(IRQ 44), USART2/3, EXTI15_10(IRQ 40), UART5(IRQ 53), USART6(IRQ 71), OTG_HS(IRQ 77).

## 시스템
- 클럭: **16 MHz 외부 크리스털**(2026-10-10 **확정** [B]: vendor `HAL_RCC_GetSysClockFreq`가 16000000 사용, SystemClock_Config M=8 N=168 P=2 Q=7. 이전의 "8 MHz"는 추정이었고 **폐기** — 이 값으로 자체 펌웨어가 336 MHz로 오버클럭돼 lockup, troubleshooting/035), HCLK 168 MHz, APB1 타이머 84 MHz, APB2 타이머 168 MHz [D 1.1.1 "168MHz", 3.9 "TIM6 APB1 84MHz"].
- RTOS: CMSIS-RTOS(FreeRTOS), 태스크 9개: default/oled/bluetooth/gui/app/imu/sbus_rx/packet_rx/packet_tx [B 문자열].
- IWDG: 바이너리에서 prescaler=3(÷32?), reload=0x13 → 약 20 ms로 매우 짧고 `app_task`만 먹임 (`troubleshooting/001`). 새 펌웨어는 태스크별 heartbeat를 모두 확인하는 감시 태스크가 먹인다.
