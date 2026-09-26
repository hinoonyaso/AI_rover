# ch341 USB-serial 드라이버 (Jetson 커널에는 없음)

Jetson Linux 커널(`6.8.12-1021-tegra`)은 `CONFIG_USB_SERIAL_CH341`이 꺼져 있어서 CH340/CH341 변환기가
`/dev/ttyUSB*`로 잡히지 않는다 (`troubleshooting/012`). 여기서는 mainline `v6.8`의 `ch341.c`를 그대로 빌드한다.

- `ch341.c`: `https://raw.githubusercontent.com/torvalds/linux/v6.8/drivers/usb/serial/ch341.c` (GPL-2.0)
- `make`: 커널 헤더(`nvidia-l4t-kernel-headers`)로 `ch341.ko` 빌드. vermagic이 실행 커널과 같아야 한다.
- `sudo ./install.sh`: `/lib/modules/<kver>/extra/`에 설치, `depmod`, `modprobe`, 부팅 시 자동 로드(`/etc/modules-load.d/ch341.conf`).

## 커널을 업데이트하면
모듈은 커널 버전에 묶여 있어서 부팅 후 `/dev/ttyUSB*`가 사라지면 다시 빌드한다.
```
cd ~/jetrover_ws/drivers/ch341 && make clean && make && sudo ./install.sh
```

## 확인
```
lsmod | grep ch341
lsusb -t | grep -i ch34        # Driver=ch341
ls -l /dev/ttyUSB*
```
서명 없는 모듈이라 로드할 때 `module verification failed: signature missing` 경고가 뜰 수 있다 (`CONFIG_MODULE_SIG_FORCE`가 꺼져 있어 로드는 된다).
