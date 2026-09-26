# RosRobotControllerM4.zip에 소스가 없고 .hex뿐
- 날짜: 2026-09-20
- 상태: 정보 (소스는 아직 못 구함)
- 관련: `firmware_source/RosRobotControllerM4.zip`, `tools/stm32_diagnostics/analyze_firmware.py`

## 증상
Hiwonder 문서에서 받은 STM32 "소스" ZIP(79 KB)의 내용이 `RosRobotControllerM4.hex` 하나(2025-06-18, 컴파일된 펌웨어)였다.
JetRover GitHub 저장소(3개 브랜치)와 ROSOrin-Pro 저장소에도 소스는 없고, ROSOrin-Pro에는 다른 로봇용 `.hex`만 있다.

## 원인
공개 자료가 공장 출력 펌웨어만 제공한다 (Hiwonder 위키 부록에 "Firmware = .hex"로 나온다).

## 해결 또는 우회
`.hex`를 정적 분석했다 (`analyze_firmware.py`): IWDG 설정, `HAL_IWDG_Refresh` 호출 위치, 태스크 스택/우선순위를 확인했다.
소스가 필요한 분석(데드락 지점 특정)은 하지 못했다.

## 확인/재발 방지
- **원본 펌웨어를 백업하기 전에는 어떤 펌웨어도 로봇에 쓰지 않는다.** 다른 로봇(ROSOrin)의 `.hex`는 올리지 않는다.
- 소스는 Hiwonder 지원에 요청하거나 SWD(ST-Link) 디버깅으로 대신한다.
