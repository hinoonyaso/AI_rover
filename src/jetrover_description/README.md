# jetrover_description

URDF(xacro)와 `robot_state_publisher` launch.

## 출처 (2026-10-03)
`urdf/*.xacro`와 `meshes/`는 Hiwonder의 공식 `jetrover_arm_moveit` 패키지에서 가져왔다
(`~/AI_secretary_robot/src/control/jetrover_arm_moveit/`, 사용자의 다른 로컬 프로젝트에 있던 사본).
패키지 이름 참조(`$(find jetrover_arm_moveit)`)는 전부 `$(find jetrover_description)`으로 바꿨다.
메카넘(`car_mecanum`)·A1 LiDAR(`lidar_a1`) 구성만 가져왔고 탱크/애커만/G4 LiDAR용 파일은 안 가져왔다
(필요해지면 vendor 쪽에서 더 복사하면 된다).

**`imu.urdf.xacro`의 `imu_joint` rpy는 벤더 원본(`${M_PI} 0 -${M_PI/2}`, 원시 센서 마운트 방향)에서
`0 0 0`으로 수정했다** — `jetrover_base`의 `base_node`가 이미 소프트웨어로 IMU 축을 base_link
convention(x 앞, y 왼쪽, z 위)으로 변환해서 `/imu/data_raw`로 publish하기 때문에, 벤더의 회전을
그대로 쓰면 이중 변환이 된다. 다른 모든 조인트(LiDAR 포함)는 벤더 원본 그대로이고, 우리가 전부터
손으로 유지하던 `jetrover_placeholder.urdf`의 수치와 정확히 일치하는 것도 확인했다.

`jetrover_placeholder.urdf`(이전의 손으로 쓴 박스/실린더 placeholder)는 폐기하지 않고 참고용으로
남겨뒀다 — 더는 launch에서 쓰지 않는다(`description.launch.py`는 이제 `jetrover.xacro`를 처리한다).

## TF 트리 (xacro 처리 후, `check_urdf`로 확인, 2026-10-03)
```
base_footprint → base_link → {back_shell_black_link, back_shell_green_link, imu_link,
    link1 → servo_link1 → link2 → link3 → link4 → {camera_connect_link → depth_cam_link → depth_cam_frame,
        servo_link2 → link5 → {end_effector_link, gripper_link → {l_in_link→l_out_link, l_link, r_in_link→r_out_link, r_link}}},
    lidar_link → lidar_frame,
    wheel_left_back_link, wheel_left_front_link, wheel_right_back_link, wheel_right_front_link}
```
로봇팔(관절 1~5)과 그리퍼가 처음으로 TF 트리에 들어갔고, depth 카메라도 `link4`에 제대로 붙었다
(`checklist/PROJECT_CHECKLIST.md` 4번/11번 섹션의 "팔 링크/카메라 아직" 항목 해결).
실제 bus servo ID(관절 1~5, 그리퍼 10)와 이 URDF 조인트가 맞물리는 컨트롤러는 아직 없다
(MoveIt2/arm_controller는 개발 순서(PRD 13절)의 5단계, 아직 미착수).
