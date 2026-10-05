# RGB-D 카메라가 Nav2 풀스택과 같이 돌 때 IR+PointCloud 켜면 조용히 멈춤
- 날짜: 2026-10-05
- 상태: 해결(우회)
- 관련: `src/jetrover_perception/config/dabai_dcw.yaml`, `tools/start_remote_viz_stack.sh`

## 증상
전날(2026-10-04) RGB/Depth/PointCloud/정렬/캘리브레이션까지 전부 실측 확인했던 카메라가, 다음 세션에서
갑자기 `/depth_cam/color/image_raw`, `/depth_cam/depth/image_raw` 둘 다 전혀 발행되지 않았다.
`ros2 node info`엔 publisher가 정상적으로 떠 있고(advertise는 됨), 로그도 매번
"Device DaBai DCW connected" → "Publishing dynamic camera transforms (/tf) at 10 Hz"까지 에러
없이 끝까지 찍히는데, **실제 프레임이 하나도 안 나왔다.** `web_video_server`로 봐도 "No valid point
in point cloud" 경고만 반복됐다.

## 시도했지만 안 된 것들 (순서대로)
1. 프로세스 kill 후 재시작 — 안 됨 (여러 번)
2. 호스트↔Jetson DDS 프로필을 카메라 쪽에도 맞춰서 테스트 — 무관함, 안 됨
3. USB 케이블 물리적으로 뽑았다 꽂기(같은 포트) — 안 됨
4. **Jetson 전체 재부팅** — 안 됨(가장 강력한 소프트웨어 리셋인데도 재발)
5. `sudo dmesg`로 커널 로그 확인: RGB 서브장치(`idProduct=0559`)가 Depth 서브장치(`idProduct=0659`)보다
   USB enumeration이 **34초나 늦게** 끝나는 게 보여서 "USB 연결 불안정" 가설을 세움
6. 허브의 다른 포트로 옮겨 꽂음 → 이번엔 RGB enumeration이 0.6초 만에 끝남(정상 속도로 보임).
   **그런데도 스트림은 여전히 안 나옴** → 5번 가설(USB 연결 불안정) 기각

## 원인 (확정)
`src/jetrover_perception/config/dabai_dcw.yaml`에서 `enable_ir`와 `enable_point_cloud`를 꺼보니
(`enable_color`/`enable_depth`만 켜둔 상태) **바로 정상 작동**했다. 이어서 IR은 끈 채로
`enable_point_cloud`만 다시 켰더니 **또 멈췄다** — 즉 PointCloud 계산 자체가 범인 중 하나다.

지금 Jetson에서는 이미 `jetrover_bringup robot.launch.py`(base_node+EKF+LiDAR) +
`jetrover_navigation nav2.launch.py`(map_server+amcl+controller/planner/bt_navigator 등 11개
노드)가 전부 떠 있는 상태였다. 이 전체 로드 위에 color+depth+ir 3-스트림 동시 디코드 +
PointCloud 생성(640×360 depth 기준 초당 최대 640×360×30 ≈ 690만 포인트 계산)까지 얹히면서
**USB 대역폭이 아니라 Jetson 자체의 CPU/스케줄링 자원 경합**으로 드라이버의 USB 읽기 스레드가
멈춘 것으로 추정된다(확정은 아님 — `perf`/`top` 등으로 직접 병목을 찍어보진 않았다). 전날
PointCloud가 잘 됐던 건 아마 그때는 Nav2 풀스택이 덜 떠 있었거나 타이밍이 달랐기 때문으로 보인다.

## 해결 또는 우회
`enable_ir: false`, `enable_point_cloud: false`를 기본값으로 바꿈(`dabai_dcw.yaml`). 지금
프로젝트에서 IR 스트림은 아무 데도 안 쓰고, PointCloud도 평소엔 안 쓴다(필요할 때만 켜는 용도).
RGB+Depth만으로 TF/정렬/캘리브레이션 재검증에 필요한 건 전부 된다.

**PointCloud가 꼭 필요하면**: Nav2 풀스택을 내리고 카메라만 단독으로 띄운 상태에서 켜거나,
Jetson 리소스 여유가 있는 상황에서만 켜는 걸 권장한다. 상시 켜두는 설정으로 쓰지 않는다.

## 확인/재발 방지
- 카메라가 "로그는 정상인데 토픽이 안 나온다" 싶으면, **먼저 `enable_ir`/`enable_point_cloud`를
  꺼보고** 그래도 안 되면 그때 USB/하드웨어 쪽을 의심한다(순서를 반대로 해서 USB 재부팅까지
  갔다가 나중에야 이게 원인인 걸 알았다 — 다음엔 설정부터 줄여본다).
- Nav2 풀스택 + 카메라(전체 스트림)를 동시에 켜는 조합은 이 Jetson(Orin Nano)에서 **리소스가
  빠듯할 수 있다** — 새 기능(YOLO 등)을 얹을 때도 `free -h`/CPU 사용률을 같이 확인한다
  (AGENTS.md의 "무거운 네이티브 빌드" 경고와 같은 종류의 문제).
