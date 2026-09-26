# robot_state_publisher에 URDF를 `-p`로 넘기면 죽는데 시험은 exit=0으로 끝남
- 날짜: 2026-09-20
- 상태: 해결
- 관련: `tools/stm32_diagnostics/ekf_pipeline_test.py`

## 증상
`robot_state_publisher --ros-args -p robot_description:=<URDF 전체>`로 띄웠더니
`terminate called after throwing an instance of 'rclcpp::exceptions::RCLInvalidROSArgsError'`로 죽었다.
`imu_link` TF가 없어져 EKF가 자이로를 못 받았고, 파이프라인 시험에서 회전 단계가 0으로 나왔다.
그런데 스크립트는 결과를 출력만 해서 `exit=0`으로 끝났다.

## 원인
여러 줄짜리 URDF(XML 선언과 따옴표 포함)를 명령줄 인자로 넘기면 ROS 인자 파서가 거부한다.
시험 스크립트에 PASS/FAIL 판정이 없어서 실패가 종료 코드로 드러나지 않았다.

## 해결 또는 우회
- URDF를 임시 파라미터 YAML 파일(`robot_description: |` 블록)로 만들어 `--params-file`로 넘긴다.
- 시험 스크립트가 값을 허용 오차로 검사해서 `RESULT: PASS/FAIL`을 출력하고 실패 시 종료 코드 1을 돌려주게 했다.

## 확인/재발 방지
launch 파일에서는 `Node(parameters=[{'robot_description': 문자열}])`로 넘기면 문제없다 (`description.launch.py`).
시험 스크립트는 출력만 하지 말고 **판정과 종료 코드**를 넣는다.
