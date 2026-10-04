# host RViz에서 base_link 메쉬만 "Could not load mesh resource" 에러
- 날짜: 2026-10-04
- 상태: 해결
- 관련: `src/jetrover_description/urdf/car_mecanum.urdf.xacro`, `description.launch.py`, host의 `~/jetrover_viz_ws`

## 증상
host(Ubuntu 24.04, 별도 `~/jetrover_viz_ws`에 `jetrover_description`을 scp+colcon build로 준비)에서
`rviz2 -d ~/jetrover.rviz`를 실행하면 다른 메쉬(바퀴/IMU/LiDAR/팔/그리퍼)는 다 뜨는데 `base_link`만
에러가 났다:
```
Could not load resource [file:///home/sang/jetrover_ws/install/jetrover_description/share/jetrover_description/meshes/mecanum/base_link.stl]: Unable to open file ...
```
`/home/sang/jetrover_ws/...`는 **Jetson의 경로**인데, host는 `~/jetrover_viz_ws`를 쓰고 `~/jetrover_ws`
자체가 host엔 없었다. host의 `AMENT_PREFIX_PATH`가 `~/jetrover_viz_ws/install/jetrover_description`을
제대로 가리키고 `ros2 pkg prefix jetrover_description`도 정상인데도 에러가 계속 났다.

## 원인
`car_mecanum.urdf.xacro`에서 `base_link`의 시각 메쉬 **한 줄만** 다른 패턴을 쓰고 있었다:
```xml
<!-- 문제: -->
<mesh filename="file://$(find jetrover_description)/meshes/mecanum/base_link.stl" />
<!-- 바로 아래 collision 메쉬, 바퀴 전부는 정상 패턴: -->
<mesh filename="package://jetrover_description/meshes/mecanum/base_link_collision.stl" />
```
`package://...`는 **런타임에** 메쉬를 불러오는 쪽(resource_retriever, 여기선 host의 RViz)이 자기
환경에서 해석하는 URI라 어느 기계에서 열어도 된다. 반면 `$(find jetrover_description)`은 **xacro가
도는 기계에서 그 순간** 절대경로로 치환되는 xacro 커맨드다. `robot_state_publisher`(`description.launch.py`의
`Command(['xacro ', xacro_file])`)는 **Jetson에서** 돌기 때문에, 생성된 `/robot_description`
문자열 안에 Jetson의 절대경로(`/home/sang/jetrover_ws/install/...`)가 그대로 박혀서 네트워크로
나갔다. host가 패키지를 제대로 빌드해놨어도 애초에 그 문자열 자체가 host 경로가 아니니 당연히 실패.

Hiwonder 원본 벤더 파일 자체의 오타/비일관성으로 보인다(같은 파일의 나머지 9개 메쉬 참조는 전부
`package://`를 정상적으로 썼다).

## 해결 또는 우회
`file://$(find jetrover_description)/...`를 `package://jetrover_description/...`로 고쳤다
(한 줄). `grep -rn 'file://\$(find' urdf/*.xacro`로 같은 패턴이 다른 곳에 없는지 전체 확인함(없음).
`colcon build --packages-select jetrover_description` 후 `robot_state_publisher`만 재시작
(`ros2 launch jetrover_description description.launch.py`)하면 적용된다 — `base_node`/EKF/LiDAR는
안 건드려도 됨.

## 확인/재발 방지
- **원격(host) RViz 시각화 + Jetson에서 xacro를 처리하는 구조에서는, `/robot_description`에 로컬
  절대경로가 안 섞여 있는지 직접 확인하는 게 안전하다**: `/robot_description`을 직접 구독해서
  (QoS는 `TRANSIENT_LOCAL`/`RELIABLE` — 기본 `ros2 topic echo`는 QoS 안 맞으면 조용히 실패한다,
  `troubleshooting/015` 참고) 호스트명/워크스페이스 경로 문자열(`/home/<user>/..._ws`)이 들어있는지
  grep해본다.
- 새로 vendor 파일을 가져올 때는 `grep -rn 'file://\$(find\|\$(find.*\.stl\|\.dae'` 정도로 메쉬
  참조 방식이 전부 `package://`로 일관되는지 한 번 점검한다.
