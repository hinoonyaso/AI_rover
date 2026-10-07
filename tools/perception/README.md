# tools/perception — 팔 홈(주행) 자세 재설계 도구 (checklist 8.13.5)

depth 카메라가 팔 끝(link4)에 있어서 **팔 홈 자세 = 장애물 감지 시야**다. 지금 자세(2026-10-05)는 앞 0.18~0.51 m만 본다.
목표: 가까운 끝 ≈ 0.2 m 유지 + 먼 끝 0.8~1.0 m 이상, LiDAR 가림 악화 없음.

| 파일 | 하는 일 | 로봇 움직임 |
|---|---|---|
| `home_pose_eval.py <label> [--png]` | 지금 팔 자세의 바닥 시야 지표를 `Log/home_pose_eval.csv`에 한 줄 추가 | 없음(읽기만) |
| `capture_depth_reference.py [--dry-run]` | 새 홈 자세의 기준 depth 촬영(기존 파일 자동 백업) | 없음(읽기만) |
| `floor_metrics.py` / `test_floor_metrics.py` | 계산 부분(numpy) + 합성 바닥 단위시험(CI) | — |

## 지표 읽는 법 (`home_pose_eval.py`)
- `floor_near_m` / `floor_far_m`: 바닥이 보이는 앞쪽 거리(5/95 백분위). **near ≤ 0.25, far ≥ 0.8**이 목표.
- `lane_cover`: 로봇 폭(|y|<0.25) 안에서 0.20~1.00 m를 5 cm 칸으로 나눴을 때 바닥이 보이는 칸 비율. 1.0이면 차로에 사각 없음.
- `width_0.5_m` / `width_1.0_m`: 그 거리에서 보이는 바닥 폭(로봇 폭 0.5 m 이상이어야 차로 전체를 봄).
- `self_frac`: 화면 중 로봇 자기 몸 비율(기준 depth가 지우므로 약간은 괜찮음).
- `low_frac`: **빈 바닥에서 0에 가까워야 함.** 크면 앞에 물체가 있거나 TF/URDF/관절값이 어긋난 것.
- `scan_valid`: LiDAR 유효 빔 비율(지금 약 0.49). 줄어들면 팔이 LiDAR를 더 가린 것.
- `cam_pitch_deg`, `cam_h_m`: 카메라 숙임 각도/높이(URDF+실제 관절값 기준).

## 절차 (팔이 움직이는 단계는 사용자 입회·승인 필요, 배터리 10 V 이상)
1. `robot.launch.py arm_command_enabled:=true arm_move_home_on_start:=true`, `camera.launch.py colorizer:=false`. 로봇 앞 1.5 m 비우기.
2. 기준선: `home_pose_eval.py current_home --png`.
3. 후보 자세로 이동(`arm/command`, 한 번에 0.35 rad 이하 단계) → `home_pose_eval.py <후보이름> --png`. 2~3개 반복.
   단서: 손목(joint4)을 들면 멀리 보지만 가까운 끝도 멀어진다(10-05 기록: joint2/3를 더 접으면 펄스 클램프 100~900에 걸림).
4. 고른 자세에서: `capture_depth_reference.py --dry-run`(노이즈 p95가 margin 60 mm보다 충분히 작은지) → 실제 촬영.
5. `base.yaml` `arm_home_pose_rad`를 그 관절값으로(바꾸기 전 이전 값 기록) → `colcon build --packages-select jetrover_base jetrover_perception` → 재기동.
6. 확인: 빈 바닥에서 `/depth_cam/depth/points_sparse` 점 수 ≈ 0, 상자를 0.3/0.6/0.9 m에 두고 점이 나오는지.
