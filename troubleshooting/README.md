# 트러블슈팅 기록

**오류나 예상 밖의 동작이 생길 때마다** 이 폴더에 파일 하나를 추가한다. 해결이 안 됐어도 적는다(상태만 `미해결`).
파일명은 `NNN-짧은-제목.md`(번호는 이어서), 아래 목록에도 한 줄 추가한다.

## 작성 형식
```
# 제목
- 날짜: YYYY-MM-DD
- 상태: 해결 / 우회 / 미해결
- 관련: 파일, 명령, 로그

## 증상
(무엇이 어떻게 보였나. 로그 원문은 짧게 인용)

## 원인
(확인된 원인. 추정이면 "추정"이라고 쓰고 근거를 적는다)

## 해결 또는 우회
(실제로 한 조치와 결과)

## 확인/재발 방지
(같은 문제인지 알아보는 방법, 다시 안 생기게 한 것)
```

## 목록

| # | 제목 | 상태 |
|---|---|---|
| 001 | [STM32 펌웨어 hang](001-stm32-firmware-hang.md) | 미해결 |
| 002 | [base_node가 `open : No such file`로 시리얼을 못 엶](002-base-node-empty-port.md) | 해결 |
| 003 | [teleop으로 조종하면 0.5초 만에 멈춤](003-teleop-stops-after-half-second.md) | 우회 |
| 004 | [시험 후 노드가 남아 포트/파이프를 점유](004-leftover-processes.md) | 해결 |
| 005 | [`src/` 안에 build/install/log 생성](005-colcon-build-inside-src.md) | 미정리 |
| 006 | [손으로 90° 돌렸는데 yaw가 절반만 나옴](006-hand-rotation-half-yaw.md) | 해결(측정법) |
| 007 | [펌웨어 ZIP에 소스가 없고 .hex뿐](007-firmware-zip-hex-only.md) | 정보 |
| 008 | [재부팅하면 /tmp의 시험 스크립트가 사라짐](008-tmp-wiped-on-reboot.md) | 해결 |
| 009 | [rclpy Twist에 정수를 넣으면 assertion으로 죽음](009-rclpy-int-vs-float.md) | 해결 |
| 010 | [옆 이동이 1.45배로 보였음 (눈대중 측정 오차)](010-mecanum-strafe-scale.md) | 해결(가설 폐기) |
| 011 | [robot_state_publisher에 URDF를 `-p`로 넘기면 죽고 시험은 exit=0](011-rsp-urdf-cli-param.md) | 해결 |
| 012 | [CH340이 있는데 `/dev/ttyUSB*`가 없음 (`ch341` 모듈 없음)](012-ch341-module-missing.md) | 해결 |
| 013 | [Orbbec DaBai DCW: depth 센서 시리얼 없음 → SDK v2 열거 실패](013-orbbec-sdk-v2-no-serial-bug.md) | 해결 (SDK v1 소스 빌드) |
| 014 | [colcon build -j6 + 스왑 0B로 SSH가 끊기고 시스템이 멈춤](014-oom-during-build.md) | 해결 (스왑 4G 추가 + -j2) |
