# 호스트 RViz의 Nav2 Goal/2D Pose Estimate가 Jetson에 전혀 안 닿음 (DDS 디스커버리 + RViz 툴 설정, 3중 원인)
- 날짜: 2026-10-04
- 상태: 해결
- 관련: `setup/fastdds_wifi_only.xml`, 호스트의 `~/fastdds_wifi_main.xml`(워크스페이스 밖), `~/jetrover.rviz`(호스트), `src/jetrover_base/config/ekf.yaml`

## 증상
호스트(`sang-GF63-8RC`, 별도 `~/jetrover_viz_ws`)에서 RViz로 Jetson의 로봇을 원격 조작하려 했다.
RViz에는 `/scan`, `/tf`, `/odom`, `/robot_description` 등 Jetson이 보내는 데이터는 전부 정상적으로
떴다. 하지만:
- RViz의 "SetInitialPose"로 클릭해도 Jetson 쪽에서 `/initialpose`에 publisher가 0개로 보임.
- "Nav2 Goal" 버튼을 눌러 드래그해도 `/navigate_to_pose` action에 외부 client가 전혀 안 뜨고,
  RViz 자체 로그에도 아무 흔적이 안 남음(2D Pose Estimate는 "Setting estimate pose:..."를 매번
  로그로 남기는 것과 대조적).
- RViz의 "Map" 디스플레이는 "No map received"만 뜸(Jetson 쪽 `/map`은 정상 발행 중인데도).

## 원인 (세 가지가 섞여 있었다)

### 1. Jetson이 여러 네트워크 인터페이스를 가져서 Fast-DDS 디스커버리가 비대칭으로 깨짐
Jetson에 `wlP1p1s0`(실제 WiFi, 172.30.1.82), `l4tbr0`(192.168.55.1, USB 브리지),
`docker0`(172.17.0.1) 세 개가 있었다. Fast-DDS(`rmw_fastrtps_cpp`, 이 Jetson에 설치된 유일한
RMW)가 기본적으로 전부에 대고 공지/수신하면서, Jetson→호스트 방향(스캔/TF/오도메트리 등)은 잘 가는데
호스트→Jetson 방향(퍼블리셔/구독자 디스커버리)만 깨지는 비대칭 증상이 났다.
`ros2 action info /navigate_to_pose`로 내부 노드(bt_navigator 등)만 client로 보이고 외부 client가
전혀 안 뜨는 것, `ros2 topic info /initialpose -v`에서 Publisher count가 0인 것으로 확인했다.

### 2. 호스트도 유선+무선이 같은 대역에 동시 연결돼 있어서 똑같은 문제가 대칭으로 발생
Jetson 쪽만 인터페이스를 WiFi로 고정했더니 `/initialpose`는 되는데 `/map`(TRANSIENT_LOCAL,
"latched" 토픽)과 `/goal_pose`는 여전히 host 쪽에서 Jetson으로 디스커버리가 전파되지 않았다.
`ip addr show`로 확인해보니 호스트(`sang-GF63-8RC`)가 **유선 `enp3s0`(172.30.1.50)과 무선
`wlo1`(172.30.1.44)을 동시에** 같은 `172.30.1.0/24` 대역에 올리고 있었다. 패킷이 어느 인터페이스로
나갈지 일관되지 않아서 host↔Jetson 디스커버리가 가끔만 성공하는 식으로 꼬였다.

### 3. (진짜 "Nav2 Goal" 버튼이 안 먹던 이유) RViz 툴 자체가 토픽을 안 쏘는 종류였다
`nav2_rviz_plugins::GoalTool`(툴바 이름 "Nav2 Goal") 소스를 직접 받아서 봤다
(`nav2_rviz_plugins/src/goal_tool.cpp`, navigation2 `jazzy` 브랜치):
```cpp
void GoalTool::onPoseSet(double x, double y, double theta)
{
  // Set goal pose on global object GoalUpdater to update nav2 Panel
  GoalUpdater.setGoal(x, y, theta, context_->getFixedFrame());
}
```
이 툴은 **토픽 발행도, action 호출도 하지 않는다.** RViz 프로세스 내부의 전역 객체
`GoalUpdater`에 값만 써 두고, 그 값을 실제로 소비해서 action을 호출하는 건 **"Navigation 2" 패널**
(`nav2_rviz_plugins::Navigation2Panel`)의 몫이다. 호스트의 `~/jetrover.rviz`에는 Displays/Views
패널만 있고 Navigation 2 패널이 없어서, 버튼을 누르고 드래그해도 **RViz 프로세스 안에서 완전히
조용히 무시됐다** — 로그도, 퍼블리셔도, action client도 하나도 안 생기는 게 당연했다. 1·2번
디스커버리 문제를 다 고친 뒤에도 이것 때문에 "SetInitialPose는 되는데 Nav2 Goal만 안 됨" 증상이
계속 남아 있었다.

## 해결 또는 우회

1. **Jetson에 WiFi 전용 Fast-DDS 프로필 적용**: `setup/fastdds_wifi_only.xml`
   (`interfaceWhiteList: 172.30.1.82`, `useBuiltinTransports: false`).
   `~/.bashrc`에 `export FASTRTPS_DEFAULT_PROFILES_FILE=/home/sang/jetrover_ws/setup/fastdds_wifi_only.xml`
   추가(ROS_DOMAIN_ID 설정 바로 아래). 로봇 스택(`jetrover_bringup robot.launch.py`,
   `jetrover_navigation nav2.launch.py`) 전체를 이 환경변수가 걸린 상태로 재시작해야 적용된다.
2. **호스트에도 동일한 WiFi 전용 프로필 적용**: 호스트 홈 디렉터리에 같은 구조의 XML을
   `interfaceWhiteList: 172.30.1.44`(wlo1)로 만들어서 `FASTRTPS_DEFAULT_PROFILES_FILE`로 지정하고
   RViz를 재시작. (이 파일은 호스트 머신에 있고 `jetrover_ws` 밖이라 이 저장소에는 없음 — 호스트
   쪽 설정 기록은 호스트 자체에 남겨야 함, `jetrover_viz_ws`가 있다면 거기.)
3. **"Nav2 Goal" 툴을 "2D Nav Goal"(`rviz_default_plugins`, 클래스명 `SetGoal`)로 교체**: RViz
   툴바에서 "Nav2 Goal" 제거(`−` 버튼) → "+"로 "2D Nav Goal" 추가. 이 툴은 "SetInitialPose"와
   같은 `PoseTool` 계열로 `/goal_pose`에 직접 `PoseStamped`를 발행하므로 Navigation 2 패널 없이도
   바로 동작한다(`bt_navigator`가 `/goal_pose`를 직접 구독하고 있는 걸 코드로 확인). 설정은
   File → Save Config로 저장해야 다음 RViz 실행에도 유지된다(저장 안 하면 재시작할 때마다 기본
   툴로 돌아감 — RViz 툴의 퍼블리셔/액션클라이언트는 그 툴을 실제로 한 번 활성화해야 생성되고,
   RViz를 새로 켤 때마다 다시 활성화해야 한다는 것도 이번에 확인).
4. **(막다른 길, 기록만 남김) amcl의 "Failed to transform initial pose in time" 경고**: 처음엔
   이게 pose 유실의 원인인 줄 알았으나, `nav2_amcl/src/amcl_node.cpp`의
   `AmclNode::handleInitialPose`를 직접 받아서 보니 **무해한 경고**였다. 이 함수는
   `tf_buffer_->lookupTransform(base_frame_id_, msg.header.stamp, base_frame_id_, now(), odom_frame_id_)`로
   "메시지 시각 ~ 지금 사이 오도메트리 변화량"을 구해서 보정하는데, 예외가 나면
   `catch` 블록에서 그 보정값을 **identity로 대체**하고 그대로 진행한다
   (`pose_new = pose_old * identity = pose_old`, 즉 클릭한 pose 값 자체는 그대로 쓰인다 — 실측으로도
   `Setting pose` 로그가 RViz가 보낸 좌표와 정확히 일치함을 확인했다). 예외의 실제 원인은
   `now()`가 EKF의 주기적 TF 발행(30 Hz, 주기 ~33 ms)보다 항상 조금 앞서는 구조적인 경쟁 상태이고
   `transform_tolerance`(0.5로 올려도 무변화, 이 호출 경로에는 적용 안 됨을 코드로 확인) 파라미터로는
   못 고친다. EKF `frequency`를 30→100으로 올려서 경쟁 창을 줄여보려 했지만 Jetson이 못 따라가서
   오히려 `ekf_filter_node`가 "Failed to meet update rate"(최대 0.5초 지연)로 더 나빠져서 30으로
   되돌렸다(`src/jetrover_base/config/ekf.yaml`). 결론: **이 경고는 무시해도 된다.**
5. 이 과정에서 "메시지 타임스탬프를 0으로 relay해서 우회"하는 `stamp_zero_relay` 노드를
   `jetrover_navigation`에 만들었었는데, 4번에서 밝혀졌듯 amcl은 메시지의 stamp가 아니라
   **자기 자신의 `now()`**를 쓰기 때문에 애초에 효과가 없는 접근이었다. 만든 즉시 삭제(커밋에는
   안 남음).

## 확인/재발 방지
- 호스트→Jetson 디스커버리가 의심되면 먼저 `ros2 topic info <topic> -v`로 Publisher/Subscriber
  count와 어느 쪽 노드가 비어 있는지부터 본다. "Jetson→호스트는 되는데 반대는 안 됨"이면 거의 항상
  둘 중 하나(또는 둘 다) 머신의 다중 네트워크 인터페이스 문제다 — `ip addr show`로 같은 대역에
  인터페이스가 두 개 이상 있는지 확인한다.
- RViz 툴이 "눌러도 반응 없음"이면, **그 툴이 실제로 토픽/액션을 쏘는 종류인지 먼저 소스로 확인**한다
  (`.rviz` 파일의 `Tools:` 섹션에서 `Class:` 값을 보고 GitHub에서 해당 `.cpp`를 받아 `onPoseSet`/
  유사 콜백을 읽는다). RViz 패널 전용으로 설계된 툴(이번 `nav2_rviz_plugins/GoalTool`처럼)은 그
  패널이 없으면 조용히 아무 일도 안 하고, 에러 로그조차 안 남는다.
- RViz 설정(`.rviz`)에 `*`가 붙어 있으면(제목표시줄) 저장 안 된 변경사항이 있다는 뜻 — 재시작하면
  사라진다. 테스트가 잘 됐으면 File → Save Config.
- amcl의 "Failed to transform initial pose in time" / "extrapolation into the future" 경고는
  무시해도 된다 — `Setting pose` 로그의 좌표가 클릭한 좌표와 일치하는지만 확인하면 충분하다.
- EKF `frequency`는 30 유지. 더 올리면 이 Jetson에서는 역효과(업데이트 지연)가 난다 —
  `src/jetrover_base/config/ekf.yaml`에 기록.
- 최종 확인: 호스트 RViz에서 "2D Nav Goal"로 실제 로봇이 움직이는 것까지 실물로 확인함(2026-10-04).
