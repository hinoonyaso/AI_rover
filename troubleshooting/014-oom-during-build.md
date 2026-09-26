# colcon build가 메모리를 다 써서 시스템이 멈추고 SSH가 끊김
- 날짜: 2026-09-22~23
- 상태: 해결
- 관련: `orbbec_camera` 소스 빌드(`colcon build --packages-select orbbec_camera_msgs orbbec_camera orbbec_description`)

## 증상
카메라(OrbbecSDK v1) 소스 빌드를 시작한 지 3~5분 만에 SSH 연결이 끊기고 다시 연결되지 않았다.
사용자가 두 번(2026-09-22 23:5x, 2026-09-23 00:0x) 로봇 전원을 껐다 켰다.

## 원인
**메모리 부족.** 이 Jetson은 데스크톱 GUI(GNOME 세션)가 같이 떠 있고, RAM은 7.3 GiB인데 **스왑이 0**이다.
`colcon build`가 기본값(`-j6 -l6`, CPU 6코어 전부)으로 네이티브 C++ SDK를 컴파일하면서 메모리를 다 써버렸다.

결정적 증거(두 번째 부팅의 죽기 직전 저널):
```
notify-send 'Low Memory Warning' 'Memory available for new process: 72 MB
 free 77 MB, buffers/cache 183 MB'
```
직후 USB 장치가 반복적으로 끊겼다 붙었다 하고 GPU(NVRM/DCE) RPC 에러가 나면서 시스템이 응답하지 않게 됐다.
첫 번째 부팅에서도 빌드 시작 3분 뒤부터 `sshd`가 `Broken pipe [preauth]`를 반복하며 새 연결을 못 받았다 — 같은 증상.

`systemd-oomd`(조기 개입하는 유저스페이스 OOM 킬러)는 이 커널에 `/proc/pressure/memory`가 없어서
애초에 비활성 상태였고, 커널 OOM 킬러가 실제로 프로세스를 죽인 로그도 없다(그 전에 시스템 전체가 먼저 맛이 감).

## 해결 또는 우회
- **병렬도를 낮춰서 빌드**: `MAKEFLAGS=-j2`, `colcon build --parallel-workers 1`로 재시도.
- 빌드 중 `free -h`로 짧은 간격(1~2분)마다 직접 감시하고, 여유 메모리가 위험 수준(수백 MB 이하)으로 떨어지면
  빌드를 즉시 중단한다. 5분 이상 확인 없이 방치하지 않는다.
- **`-j2`만으로는 부족했다.** 스왑 없이 `-j2`로 재시도했을 때도 빌드 도중 여유 메모리가 88 MB까지 떨어져서
  다시 위험한 상태가 됐고, 시스템이 죽기 전에 직접 빌드를 중단시켰다.
- **스왑 4 GB 추가함** (`/swapfile`, `sudo fallocate/mkswap/swapon` + `/etc/fstab` 등록, `setup/ENVIRONMENT_SETUP.md` 6번).
  스왑을 추가한 뒤 같은 `-j2`로 다시 시도하자 이번엔 안전하게 끝났다(실제 스왑 사용량은 `0B`였지만,
  스왑이 존재한다는 것만으로 커널의 메모리 여유 계산/회수 동작이 달라져 도움이 된 것으로 보인다. 확정은 아니다).
  스왑은 **앞으로의 다른 무거운 빌드(YOLO/TensorRT 등)를 위한 안전망**으로도 남겨둔다.

## 확인/재발 방지
- 무거운 네이티브 빌드(특히 `orbbec_camera`, TensorRT/YOLO 등 앞으로 나올 큰 빌드)는 항상 낮은 병렬도로 시작하고
  `free -h`를 자주 확인한다.
- 스왑이 설정되면 `free -h`의 `Swap` 줄로 확인.
- 이 로봇은 헤드리스가 아니라 **GNOME 데스크톱이 동시에 떠 있다** — 메모리 여유를 셈할 때 이것도 고려한다.
