# 026 — depth로만 보이는 장애물(박스) 앞에서 DWB가 멈추고 회피를 못 함 (해결, 2026-10-05)

## 증상
로봇 앞에 박스를 두고 `NavigateToPose`를 보내면 박스 앞에서 멈추고(`Failed to make progress`, `No valid trajectories out of 1973`, 스핀 recovery는 `Collision Ahead - Exiting Spin`) 우회하지 못한다.
박스를 더 멀리 옮겨도 "앞에서 멈춤"이 반복됐다.

## 원인 (2가지)
1. **depth 장애물이 local costmap에만 있었다.** 이 박스는 LiDAR(`/scan`)에 전혀 안 잡혀(점 없음, 팔/높이 때문) depth 포인트클라우드로만 보인다.
   global costmap은 `/scan`만 써서 전역 경로가 박스를 **그대로 통과**하게 계획되고, DWB는 그 경로를 따라가려다 유효 궤적이 없어 멈춘다.
   (`nav2_params.yaml`에 "local costmap only -- not worth adding to the global one"이라고 적어 둔 가정이 틀렸다.)
2. **depth 카메라는 홈 자세에서 바닥을 내려다봐서 감지 거리가 매우 짧다**(약 0.1~0.6 m, 영상 아래쪽만 바닥을 봄). 박스가 더 멀리 있으면 아예 안 보이고, 가까워진 뒤에야 보이므로 회피 여유가 작다.

## 해결 / 우회
- 1번: `jetrover_navigation/config/nav2_params.yaml`의 **global_costmap obstacle_layer에도 `depth_cloud`**(`/depth_cam/depth/points_sparse`, 범위 3 m)를 추가했다. 적용 후 전역 경로가 박스를 피해 계획된다.
- 2번은 구조적 한계다: 팔 자세(카메라 각도)를 바꾸거나 LiDAR/카메라 높이를 조정하지 않는 한 박스는 약 0.4 m 앞에서야 보인다. 큰 회피 시험은 박스가 경로 중앙에 있고 목표가 박스 inflation(약 0.4 m) 밖에 있게 둔다.

## 확인
- `/global_costmap/costmap`에 박스 위치가 lethal(#)로 나오는지, 목표가 박스 inflation 안이면 도달 못 하는 것이 정상이라는 점을 구분한다.
- 시험 중 정리: Nav2 재시작 시 이전 프로세스가 남아 노드 이름이 중복되면 lifecycle 활성화가 실패한다(`/proc/*/exe`로 `nav2_*` 프로세스를 모두 종료 후 `ros2 daemon stop/start`).
- 시험 중 AMCL 초기 위치는 재시작할 때마다 (0,0,0)으로 돌아간다: `/initialpose`를 다시 보내고, 라이다 스냅샷(`tools/viz/snapshot.py --frame map`)으로 확인한다.
