# ROS Robot Control Board — 커넥터/센서/액추에이터 연결 정리

출처: (1) 사용자가 공유한 Hiwonder 제품 이미지의 보드 라벨(항목 ⑦ "ROS Robot Control Board",
항목 ⑥ "USB HUB"), (2) 이 프로젝트에서 실제 로봇에 raw RRC 프로토콜로 시험해서 확인한 내용
(2026-09-27, `tools/stm32_diagnostics/rrc_raw.py` 및 관련 스크립트).
**핀 번호(PAx/PBx 등)나 내부 배선은 여전히 모른다** — 스키매틱이 없어서 라벨과 프로토콜 동작으로만
무엇이 어디에 물려 있는지 대응시킨 것이다. GPIO 레벨 확정은 `~/.claude/plans/enchanted-chasing-sky.md`의
Phase A/B(정적 리버스엔지니어링 + ST-Link/SWD 실측)에서 한다.

메인 칩: **STM32F407VET6** (100핀, LQFP), 부트로더 버전 0x31, PID `0x0413` (2026-09-27 UART1로 직접 확인).

## 커넥터별 대응표

| 보드 라벨 | 실제로 뭐가 물려있나 | 프로토콜/확인 상태 |
|---|---|---|
| USB serial port 2 (Type-C) | Jetson ↔ STM32 호스트 통신 (CH9102 USB-UART) | **확정**: `/dev/serial/by-id/usb-1a86_USB_Single_Serial_596F003889-if00` = `/dev/ttyACM0`, UART2, 1,000,000 baud, RRC 프레임(AA55 FUNC LEN DATA CRC) |
| USB serial port 1/flashing download (Type-C) | Jetson ↔ STM32 ISP(펌웨어 다운로드) | **확정**: `/dev/ttyACM1`, ROM 부트로더(AN3155), 115200 8E1, DTR=NRST/RTS=BOOT0 조합으로 진입(`DTR=0&RTS=1`). 진입 시 앱 정지, RST 버튼으로만 정상 복귀됨(소프트웨어 리셋 안 됨, `troubleshooting/001`) |
| MPU6050 IMU (보드 라벨에 명시) | 온보드 IMU 칩, STM32 내부 버스(추정: I2C)로 직결 | **확정(칩 정체)**: FUNC7, 6×float32(accel g / gyro deg/s), 약 111 Hz. 원시축 X=오른쪽,Y=뒤,Z=아래. I2C 핀 번호는 미확인 |
| Power interface | 배터리팩 커넥터 | **확정**: FUNC0 응답(`04`+u16LE mV). 오늘 완충 12.5 V 확인. ADC 채널/분압비는 미확인 |
| Buzzer (보드 라벨) | 온보드 부저, GPIO/타이머로 직결 | **확정**: FUNC2 (freq u16, on_ms u16, off_ms u16, cycles u16, 전부 LE). 2026-09-27 실제 소리로 확인 |
| 0.96-inch LCD display interface (8-pin SPI, "색상 화면") | 외부 소형 디스플레이 모듈(흔히 OLED라고 부르는 것) | **확정(동작)**: 3번째 줄에 배터리 mV 표시. **호스트에서 제어하는 FUNC가 프로토콜에 없음** — 펌웨어가 자체적으로만 그림/문자를 그린다(추정). 컨트롤러 칩 정체·SPI 핀은 미확인 |
| Bus servo interface (1채널, half-duplex UART로 데이지체인) | 로봇팔 6개 서보 | **확정(2026-09-27)**: FUNC5, subcommand 0x01(이동)/0x05(위치 읽기). **ID 1~5 = 팔 관절**(pulse 0~1000 ↔ 0~240°), **ID 10 = 그리퍼**. ID 0,6~9,11~15 무응답 |
| Battery voltage powered PWM servo interface / 5V power supply PWM servo interface (합쳐서 4채널) | PWM(아날로그) 서보 4개 슬롯 | **시험함, 응답은 하지만 미사용으로 보임**: FUNC4, subcommand 0x03(단일 이동)/0x05(위치 읽기), pulse 500~2500 ↔ 0~180°. 채널 1~4 전부 읽으면 1500(중앙) 응답하고 명령도 받아들이지만, **실제로 움직여도 육안으로 아무 변화 없음** → 지금 이 로봇엔 이 커넥터에 아무것도 안 꽂혀 있거나 팔과 무관한 용도로 보임(추정) |
| 4-ch encoded motor interface ×2 (보드에 라벨이 두 번 나옴) | 메카넘 휠 4개(엔코더 내장 모터) | **확정**: FUNC3, `01,N,N×(id0based u8, rps f32LE)`. ID 0 왼앞·1 왼뒤·2 오른앞·3 오른뒤(오른쪽 부호반전). **엔코더 신호 자체는 모터에 있지만 호스트로 안 옴**(프로토콜에 업로드 FUNC 없음, 재플래시 후에도 동일) |
| USB HOST interface ("무선 컨트롤러, 마우스 등 연결") | 2.4G 무선 게임패드 동글 | **확정(추정 경로)**: STM32가 이 포트로 동글을 직접 물고(USB host), 디코드해서 **FUNC8로 UART2에 실어 Jetson에 보낸다** (`buttons u16, hat u8, lx/ly/rx/ry i8`, 7바이트). Jetson 쪽에서 별도 USB 장치로는 안 보인다 — `tools/stm32_diagnostics/NOTES.md`에 있던 "두 번째 CH340 = 게임패드 동글" 기록은 **이것과는 다른, Jetson에 직접 꽂힌 별개의 동글**이었던 것으로 정리한다 |
| SBUS remote control receiver interface | SBUS 수신기(RC 조종기용) | **라벨만 확인, 미시험**. 프로토콜상 FUNC9: `int16[16]` 채널 + ch17/ch18/signal_loss/fail_safe(각 u8), 36바이트. 이 로봇에 수신기가 꽂혀 있는지는 확인 안 함 |
| Bluetooth module interface (TTL) | 블루투스 모듈 슬롯 | **라벨만 확인, 미시험**. `bluetooth_task`가 바이너리에 존재(이전 정적분석), 프로토콜 문서엔 별도 FUNC 없음 — TTL 패스스루로 추정 |
| I2C expansion interface (4핀) | 사용자 확장용 I2C | **라벨만 확인, 미사용/미시험** |
| Custom button | 보드 위 물리 버튼 | **라벨만 확인, 미시험**. FUNC6: `button_id u8, event u8`(PRESSED/LONGPRESS/CLICK/DOUBLE_CLICK) |
| Reset button | **이번 세션 내내 눌러온 그 RST 버튼** | **확정, 매우 많이 검증함**: hang 상태에서도 물리적으로 눌러야만 복구됨(소프트웨어 DTR/RTS 리셋은 5회 이상 시도 전부 실패, `troubleshooting/001`) |
| GPIO expansion and SWD debugging | SWD 헤더(SWDIO/SWCLK 등) | **라벨만 확인, 아직 안 씀**. ST-Link 도착 후 Phase B에서 사용 예정 |
| Motor control switch / Power switch / On-board power indicator / User indicator light | 보드 자체 스위치·LED | 라벨만 확인. User indicator light는 향후 신규 펌웨어 Hello World(LED 깜빡임) 타겟 후보 |
| (액세서리 보드) USB HUB | Jetson USB 포트 부족 보완, 1→4포트, 외부 9-24V 전원 | 카메라/LiDAR 등이 이 허브를 거쳐 Jetson에 연결되는 것으로 추정(개별 포트 확인은 안 함) |

## 아직 모르는 것 (Phase A/B에서 확정 예정)
- 위 커넥터들의 실제 STM32 핀 번호(PAx/PBx), 사용 페리페럴(TIMx/I2Cx/USARTx/ADCx)
- 배터리 ADC 채널과 분압비(mV 스케일 보정 값)
- OLED/LCD 컨트롤러 칩 정체, SPI 핀
- PWM 서보 4채널이 실제로 이 로봇에 연결이 안 된 것인지, 다른 이유로 안 움직이는지
