# 025 — 디컴파일 재구성 패키지의 함수/핀 이름 오류 (해결, 2026-10-05)

## 증상
`JetRover_Hiwonder_Official_Pack`의 `decompile_name_map.csv`가 `MX_TIM8_Init`을 "TIM8 base 0x40014000"이라 적었고, 재구성 README는 Motor2~4 PWM 매핑을 "알 수 없음"으로 남겼다. 부저 핀은 하드웨어 문서(PA4)와 프로그램 분석 문서(PA8)가 서로 달랐다.

## 원인과 정정
- `0x40014000`은 TIM8이 아니라 **TIM9**다. TIM8(`0x40010400`)은 초기화되지 않는다. TIM9/10/11은 PWM 서보가 아니라 **모터 PWM 후반 4채널**(공식 하드웨어 문서 1.2.23: PE9, PE11, PE5, PE6, PE13, PE14, PB8, PB9).
- 부저는 바이너리에서 PA8만 푸시풀 출력이고 PA4는 아날로그 → **PA8**.
- 호스트 링크는 USART3(PD8/PD9, 1 Mbaud). 보드 라벨의 "serial port 2"와 MCU의 USART 번호는 다르다.
상세와 신뢰 수준: `firmware_source/PINMAP.md`.

## 확인
`python3 tools/firmware_re/extract_gpio.py`로 GPIO 초기화 호출을 다시 뽑을 수 있다.
