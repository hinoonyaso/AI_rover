# 065 Jetson의 Gazebo 임무가 시간 초과·START_OCCUPIED로 실패

상태: 우회 적용 (2026-11-22). 근본 해결(호스트 PC에서 Gazebo 실행)은 미적용.

## 증상
음성 출발점 복귀(Gazebo `return_to_start`) 시험 3회 중 2회 실패.
- 일시정지 → 재개 뒤 같은 구간이 180초(벽시계) 안에 끝나지 않아 `timeout_cancel_confirmed`. STT 서버를 꺼도 재현.
- 일시정지 없는 대조 1회는 목표 전송 직후 `ABORTED error_code=205`(ComputePathToPose `START_OCCUPIED`).
- 주행 중 collision_monitor가 "depth_cloud 시각 차 1초 초과, invalid source로 정지"를 반복.

## 원인
Jetson에서 Gazebo+Nav2+센서 서비스+대시보드+MySQL+STT 서버가 함께 돌아 load average 약 16(6코어), 메모리 거의 소진, 스왑 1.9GB. 성공 회차에서 시뮬 시간 25초·36초인 구간이 벽시계 약 124초·186초 걸려 **Gazebo가 실시간의 약 1/5로 동작**했다. 벽시계 180초 제한(기존 단일 구간 125~131초, 2026-11-16 기록)과 늦게 도착하는 depth 점 때문에 진행 중인 주행이 실패했다. START_OCCUPIED는 시작 직후 비용지도 정리 전의 경쟁으로 보이며 원인 확정은 아니다.

## 조치
- `gazebo_nav_trial.py` 구간 제한을 **시뮬레이션 시간 180초**로 변경, 벽시계 600초 안전 상한.
- 목표 전송 5초(시뮬) 안의 START_OCCUPIED는 3초 뒤 한 번 재전송.
- 결과: 같은 시험(일시정지 8초 → 재개 → 두 구간) `succeeded / returned_to_start`, 벽시계 355초.

## 남은 것
대시보드 Gazebo 임무가 5~6분 걸린다. AGENTS.md의 원래 계획대로 Gazebo를 호스트 PC에서 돌리거나 Jetson 동시 실행 서비스를 줄여야 실사용 속도가 나온다. 반복 횟수 1회라 안정성 판단에 충분하지 않다.

## 호스트 PC 이전 시도 (2026-11-22)

사용자 지시로 호스트(172.30.1.50, 12코어, GTX 1050) `~/AI_rover`에서 진행. 호스트의 미커밋 문서 수정은 `git stash`(`host local edits before pull 2026-11-22`)로 보존 후 `2e260c2`로 pull, `colcon build --packages-up-to jetrover_gazebo jetrover_navigation jetrover_bringup` 성공.

- 첫 실행 `gazebo_start_failed`: 원인은 **`tools/nav/ab_params/nav2_params_mppi.yaml` 없음**(git 제외 생성 파일). `make_variants.sh`는 `~/jetrover_ws` 경로가 고정돼 있다.
- **Jetson의 이 파일은 2026-10-11 생성본으로, 10-25에 바뀐 공식 nav2_params(VoxelLayer·footprint padding 등)를 반영하지 않는다.** 11-16 Gazebo 임무 성공 기록과 오늘 Jetson 시험은 모두 이 옛 설정으로 돌았다.
- 호스트에서 현재 공식 설정으로 만든 파일(`nav2_params_mppi.current.yaml`로 보관): 첫 계획 "no valid path", 재개 후 2초 만에 BT 중단.
- Jetson과 같은 옛 파일 사용: 출발 → 일시정지 → 재개 → 1구간 도착 성공(시뮬 21초, 벽시계 약 46초), **복귀 구간은 8초 만에 BT 중단**. 호스트에서도 collision_monitor가 "depth 데이터 지연(invalid source)"으로 반복 정지했다. 호스트 load average 약 3(12코어)으로 CPU 부족은 아니며, 실시간 비율이 1보다 낮은 원인(센서 렌더링 등)은 미확인.
- 결론: 일시정지·재개 자체는 Jetson·호스트 모두 동작했다. **Gazebo 주행 안정성(특히 복귀 구간, depth 지연, 현재 공식 설정과 Gazebo 맵의 불일치)은 별도 과제**이며 음성 기능과 분리해 다룬다.

## 원인 확정과 해결 (2026-11-23, 호스트)

1. **복귀 목표가 벽 옆**: Gazebo 시작 자세 (1.02, 0.37)는 전역 비용 88, 왼쪽 10 cm가 내접 영역(costmap_probe). 검증된 시뮬 설정(`nav2_params_sim_tol05.yaml`, 여유 포함 외곽)은 이 점을 목표로 받지 못한다.
2. **DirStop 교착**: 벽에서 약 0.2~0.3 m 안의 지점(시범 지점 앞 벽, 시작점 옆 벽)에서 되돌아서거나 다가갈 때 → 제어기가 움직임 → collision_monitor DirStop(LiDAR, 앞 0.33·옆 0.25·뒤 0.29 m)이 즉시 정지 → "Failed to make progress" → 대기 BT가 무한 재시도. BT가 포기하지 않아 180초(시뮬) 시간 초과로만 끝났다. 같은 DirStop이 **공식 실기 설정에도 있어 실기에서도 벽 가까이 목표는 같은 교착이 날 수 있다**(V2 착수 전 확인 필요).
3. 시작점 옆 벽 때문에 출발 직후 경로가 벽을 따라가다 내접 영역으로 들어가 NO_VALID_PATH(208)로 끝난 경우도 있었다.

**조치**
- 대시보드 Gazebo 주행 임무(`navigate_demo`, `return_to_start`)의 Nav2 설정을 10-11 생성 `nav2_params_mppi.yaml` → 추적되는 시뮬 검증 변형 `nav2_params_sim_tol05.yaml`로 변경. BT XML 등 `.../jetrover_ws/install/...` 절대 경로는 실행 중인 체크아웃의 install로 바꿔 임시 파일로 쓴다(`gazebo_managed_session.workspace_paths`). 경광등 점검 임무는 시야 보정 때문에 기존 설정 유지(후속).
- `return_to_start`만 시작 자세를 모든 벽에서 0.35 m 이상인 **(1.30, 0.40, 1.45)**로 두고, 왕복 지점을 (1.00, 1.25)로(앞 벽에서 0.2 m 더), 복귀 목표를 그 시작 자세로 한다.
- 진단용 `JETINSPECT_SESSION_LOG_DIR`(세션 로그 보존), 재사용 시험 도구 `tools/mission/gazebo_return_pause_trial.py`.

**결과(호스트, 실시간 비율 약 0.45)**: `return_to_start` 일시정지·재개 2/2, 일시정지 없음 1/1 성공(각 약 110초). `navigate_demo` 2/2 성공(각 약 50초). 변경 전 같은 조건 복귀 성공 2/7.
