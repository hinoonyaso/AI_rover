# CH340 시리얼 변환기가 있는데 `/dev/ttyUSB*`가 없음 (`ch341` 커널 모듈 없음)
- 날짜: 2026-09-20
- 상태: 해결 (모듈 설치, 재부팅 후 자동 로드 확인)
- 관련: `lsusb`의 `1a86:7523` 2개 (`1-2.1.1.1`, `1-2.1.4`), 커널 `6.8.12-1021-tegra`

## 증상
`lsusb`에 CH340 시리얼 변환기(`1a86:7523`)가 2개 보이지만 `lsusb -t`에서 `Driver=[none]`이고 `/dev/ttyUSB*`가 없다.
ROS 쪽에도 LiDAR 드라이버 패키지가 없다.

## 원인
`modinfo ch341`이 `Module ch341 not found`를 반환한다. 이 Tegra 커널에는 `cp210x`, `ftdi_sio`는 있으나 `ch341`이 없다.
`linux-modules-extra-6.8.12-1021-tegra` 패키지도 apt에서 찾지 못했다 (다른 버전만 존재).
(추정: 어느 CH340에 LiDAR가 붙어 있는지, 두 번째 CH340이 무엇인지는 드라이버가 없어 확인하지 못했다.)

## 해결 또는 우회
커널 설정 `# CONFIG_USB_SERIAL_CH341 is not set`이 원인이다. mainline v6.8의 `ch341.c`를 커널 헤더로 out-of-tree 빌드했고
(`drivers/ch341/`, vermagic 일치, CH340 `1a86:7523` alias 포함) `sudo ./install.sh`로 설치한다. 커널 업데이트 시 재빌드가 필요하다.
LiDAR 모델은 사용자가 **RPLIDAR A1**이라고 확인했다.

이전에 검토한 후보:
1. 커널 헤더로 `ch341` 모듈을 직접 빌드해서 설치 (sudo 필요, 커널 헤더 확보 필요).
2. Jetson 공식 커널 패키지에 `ch341`이 포함된 버전이 있는지 확인.
3. 먼저 **LiDAR 모델과 연결 방식 확인** (Hiwonder URDF가 지원하는 LiDAR는 A1/A2/S2L/LD14P/G4이고 RPLIDAR C1은 사용자 제공 정보라 미확인. 모델에 따라 어댑터 칩이 CP210x일 수도 있다).

## 결과
- `sudo ./install.sh` 성공, `/dev/ttyUSB0`, `/dev/ttyUSB1` 생성. 커널 로그에 `module verification failed: signature and/or required key missing - tainting kernel`(로드는 됨).
- `ttyUSB1` = RPLIDAR A1M8 (GET_INFO 확인), `ttyUSB0`은 다른 장치(0.5초마다 12바이트를 스스로 송신, 정체 미상).
- **재부팅하면 ttyUSB 번호가 바뀐다** (LiDAR가 ttyUSB1 → ttyUSB0). 그래서 by-path 경로로 지정했다.

## 확인/재발 방지
`lsusb`, `lsusb -t`(Driver 열), `ls /dev/ttyUSB*`, `modinfo ch341`.
