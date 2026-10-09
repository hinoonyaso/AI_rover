# 033 — 팔을 움직인 뒤 팔 관절 TF와 카메라 color TF가 안 나옴 (2026-10-09)

- 상태: **미해결**(재시작으로 복구, 이후 재발 없음)
- 관련: `docs/benchmarks/perception/home_pose_20261009.md`, `tools/perception/arm_set_joint.py`

## 증상
홈 자세 후보 측정 중 `arm/command`로 joint4를 두 번 움직인 뒤 `home_pose_eval.py`가
`base_footprint <- depth_cam_color_optical_frame` TF를 못 찾음("not part of the same tree").
`/tf`를 직접 세어 보니 `robot_state_publisher`의 관절 TF(`base_link→link1…link4`)가 4초 동안 0개,
카메라 드라이버의 `depth_cam_color_frame` 계열도 없음. 반면 `odom→base_footprint`(EKF), `map→odom`(AMCL),
고정 TF(`link4→camera_connect_link` 등)는 정상.

## 확인한 것
- 두 노드 모두 살아 있고 응답함(`ros2 param get` 정상), `/joint_states` 4 Hz·타임스탬프 정상(base_node가 `now()`로 찍음),
  `/joint_states`·`/tf` 연결(endpoint)도 정상. `/dev/shm`·메모리 여유 있음. CPU load 4~6.
- base/카메라 launch 재시작 → 즉시 복구. 이후 팔을 다시 여러 번 움직여도 재발 없음.

## 추정 (미검증)
`robot_state_publisher`는 `/joint_states` 타임스탬프가 마지막 발행 시각+주기보다 이르면 건너뛴다. 어떤 이유로 내부 기준 시각이
앞서 버렸을 가능성. 카메라 color TF도 같이 끊긴 점은 이 설명만으로 안 맞아 DDS 쪽 문제일 수도 있음.

## 재발 시
`/tf`를 프레임 쌍별로 세는 스크립트(이 문서 작성 시 사용한 방식)로 어느 발행자가 멈췄는지 확인 →
`ros2 topic echo /joint_states --once`의 stamp와 `date +%s` 비교 → `robot_state_publisher`만 재시작해 보고 결과 기록.

## 2026-10-10: 진단 도구 저장
문서 작성 때 쓴 "쌍별 /tf 세기"를 `tools/viz/tf_pair_rates.py`로 저장(읽기 전용). 정상 기준(2026-10-10, 홈 자세, base+camera):
관절 TF(`base_link→link1`, `link2→link3`, `link3→link4` …) **5 Hz**(= joint_states 폴링), 카메라 `depth_cam_*` **10 Hz**,
`odom→base_footprint` 30 Hz, static 17쌍, joint_states stamp − now ≈ 0. 재발하면 이 출력과 비교 → 멈춘 쌍의 발행자만 재시작.
`--expect`에 든 프레임(기본 link1, link4, depth_cam_color_frame)이 없으면 종료 코드 1 — 팔 시험 스크립트 앞뒤에 넣어 자동 감지 가능.
