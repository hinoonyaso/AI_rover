# rrc_m4 — STM32F407 RRC 보드 자체 펌웨어 (진행 중)

배경과 전체 계획: `~/.claude/plans/enchanted-chasing-sky.md`, 진행 상황: `checklist/PROJECT_CHECKLIST.md` 1번 섹션.
커넥터/센서/액추에이터가 뭐에 물려있는지는 `firmware_source/BOARD_CONNECTORS.md`.

## 지금 있는 것

`lib/protocol/` — RRC 프레임 코덱(`AA 55 FUNC LEN DATA CRC8-MAXIM`)과 FUNC 0~9 pack/unpack 헬퍼.
**타겟 하드웨어도, ARM 툴체인도 필요 없이 지금 바로 빌드·테스트된다** (순수 C, freestanding, 동적할당 없음).

```bash
cmake -S . -B build && cmake --build build
./build/lib/protocol/test_protocol   # ALL TESTS PASSED 가 나와야 함
```

골든 벡터 출처: PDF의 worked example(LED/PWM서보/버스서보)과, **이번 세션에 실제 로봇에 보내서
동작을 확인한 프레임**(부저 비프, 버스 서보 위치 읽기)을 그대로 하드코딩해서 회귀시험으로 남겼다.

Cortex-M4 타겟으로 프리스탠딩 컴파일도 확인함(2026-09-27):
```bash
export PATH="$PATH:/home/sang/.local/opt/stm32/bin"
arm-none-eabi-gcc -c -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16 \
  -ffreestanding -Iinclude src/rrc_protocol.c -o /tmp/rrc_protocol.o
```

## 아직 없는 것 (계획 순서대로)
- ARM 타겟 실제 링크(링커 스크립트, startup, CMSIS/HAL vendor) — CMakeLists.txt에 아직 cross target 없음
- 핀맵(정적 리버스엔지니어링 + ST-Link 도착 후 SWD 실측)
- 실제 펌웨어 본체(clock/task/드라이버) — 지금은 코덱 라이브러리만 있음
- 버스 서보(FUNC5) 부가 서브커맨드(전원 on/off, ID 변경, 전압/온도 한계·업로드): PDF 재확인 필요, `rrc_funcs.h` 파일 상단 주석 참고
- PWM 서보(FUNC4) deviation upload의 서브커맨드 바이트 값(0x05 vs 0x09): PDF 텍스트가 모호함, 실제 캡처로 재검증 필요 (`rrc_funcs.h`/`rrc_funcs.c` 주석 참고)

## 라이선스/출처
`lib/protocol`은 이 프로젝트에서 새로 작성한 코드다(리버스엔지니어링한 프로토콜 명세를 바탕으로 함, Hiwonder 코드를
복사한 게 아님). CMSIS/HAL을 vendor하게 되면(다음 단계) 그 출처(STMicroelectronics/STM32CubeF4, BSD-3-Clause)를 여기 추가로 기록한다.
