# 030 — MoveIt2 설정 / Setup Assistant로 SRDF 충돌 매트릭스 생성 (2026-10-06)

패키지: `src/jetrover_manipulation/`. 이 문서는 **어떻게 만들었고, 어떤 파일이 어디서 왔고, 무엇이 실패했는지**를 남긴다.

## 파일의 출처
| 파일 | 내용 |
|---|---|
| `config/jetrover.srdf` | 실제로 쓰는 SRDF. 그룹/home 자세/end effector는 우리가 작성, `disable_collisions`는 아래 두 출처의 합 |
| `config/jetrover.setup_assistant.srdf` | **MoveIt Setup Assistant(host GUI)가 만든 원본 그대로**(126쌍, density 10000, min collisions 95%). 수정하지 않는다 |
| `config/jetrover.conservative_before_sa.srdf` | Setup Assistant 이전에 쓰던 보수적 SRDF(참고 Humble 패키지에서 옮겨 정리, 34쌍). 비교/롤백용 |
| 참고 출처 | `~/AI_secretary_robot/src/control/jetrover_arm_moveit/config/` (Humble) |

## Setup Assistant로 충돌 매트릭스를 다시 만드는 절차 (host)
1. host에서 Jetson의 최신 URDF를 맞춘다: `scp -r sang@jetrover.local:~/jetrover_ws/src/jetrover_description ~/jetrover_viz_ws/src/` 후 빌드.
2. `ros2 launch moveit_setup_assistant setup_assistant.launch.py` -> Create New -> URDF `.../urdf/jetrover.xacro` -> Load Files.
3. Self-Collisions 탭: Sampling Density 10000, Min. collisions for "always"-colliding pairs 95 % -> Generate Collision Matrix.
4. Configuration Files 탭에서 `~/jetrover_viz_ws/sa_out`에 Generate Package(그룹이 없다는 경고는 무시).
5. 생성된 `config/*.srdf`를 Jetson으로 보내 `config/jetrover.setup_assistant.srdf`로 저장.
6. `disable_collisions` 줄만 `jetrover.srdf`에 합친다(그룹/자세는 건드리지 않는다). **아래 7번 항목의 그리퍼 쌍을 반드시 유지.**
7. 검증: move_group 재시작 -> 관절/위치 목표 계획이 성공하는지, `/check_state_validity`로 몸통 껍데기와의 충돌이 검출되는지.

링크(URDF)가 바뀌면 이 절차를 다시 한다.

## 겪은 문제와 해결
1. **SRDF `<chain base_link="link1">`**: joint1(base_link->link1)이 arm 그룹에 안 들어가 `Group state 'home' specifies value for joint 'joint1', but that joint is not part of group 'arm'` 오류. `base_link`~`end_effector_link` 체인으로 수정.
2. **TRAC-IK로 위치 목표가 전부 실패**("Unable to sample any valid states for goal tree"): IK 서비스는 현재 자세에서 정상. 5자유도 팔은 임의의 6D 자세를 못 만드는데 TRAC-IK는 전체 자세를 풀려 한다(OMPL 목표 샘플러는 허용 범위 안의 무작위 자세를 샘플링). KDL `position_only_ik: true`로 교체해 해결. 자세가 필요한 파지는 이후에 관절 공간/별도 IK.
3. **관절 한계 ±1.65가 실제 팔 자세와 충돌**: 실제 팔이 joint3 = 1.688에 놓이면 "start state out of bounds"로 계획 거부(CheckStartStateBounds). 한계를 ±1.70으로. 최종 안전장치는 base_node 펄스 클램프(100~900 = ±1.676 rad).
4. **`/joint_states` 발행자 중복**: plan_only에서 가짜 joint_state_publisher를 켜면 base_node(실제 값)와 섞여 상태가 흔들렸다. launch의 `fake_joint_states` 인자(기본 false)로 분리.
5. **Setup Assistant 생성본만 썼더니 모든 계획 실패**: `CheckStartStateCollision failed: 2 contact(s) detected : l_in_link - l_link, r_in_link - r_link`. 생성기는 기본 그리퍼 자세만 샘플링해 그리퍼 연동부 쌍을 면제 목록에 넣지 않았다. 이전 목록에만 있던 19쌍(그리퍼 연동부 + 카메라 연결부)을 되살려 합침. **이 쌍들은 다음 재생성 때도 반드시 다시 합쳐야 한다.**
6. 정상인 메시지: `No 3D sensor plugin(s) defined for octomap updates`(옥토맵 센서 없음), `No active joints ... for group 'gripper'`(그리퍼 그룹은 끌 마커가 없음).

## 검증 결과 (plan_only, 팔은 움직이지 않음)
- 관절 목표 성공(24점, 약 2.2 s), 위치 목표 4곳 성공((0.12,0.17), (0.20,0.05), (0.30,0.10), (0.15,0.30) in base_link).
- 충돌 검출: 팔을 뒤쪽 껍데기 방향으로 꺾은 자세는 `back_shell_*`와 충돌로 판정, 홈/영점 자세는 정상.
- host RViz(MotionPlanning)가 Jetson의 move_group에 연결돼 계획 표시. Plan and Execute는 plan_only 설정이 막음.

## 실행 브리지 (2026-10-06, 실기 시험 전)
- 구조: MoveIt -> `arm_controller/follow_joint_trajectory`(trajectory_bridge.py) -> `arm/command_timed`(JointTrajectory 1점) -> base_node(스텝 가드 0.35 rad + 펄스 클램프 100~900 재검사).
- **move_group segfault(exit -11)**: moveit_controllers.yaml에서 컨트롤러 두 개 모두 `default: true`면 시작 직후 죽는다. gripper_controller를 `default: false`로.
- **dry_run 종단 시험으로 발견**: 실제 팔이 joint3 = 1.688에 놓여 있어 브리지가 "target 1.688 outside [-1.676, 1.676]"로 거부했다(의도한 동작). 클램프 안의 홈 자세(1.663)로 먼저 들어가야 한다.
- **관절 읽기 갱신이 느림**: arm_poll_hz 5 Hz를 6개 서보에 돌려가며 쓰므로 관절당 ~1.2 s 간격. 빠른 궤적에선 base_node 스텝 가드(현재값 기준 0.35 rad)에 걸릴 수 있어 MoveIt 속도 한계를 0.4 rad/s로 낮추고 실행 시 arm_poll_hz를 12로 올린다(시험 필요, STM32 부하 영향은 미확인).

## 실기 실행 시험 결과 (2026-10-06, 배터리 9.97 V, 사용자가 전원 스위치 옆)
- base_node `arm_command_enabled`/`arm_move_home_on_start`/`arm_poll_hz:=12` 로 재시작 -> 홈 자세 도달, 브리지 `dry_run:=false`.
- 팔은 홈에서 서보가 명령(1.663)보다 6틱 처진 joint3 = 1.688로 쉰다 -> 브리지 limit_rad를 1.676에서 1.70으로(MoveIt과 동일, base_node 펄스 클램프가 최종 안전장치).
- 왕복 4회(joint1 ±0.10, joint2 ±0.15 rad, MoveIt 속도/가속 스케일 0.3): 전부 SUCCESS, 브리지/base_node 거부 없음. 실제 이동량은 목표와 0.004~0.016 rad 차이(서보 데드밴드).
- 아직: RViz에서 큰 위치 목표 실행, 그리퍼 컨트롤러, 충전 후 반복. arm_poll_hz 12가 STM32 hang에 영향을 주는지는 장시간 관찰 필요(이번엔 문제 없음).

## RViz 드래그 마커가 안 보임 -- 원인 확정 (2026-10-07)
- 증상: host RViz에서 Query Goal State를 켜도 팔 끝의 화살표/링(드래그 마커)이 안 보임. 마커 서버 조회(`get_interactive_markers`)에는 `EE:goal_end_effector_link`가 정상적으로 있었다.
- **원인: `moveit.rviz`에 `Tools:` 섹션이 없어 Interact 도구가 없었다.** RViz는 Interact 도구가 활성일 때만 움직일 수 있는 마커 컨트롤을 그린다(툴바에 +/- 버튼만 보이던 것이 단서).
- 검증 방법: Jetson에 Xvfb(apt-get download로 `~/.local/opt/xvfb`에 풀어 sudo 없이)로 가상 화면을 띄우고 RViz를 직접 렌더링. 진단 마커로 분리 시험: 모양이 있는 고정 컨트롤(박스)은 보이고 움직이는 컨트롤(화살표, 직접 넣은 화살표 포함)은 안 보임 -> Tools 추가 후 모두 보임.
- 같이 고친 것: RViz2 InteractiveMarkers 표시의 속성 이름은 `Update Topic`(ROS1)이 아니라 `Interactive Markers Namespace`. 중복 DragMarker 표시는 제거(MotionPlanning 내장 표시로 충분).
- 잘못 짚었던 것(기록): SRDF end_effector/virtual_joint 수정은 마커 미표시의 원인이 아니었다(virtual_joint 제거로 planning frame이 TF에 있는 base_footprint가 된 것 자체는 유지).

## 그리퍼 각도 부호 검증 (2026-10-07)
- 실제 그리퍼를 활짝 연 상태(서보 tick 205)에서 기존 부호(-1)로 r_joint = +1.236.
- r_joint 부호를 +1로 바꿔 봤으나(-1.236) **틀림**: 메쉬 관통 계산(손가락 메쉬 vs 볼록 껍질)에서 부호 +1이면 좌우 손가락(l_link<->r_link, l_in<->r_in)이 서로 관통, 기존 부호(-1)면 관통 없음. 카메라 메쉬 경계 안으로 들어가는 손가락 꼭짓점은 두 경우 모두 0개. -> **기존 부호 -1이 맞음, 원복함**.
- 남은 의문: 모델에서 1.236 rad(약 71도)로 벌어진 정도가 실제 그리퍼의 "활짝 연" 정도와 같은지(서보 각도 -> 손가락 각도 비율). Hiwonder 참고 시험 코드는 open 650 / close 350 펄스를 쓰지만 이 로봇은 닫힘 ~504, 열림 205로 읽혀 기준이 다르다. 실물과 RViz를 나란히 보고 비교해야 확정.

## 마커 회전 링이 효과 없음 -> IK를 pick_ik로 교체 (2026-10-07)
- 원인: KDL `position_only_ik: true`는 자세를 완전히 무시하므로 회전 링을 돌려도 IK 해가 그대로였다.
- 해결: `pick_ik`(위치는 정확히, 자세는 rotation_scale 가중치로 가능한 만큼). compute_ik 검증: 같은 위치에서 공구 피치 -0.3 rad -> joint2~4 변화, 롤 +0.5 rad -> joint5가 정확히 -0.5 변화. 옆으로 비틀기(5자유도로 불가능)는 해 없음(정상).
- 설치: apt 패키지 `ros-jazzy-pick-ik`. sudo 없이 `apt-get download` + `dpkg-deb -x`로 `~/.local/opt/pick_ik`에 풀고 `AMENT_PREFIX_PATH`/`LD_LIBRARY_PATH`에 추가해서 사용 중(Jetson move_group, host RViz 둘 다 필요 -- RViz도 마커 IK를 자기 쪽에서 푼다). host는 `~/jetrover_viz_ws/moveit_rviz.sh`로 실행. 정식으로는 두 장비에서 `sudo apt install ros-jazzy-pick-ik`.
- 그리퍼 컨트롤러 재활성화(default: false). 그리퍼 속도 한계 0.5 rad/s x RViz 속도 스케일 0.1이면 1.2 rad 이동에 약 25초 -- 그리퍼는 스케일을 올려서 쓴다.
- (보완) pick_ik `orientation_threshold: 0.6`은 실패: 0.6 rad 미만 회전은 이미 만족으로 보고 관절을 안 바꾸고, 위치 드래그는 자세 유지 조건 때문에 대부분 실패했다.
  최종: 정확 모드(위치 1 mm, 자세 0.01 rad) + 근사 모드(`approximate_solution_*`: 위치 5 mm, 자세 무제한). RViz Planning 탭의 **Approx IK Solutions**를 체크해야 드래그가 근사 해를 쓴다.
  compute_ik(정확 모드) 검증: 실제 피치축(팔 평면에 수직, base 기준) -0.3 rad -> joint2~4 변화, 롤 +0.5 -> joint5 -0.5, 자세 고정 위치 이동(+x, +y)은 실패(근사 모드 필요, 정상).
